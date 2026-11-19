import os
import sys
import json
import math
import hashlib
import subprocess
import numpy as np
from mpi4py import MPI
from numba import cuda, float64
# Compile-time constants for 2D shared-memory tiling (16x16 interior + 1-cell halo apron)
TILE_DIM = 16
SHARED_DIM = TILE_DIM + 2  # 18
GLOBAL_NX = 512
GLOBAL_NY = 512
STEPS = 400
LAMBDA_DAMP = 0.15
def get_gpu_uuid() -> str:
    """Query active NVIDIA GPU UUID via nvidia-smi."""
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=uuid", "--format=csv,noheader"],
        encoding="utf-8",
    )
    return out.strip().splitlines()[0].strip()
def derive_student_seed(github_user: str, gpu_uuid: str) -> int:
    """Derive deterministic 64-bit integer seed bound to student GitHub handle and 
GPU UUID."""
    digest = hashlib.sha256(f"{github_user.strip()}::{gpu_uuid}".encode("utf8")).hexdigest()
    return int(digest[:16], 16)
def _neighbor_rank(rank):
    """JSON-friendly neighbor: missing Cartesian neighbors stay unset."""
    if rank == MPI.PROC_NULL:
        return None
    return int(rank)


def _device_name() -> str:
    name = cuda.get_current_device().name
    if isinstance(name, bytes):
        name = name.decode()
    return str(name)


# ==============================================================================
# TASK 1: Distributed Cartesian Topology & Hardware Context Initialization
# ==============================================================================
def init_distributed_context(github_user: str):
    """Build a non-periodic 2x2 Cartesian grid and bind every rank to GPU 0.

    Rank 0 reads the GPU UUID and broadcasts it so all four ranks derive the
    same student seed. Shift() yields MPI.PROC_NULL on the outer boundary.
    """
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    if size != 4:
        raise RuntimeError(f"Expected exactly 4 MPI ranks (2x2 grid), got {size}.")
    if GLOBAL_NX % 2 or GLOBAL_NY % 2:
        raise RuntimeError("Global grid must divide evenly across a 2x2 process grid.")
    if (GLOBAL_NX // 2) % TILE_DIM or (GLOBAL_NY // 2) % TILE_DIM:
        raise RuntimeError("Local interior must be an integer number of 16x16 tiles.")
    if TILE_DIM != 16 or SHARED_DIM != 18:
        raise RuntimeError("Stencil kernel is compiled for a 16x16 tile and an 18x18 apron.")

    # Bind process to GPU 0 on Google Colab. One physical GPU, four CUDA contexts.
    cuda.select_device(0)
    gpu_uuid = get_gpu_uuid() if rank == 0 else None
    gpu_uuid = comm.bcast(gpu_uuid, root=0)
    if not gpu_uuid:
        raise RuntimeError("Rank 0 failed to read the GPU UUID from nvidia-smi.")
    instance_seed = derive_student_seed(github_user, gpu_uuid)

    cart = comm.Create_cart((2, 2), periods=(False, False), reorder=False)
    cart_rank = cart.Get_rank()
    coords = tuple(int(c) for c in cart.Get_coords(cart_rank))
    # direction 0 grows southward, direction 1 grows eastward.
    # Shift returns (source, dest) = (north, south) and (west, east).
    north, south = cart.Shift(0, 1)
    west, east = cart.Shift(1, 1)
    return {
        "world": comm,
        "cart": cart,
        "rank": rank,
        "cart_rank": cart_rank,
        "size": size,
        "coords": coords,
        "north": north,
        "south": south,
        "west": west,
        "east": east,
        "seed": int(instance_seed),
        "gpu_uuid": gpu_uuid,
        "github_user": github_user.strip(),
        "device": _device_name(),
    }


# ==============================================================================
# TASK 2: Seeded local subdomain (256x256 interior + 1-cell halo)
# ==============================================================================
def initialize_local(ctx):
    """Fill this rank's interior from the shared seed and global coordinates.

    Halo cells start at 0. The outer halo stays 0 because a receive from
    MPI.PROC_NULL does not write the buffer, which is the Dirichlet boundary.
    """
    row, col = ctx["coords"]
    ny = GLOBAL_NY // 2
    nx = GLOBAL_NX // 2
    local = np.zeros((ny + 2, nx + 2), dtype=np.float64)
    child = np.random.SeedSequence(ctx["seed"]).spawn(4)[row * 2 + col]
    rng = np.random.default_rng(child)
    ys = np.arange(ny, dtype=np.float64) + row * ny
    xs = np.arange(nx, dtype=np.float64) + col * nx
    wave = np.sin(2.0 * math.pi * (ys[:, None] + 0.5) / GLOBAL_NY) * np.sin(
        2.0 * math.pi * (xs[None, :] + 0.5) / GLOBAL_NX
    )
    local[1:-1, 1:-1] = wave + 0.05 * rng.standard_normal((ny, nx))
    return local


def local_energy(field) -> float:
    view = field[1:-1, 1:-1]
    return float(np.sum(view * view))


# ==============================================================================
# TASK 3: Shared-memory stencil and coalesced-vs-strided edge packing
# ==============================================================================
@cuda.jit
def pack_edges(u, north, south, west, east):
    """Pack interior edges into contiguous buffers for the halo exchange.

    north[t] / south[t] read a contiguous row (coalesced).
    west[t] / east[t] read a column, stride = u.shape[1] elements (not coalesced).
    """
    t = cuda.grid(1)
    if t < north.shape[0]:
        north[t] = u[1, t + 1]
        south[t] = u[u.shape[0] - 2, t + 1]
    if t < west.shape[0]:
        west[t] = u[t + 1, 1]
        east[t] = u[t + 1, u.shape[1] - 2]


@cuda.jit
def unpack_halos(u, north, south, west, east):
    """Scatter received halo buffers into the one-cell apron of u."""
    t = cuda.grid(1)
    if t < north.shape[0]:
        u[0, t + 1] = north[t]
        u[u.shape[0] - 1, t + 1] = south[t]
    if t < west.shape[0]:
        u[t + 1, 0] = west[t]
        u[t + 1, u.shape[1] - 1] = east[t]


@cuda.jit
def stencil_kernel(u, u_new, lam):
    """Damped 5-point update on a 16x16 tile with an 18x18 shared apron.

    u_new = (1 - lam) * center + lam * (north + south + west + east) / 4
    """
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    bx = cuda.blockIdx.x
    by = cuda.blockIdx.y
    i = by * 16 + ty + 1
    j = bx * 16 + tx + 1

    tile = cuda.shared.array((18, 18), dtype=float64)
    tile[ty + 1, tx + 1] = u[i, j]
    if ty == 0:
        tile[0, tx + 1] = u[i - 1, j]
        if tx == 0:
            tile[0, 0] = u[i - 1, j - 1]
        if tx == 15:
            tile[0, 17] = u[i - 1, j + 1]
    if ty == 15:
        tile[17, tx + 1] = u[i + 1, j]
        if tx == 0:
            tile[17, 0] = u[i + 1, j - 1]
        if tx == 15:
            tile[17, 17] = u[i + 1, j + 1]
    if tx == 0:
        tile[ty + 1, 0] = u[i, j - 1]
    if tx == 15:
        tile[ty + 1, 17] = u[i, j + 1]

    # PTX barrier (bar.sync 0). Every thread in the block must reach this
    # before any thread reads a neighbor loaded by another thread.
    cuda.syncthreads()

    center = tile[ty + 1, tx + 1]
    avg = 0.25 * (
        tile[ty, tx + 1] + tile[ty + 2, tx + 1] + tile[ty + 1, tx] + tile[ty + 1, tx + 2]
    )
    u_new[i, j] = (1.0 - lam) * center + lam * avg


def collect_barrier_ptx():
    """Return the PTX lines that implement cuda.syncthreads in the stencil."""
    sig = (float64[:, :], float64[:, :], float64)
    try:
        stencil_kernel.compile(sig)
        asm = stencil_kernel.inspect_asm(sig)
    except Exception:
        try:
            asm = stencil_kernel.inspect_asm()
        except Exception as exc:
            return [f"PTX inspection failed: {exc}"]
    text = "\n".join(asm.values()) if isinstance(asm, dict) else str(asm)
    hits = []
    for line in text.splitlines():
        low = line.lower()
        if "bar.sync" in low or "barrier.sync" in low:
            hits.append(line.strip())
    return hits[:8] or ["no bar.sync / barrier.sync instruction found in PTX"]


# ==============================================================================
# TASK 4: Deadlock-free halo exchange and the 400-step time loop
# ==============================================================================
def exchange_halos(ctx, north_edge, south_edge, west_edge, east_edge):
    """Trade one-cell edges with Cartesian neighbors.

    Sendrecv posts the receive with the send, so a pair of neighbors cannot
    both block inside a send. Buffers are zeroed first: MPI.PROC_NULL completes
    the receive without writing, and that zero is the outer Dirichlet value.
    Tags 10..13 keep the four directions from matching the wrong message.
    """
    cart = ctx["cart"]
    north_edge = np.ascontiguousarray(north_edge, dtype=np.float64)
    south_edge = np.ascontiguousarray(south_edge, dtype=np.float64)
    west_edge = np.ascontiguousarray(west_edge, dtype=np.float64)
    east_edge = np.ascontiguousarray(east_edge, dtype=np.float64)
    north_halo = np.zeros_like(north_edge)
    south_halo = np.zeros_like(south_edge)
    west_halo = np.zeros_like(west_edge)
    east_halo = np.zeros_like(east_edge)

    # Northbound payload (my north edge) is what my northern neighbor stores
    # on its south halo. The matching receive is therefore posted from the south.
    cart.Sendrecv(
        north_edge, dest=ctx["north"], sendtag=10, recvbuf=south_halo, source=ctx["south"], recvtag=10
    )
    cart.Sendrecv(
        south_edge, dest=ctx["south"], sendtag=11, recvbuf=north_halo, source=ctx["north"], recvtag=11
    )
    cart.Sendrecv(
        west_edge, dest=ctx["west"], sendtag=12, recvbuf=east_halo, source=ctx["east"], recvtag=12
    )
    cart.Sendrecv(
        east_edge, dest=ctx["east"], sendtag=13, recvbuf=west_halo, source=ctx["west"], recvtag=13
    )
    return north_halo, south_halo, west_halo, east_halo


def advance(ctx, local):
    """Run STEPS damped Jacobi updates. The field stays on the GPU between steps."""
    ny = local.shape[0] - 2
    nx = local.shape[1] - 2
    d_u = cuda.to_device(local)
    d_v = cuda.device_array(local.shape, dtype=np.float64)
    d_north = cuda.device_array(nx, dtype=np.float64)
    d_south = cuda.device_array(nx, dtype=np.float64)
    d_west = cuda.device_array(ny, dtype=np.float64)
    d_east = cuda.device_array(ny, dtype=np.float64)
    d_north_h = cuda.device_array(nx, dtype=np.float64)
    d_south_h = cuda.device_array(nx, dtype=np.float64)
    d_west_h = cuda.device_array(ny, dtype=np.float64)
    d_east_h = cuda.device_array(ny, dtype=np.float64)

    edge_threads = 128
    edge_blocks = ((max(nx, ny) + edge_threads - 1) // edge_threads,)
    stencil_grid = (nx // TILE_DIM, ny // TILE_DIM)
    stencil_block = (TILE_DIM, TILE_DIM)
    lam = np.float64(LAMBDA_DAMP)

    for _ in range(STEPS):
        pack_edges[edge_blocks, edge_threads](d_u, d_north, d_south, d_west, d_east)
        north_halo, south_halo, west_halo, east_halo = exchange_halos(
            ctx,
            d_north.copy_to_host(),
            d_south.copy_to_host(),
            d_west.copy_to_host(),
            d_east.copy_to_host(),
        )
        d_north_h.copy_to_device(north_halo)
        d_south_h.copy_to_device(south_halo)
        d_west_h.copy_to_device(west_halo)
        d_east_h.copy_to_device(east_halo)
        unpack_halos[edge_blocks, edge_threads](d_u, d_north_h, d_south_h, d_west_h, d_east_h)
        stencil_kernel[stencil_grid, stencil_block](d_u, d_v, lam)
        d_u, d_v = d_v, d_u

    return d_u.copy_to_host()


# ==============================================================================
# TASK 5: Assemble the global field and print the audit report
# ==============================================================================
def publish(ctx, field, energy0, energy1):
    cart = ctx["cart"]
    interior = np.ascontiguousarray(field[1:-1, 1:-1])
    pieces = cart.gather(interior, root=0)
    infos = cart.gather(
        {
            "rank": int(ctx["rank"]),
            "coords": [int(ctx["coords"][0]), int(ctx["coords"][1])],
            "north": _neighbor_rank(ctx["north"]),
            "south": _neighbor_rank(ctx["south"]),
            "west": _neighbor_rank(ctx["west"]),
            "east": _neighbor_rank(ctx["east"]),
            "device": ctx["device"],
        },
        root=0,
    )
    if ctx["rank"] != 0:
        return

    global_u = np.empty((GLOBAL_NY, GLOBAL_NX), dtype=np.float64)
    for piece, info in zip(pieces, infos):
        row, col = info["coords"]
        y0 = row * piece.shape[0]
        x0 = col * piece.shape[1]
        global_u[y0 : y0 + piece.shape[0], x0 : x0 + piece.shape[1]] = piece

    digest = hashlib.sha256(np.ascontiguousarray(global_u).tobytes()).hexdigest()
    report = {
        "github_user": ctx["github_user"],
        "gpu_uuid": ctx["gpu_uuid"],
        "seed": ctx["seed"],
        "device": ctx["device"],
        "process_grid": "2x2",
        "global_shape": [GLOBAL_NY, GLOBAL_NX],
        "tile": [TILE_DIM, TILE_DIM],
        "shared_apron": [SHARED_DIM, SHARED_DIM],
        "steps": STEPS,
        "lambda_damp": LAMBDA_DAMP,
        "cfl_r": LAMBDA_DAMP / 4.0,
        "cfl_limit": 0.25,
        "initial_energy": energy0,
        "final_energy": energy1,
        "energy_decreased": bool(energy1 < energy0),
        "interior_sum": float(np.sum(global_u)),
        "sha256": digest,
        "ranks": infos,
        "ptx_barrier": collect_barrier_ptx(),
    }
    print(
        f"OK user={ctx['github_user']} energy {energy0:.6e} -> {energy1:.6e} sha256={digest}",
        flush=True,
    )
    print(json.dumps(report, indent=2), flush=True)


def main():
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        raise RuntimeError("Pass the GitHub username as the only argument.")
    ctx = init_distributed_context(sys.argv[1])
    local = initialize_local(ctx)
    energy0 = float(ctx["cart"].allreduce(local_energy(local), op=MPI.SUM))
    final_local = advance(ctx, local)
    energy1 = float(ctx["cart"].allreduce(local_energy(final_local), op=MPI.SUM))
    publish(ctx, final_local, energy0, energy1)


if __name__ == "__main__":
    main()
