"""Inspect the host CPU topology and emit salted problem parameters.

Writes:
  results/host_profile.json
  results/salted_params.json
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salt import get_student_params

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# Intel CPUID display model (family 6) -> microarchitecture.
# Hybrid parts that share a model (Kaby Lake / Coffee Lake / Comet Lake on
# 0x8E and 0x9E) are refined from the marketing name afterwards.
INTEL_FAMILY6 = {
    0x1A: "Nehalem",
    0x1E: "Nehalem",
    0x25: "Westmere",
    0x2C: "Westmere",
    0x2A: "Sandy Bridge",
    0x2D: "Sandy Bridge",
    0x3A: "Ivy Bridge",
    0x3E: "Ivy Bridge",
    0x3C: "Haswell",
    0x3F: "Haswell",
    0x45: "Haswell",
    0x46: "Haswell",
    0x3D: "Broadwell",
    0x47: "Broadwell",
    0x4F: "Broadwell",
    0x56: "Broadwell",
    0x4E: "Skylake",
    0x5E: "Skylake",
    0x55: "Skylake",
    0x8E: "Kaby Lake",
    0x9E: "Kaby Lake",
    0x66: "Cannon Lake",
    0x7D: "Ice Lake",
    0x7E: "Ice Lake",
    0x6A: "Ice Lake",
    0x6C: "Ice Lake",
    0xA5: "Comet Lake",
    0xA6: "Comet Lake",
    0x8C: "Tiger Lake",
    0x8D: "Tiger Lake",
    0xA7: "Rocket Lake",
    0x97: "Alder Lake",
    0x9A: "Alder Lake",
    0xB7: "Raptor Lake",
    0xBA: "Raptor Lake",
    0xBF: "Raptor Lake",
    0xAA: "Meteor Lake",
    0xAC: "Meteor Lake",
    0xC5: "Arrow Lake",
    0xC6: "Arrow Lake",
    0xBD: "Lunar Lake",
}

NAME_UARCH = (
    ("lunar lake", "Lunar Lake"),
    ("arrow lake", "Arrow Lake"),
    ("meteor lake", "Meteor Lake"),
    ("raptor lake", "Raptor Lake"),
    ("alder lake", "Alder Lake"),
    ("tiger lake", "Tiger Lake"),
    ("ice lake", "Ice Lake"),
    ("comet lake", "Comet Lake"),
    ("coffee lake", "Coffee Lake"),
    ("whiskey lake", "Whiskey Lake"),
    ("kaby lake", "Kaby Lake"),
    ("cannon lake", "Cannon Lake"),
    ("cascade lake", "Cascade Lake"),
    ("skylake", "Skylake"),
    ("broadwell", "Broadwell"),
    ("haswell", "Haswell"),
    ("14th gen", "Raptor Lake Refresh"),
    ("13th gen", "Raptor Lake"),
    ("12th gen", "Alder Lake"),
    ("11th gen", "Tiger Lake"),
    ("10th gen", "Comet Lake"),
    ("zen 5", "Zen 5"),
    ("zen 4", "Zen 4"),
    ("zen 3", "Zen 3"),
    ("zen 2", "Zen 2"),
    ("zen+", "Zen+"),
    ("zen", "Zen"),
)


def microarchitecture(vendor, family, model, model_name):
    name = model_name or ""
    lowered = name.lower()
    for needle, label in NAME_UARCH:
        if needle in lowered:
            return label

    vendor_l = (vendor or "").lower()
    if family == 6 and model in INTEL_FAMILY6 and (
        "intel" in vendor_l or "genuineintel" in vendor_l or vendor_l == ""
    ):
        return INTEL_FAMILY6[model]

    if "amd" in vendor_l or "authenticamd" in vendor_l:
        if family == 0x19:
            return "Zen 4" if model is not None and model >= 0x10 else "Zen 3"
        if family == 0x1A:
            return "Zen 5"
        if family == 0x17:
            if model is not None and model >= 0x30:
                return "Zen 2"
            if model is not None and model >= 0x10:
                return "Zen+"
            return "Zen"

    if family is not None and model is not None:
        return f"Family {family} Model {model}"
    return "unknown"


def parse_family_model(text):
    """Parse 'Family 6 Model 154 Stepping 3' style identifiers."""
    if not text:
        return None, None, None
    family = re.search(r"Family\s+(\d+)", text, re.IGNORECASE)
    model = re.search(r"Model\s+(\d+)", text, re.IGNORECASE)
    stepping = re.search(r"Stepping\s+(\d+)", text, re.IGNORECASE)
    return (
        int(family.group(1)) if family else None,
        int(model.group(1)) if model else None,
        int(stepping.group(1)) if stepping else None,
    )


def parse_ghz(model_name):
    match = re.search(r"@\s*([0-9]+(?:\.[0-9]+)?)\s*GHz", model_name or "", re.IGNORECASE)
    if not match:
        return None
    return int(round(float(match.group(1)) * 1000))


def parse_sysfs_size(text):
    match = re.fullmatch(r"\s*(\d+)\s*([KMG])?\s*", text.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"unrecognized cache size {text!r}")
    value = int(match.group(1))
    unit = (match.group(2) or "").upper()
    scale = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3}
    return value * scale[unit]


def python_details():
    return {
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
        "compiler": platform.python_compiler(),
        "build": list(platform.python_build()),
        "executable": sys.executable,
        "bits": 64 if sys.maxsize > 2**32 else 32,
        "version_string": sys.version.replace("\n", " "),
    }


def os_details():
    uname = platform.uname()
    return {
        "system": uname.system,
        "node": uname.node,
        "release": uname.release,
        "kernel_version": uname.version,
        "machine": uname.machine,
        "platform": platform.platform(),
    }


def profile_document(
    *,
    model_name,
    vendor,
    family,
    model,
    stepping,
    base_frequency_mhz,
    frequency_source,
    physical_cores,
    logical_threads,
    smt_enabled,
    l1d_cache_bytes,
    l2_cache_bytes,
    l3_cache_bytes,
    cache_line_bytes,
    cache_instances,
    probe,
):
    vendor_l = (vendor or "").lower()
    if not smt_enabled:
        smt_name = "disabled"
    elif "intel" in vendor_l or "genuineintel" in vendor_l:
        smt_name = "Hyper-Threading"
    else:
        smt_name = "SMT"

    host_os = os_details()
    py = python_details()
    return {
        "cpu_model": model_name,
        "cpu_model_name": model_name,
        "vendor": vendor,
        "family": family,
        "model": model,
        "stepping": stepping,
        "microarchitecture": microarchitecture(vendor, family, model, model_name),
        "base_frequency_mhz": base_frequency_mhz,
        "base_frequency_hz": None
        if base_frequency_mhz is None
        else int(base_frequency_mhz) * 1_000_000,
        "frequency_source": frequency_source,
        "physical_cores": physical_cores,
        "logical_threads": logical_threads,
        "smt_enabled": smt_enabled,
        "smt": smt_name,
        "l1d_cache_bytes": l1d_cache_bytes,
        "l2_cache_bytes": l2_cache_bytes,
        "l3_cache_bytes": l3_cache_bytes,
        "cache_line_bytes": cache_line_bytes,
        "cache_instances": cache_instances,
        "os_kernel_version": host_os["kernel_version"],
        "os": host_os,
        "python_implementation": py["implementation"],
        "python_version": py["version"],
        "python_compiler": py["compiler"],
        "python": py,
        "probe": probe,
    }


def _run(args):
    completed = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def profile_linux():
    cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
    blocks = [b for b in cpuinfo.split("\n\n") if b.strip()]
    fields = []
    for block in blocks:
        entry = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            entry[key.strip()] = value.strip()
        if entry:
            fields.append(entry)
    first = fields[0] if fields else {}
    model_name = first.get("model name") or first.get("Processor") or platform.processor()
    vendor = first.get("vendor_id") or ""
    family = int(first["cpu family"]) if "cpu family" in first else None
    model = int(first["model"]) if "model" in first else None
    stepping = int(first["stepping"]) if "stepping" in first else None

    physical = set()
    for entry in fields:
        if "core id" in entry:
            physical.add((entry.get("physical id", "0"), entry["core id"]))
    physical_cores = len(physical) if physical else None
    if physical_cores is None and "cpu cores" in first:
        physical_cores = int(first["cpu cores"])
    logical_threads = len(fields) if fields else os.cpu_count()
    flags = set((first.get("flags") or "").split())
    smt_enabled = logical_threads > physical_cores if physical_cores else ("ht" in flags)

    base_mhz = None
    frequency_source = None
    base_file = Path("/sys/devices/system/cpu/cpu0/cpufreq/base_frequency")
    if base_file.is_file():
        base_mhz = int(base_file.read_text().strip()) // 1000
        frequency_source = str(base_file)
    if base_mhz is None:
        base_mhz = parse_ghz(model_name)
        if base_mhz is not None:
            frequency_source = "model name"
    if base_mhz is None and "cpu MHz" in first:
        base_mhz = int(round(float(first["cpu MHz"])))
        frequency_source = "/proc/cpuinfo cpu MHz (current)"

    instances = _linux_cache_instances()
    l1d, l2, l3, line = _sum_caches(instances)
    if line is None:
        line = 64

    return profile_document(
        model_name=model_name,
        vendor=vendor,
        family=family,
        model=model,
        stepping=stepping,
        base_frequency_mhz=base_mhz,
        frequency_source=frequency_source,
        physical_cores=physical_cores,
        logical_threads=logical_threads,
        smt_enabled=bool(smt_enabled),
        l1d_cache_bytes=l1d,
        l2_cache_bytes=l2,
        l3_cache_bytes=l3,
        cache_line_bytes=line,
        cache_instances=instances,
        probe="/proc/cpuinfo + /sys/devices/system/cpu/*/cache",
    )


def _linux_cache_instances():
    seen = set()
    instances = []
    cpu_root = Path("/sys/devices/system/cpu")
    indexes = sorted(
        cpu_root.glob("cpu[0-9]*/cache/index*"),
        key=lambda path: str(path),
    )
    for index in indexes:
        try:
            level = int((index / "level").read_text().strip())
            kind = (index / "type").read_text().strip()
            size = parse_sysfs_size((index / "size").read_text())
            line = int((index / "coherency_line_size").read_text().strip())
            shared = (index / "shared_cpu_list").read_text().strip()
            cache_id = (index / "id").read_text().strip() if (index / "id").is_file() else None
        except (OSError, ValueError):
            continue
        key = (level, kind, cache_id if cache_id is not None else shared, size)
        if key in seen:
            continue
        seen.add(key)
        instances.append(
            {
                "level": level,
                "type": kind,
                "bytes": size,
                "line_size_bytes": line,
                "shared_cpu_list": shared,
            }
        )
    return instances


def _sum_caches(instances):
    l1d = l2 = l3 = 0
    line = None
    for item in instances:
        if line is None:
            line = item.get("line_size_bytes")
        kind = str(item["type"]).lower()
        if item["level"] == 1 and "data" in kind:
            l1d += item["bytes"]
        elif item["level"] == 2:
            l2 += item["bytes"]
        elif item["level"] == 3:
            l3 += item["bytes"]
    return l1d, l2, l3, line


def profile_macos():
    def sysctl(key):
        return _run(["sysctl", "-n", key])

    model_name = sysctl("machdep.cpu.brand_string") or platform.processor() or sysctl("hw.model")
    vendor = sysctl("machdep.cpu.vendor") or ""
    family_s = sysctl("machdep.cpu.family")
    model_s = sysctl("machdep.cpu.model")
    stepping_s = sysctl("machdep.cpu.stepping")
    family = int(family_s) if family_s and family_s.isdigit() else None
    model = int(model_s) if model_s and model_s.isdigit() else None
    stepping = int(stepping_s) if stepping_s and stepping_s.isdigit() else None

    physical = sysctl("hw.physicalcpu")
    logical = sysctl("hw.logicalcpu")
    physical_cores = int(physical) if physical else None
    logical_threads = int(logical) if logical else os.cpu_count()
    smt_enabled = (
        physical_cores is not None and logical_threads is not None and logical_threads > physical_cores
    )

    freq = sysctl("hw.cpufrequency")
    if freq and freq.isdigit():
        base_mhz = int(freq) // 1_000_000
        frequency_source = "hw.cpufrequency"
    else:
        base_mhz = parse_ghz(model_name)
        frequency_source = "model name" if base_mhz is not None else None

    def cache_bytes(key):
        raw = sysctl(key)
        if raw and raw.isdigit():
            return int(raw)
        return 0

    line_raw = sysctl("hw.cachelinesize")
    line = int(line_raw) if line_raw and line_raw.isdigit() else 64
    kernel = sysctl("kern.version") or platform.uname().version

    doc = profile_document(
        model_name=model_name,
        vendor=vendor,
        family=family,
        model=model,
        stepping=stepping,
        base_frequency_mhz=base_mhz,
        frequency_source=frequency_source,
        physical_cores=physical_cores,
        logical_threads=logical_threads,
        smt_enabled=smt_enabled,
        l1d_cache_bytes=cache_bytes("hw.l1dcachesize"),
        l2_cache_bytes=cache_bytes("hw.l2cachesize"),
        l3_cache_bytes=cache_bytes("hw.l3cachesize"),
        cache_line_bytes=line,
        cache_instances=[],
        probe="sysctl",
    )
    doc["os_kernel_version"] = kernel
    doc["os"]["kernel_version"] = kernel
    return doc


def profile_windows():
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
    ) as key:
        model_name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        identifier = winreg.QueryValueEx(key, "Identifier")[0].strip()
        vendor = winreg.QueryValueEx(key, "VendorIdentifier")[0].strip()
        current_mhz = int(winreg.QueryValueEx(key, "~MHz")[0])

    family, model, stepping = parse_family_model(identifier)
    topology = _windows_logical_processor_info()

    base_mhz = parse_ghz(model_name)
    frequency_source = "model name" if base_mhz is not None else None
    wmi_mhz = _windows_max_clock_mhz()
    if base_mhz is None and wmi_mhz is not None:
        base_mhz = wmi_mhz
        frequency_source = "Win32_Processor.MaxClockSpeed"
    if base_mhz is None:
        base_mhz = current_mhz
        frequency_source = r"HKLM\...\CentralProcessor\0 ~MHz"

    instances = topology["caches"]
    l1d, l2, l3, line = _sum_caches(instances)
    if line is None:
        line = 64

    return profile_document(
        model_name=model_name,
        vendor=vendor,
        family=family,
        model=model,
        stepping=stepping,
        base_frequency_mhz=base_mhz,
        frequency_source=frequency_source,
        physical_cores=topology["physical_cores"],
        logical_threads=topology["logical_threads"],
        smt_enabled=topology["smt_enabled"],
        l1d_cache_bytes=l1d,
        l2_cache_bytes=l2,
        l3_cache_bytes=l3,
        cache_line_bytes=line,
        cache_instances=instances,
        probe="GetLogicalProcessorInformation + processor registry",
    )


def _windows_max_clock_mhz():
    script = (
        "(Get-CimInstance Win32_Processor | "
        "Select-Object -First 1 -ExpandProperty MaxClockSpeed)"
    )
    raw = _run(["powershell", "-NoProfile", "-Command", script])
    if raw and raw.strip().isdigit():
        return int(raw.strip())
    return None


def _windows_logical_processor_info():
    import ctypes
    from ctypes import wintypes

    class CACHE_DESCRIPTOR(ctypes.Structure):
        _fields_ = [
            ("Level", ctypes.c_ubyte),
            ("Associativity", ctypes.c_ubyte),
            ("LineSize", ctypes.c_ushort),
            ("Size", ctypes.c_ulong),
            ("Type", ctypes.c_int),
        ]

    class PROCESSORCORE(ctypes.Structure):
        _fields_ = [("Flags", ctypes.c_ubyte)]

    class NUMANODE(ctypes.Structure):
        _fields_ = [("NodeNumber", ctypes.c_ulong)]

    class SLPI_UNION(ctypes.Union):
        _fields_ = [
            ("ProcessorCore", PROCESSORCORE),
            ("NumaNode", NUMANODE),
            ("Cache", CACHE_DESCRIPTOR),
            ("Reserved", ctypes.c_ulonglong * 2),
        ]

    class SLPI(ctypes.Structure):
        _fields_ = [
            ("ProcessorMask", ctypes.c_ulonglong),
            ("Relationship", ctypes.c_int),
            ("Payload", SLPI_UNION),
        ]

    relation_core = 0
    relation_cache = 2
    cache_type = {0: "Unified", 1: "Instruction", 2: "Data", 3: "Trace"}

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_info = kernel32.GetLogicalProcessorInformation
    get_info.argtypes = [ctypes.POINTER(SLPI), ctypes.POINTER(wintypes.DWORD)]
    get_info.restype = wintypes.BOOL

    needed = wintypes.DWORD(0)
    get_info(None, ctypes.byref(needed))
    count = needed.value // ctypes.sizeof(SLPI)
    buffer = (SLPI * count)()
    if not get_info(buffer, ctypes.byref(needed)):
        raise OSError("GetLogicalProcessorInformation failed")

    physical = 0
    logical = 0
    smt = False
    caches = []
    for item in buffer:
        if item.Relationship == relation_core:
            threads = bin(item.ProcessorMask).count("1")
            physical += 1
            logical += threads
            smt = smt or threads > 1
        elif item.Relationship == relation_cache:
            cache = item.Payload.Cache
            caches.append(
                {
                    "level": int(cache.Level),
                    "type": cache_type.get(int(cache.Type), str(int(cache.Type))),
                    "bytes": int(cache.Size),
                    "line_size_bytes": int(cache.LineSize),
                    "shared_by_logical_processors": bin(item.ProcessorMask).count("1"),
                }
            )

    if logical == 0:
        logical = os.cpu_count() or 0
    return {
        "physical_cores": physical,
        "logical_threads": logical,
        "smt_enabled": smt,
        "caches": caches,
    }


def profile_generic():
    uname = platform.uname()
    logical = os.cpu_count()
    return profile_document(
        model_name=platform.processor() or uname.processor,
        vendor="",
        family=None,
        model=None,
        stepping=None,
        base_frequency_mhz=None,
        frequency_source=None,
        physical_cores=logical,
        logical_threads=logical,
        smt_enabled=False,
        l1d_cache_bytes=0,
        l2_cache_bytes=0,
        l3_cache_bytes=0,
        cache_line_bytes=64,
        cache_instances=[],
        probe="platform",
    )


def collect_profile():
    system = platform.system()
    if system == "Linux":
        return profile_linux()
    if system == "Darwin":
        return profile_macos()
    if system == "Windows":
        return profile_windows()
    return profile_generic()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Profile host topology and salt problem parameters from a student ID."
    )
    parser.add_argument("--student-id", required=True, help="Student ID used to salt N and the RNG seed.")
    args = parser.parse_args(argv)

    profile = collect_profile()
    params = get_student_params(args.student_id)
    profile_path = RESULTS / "host_profile.json"
    params_path = RESULTS / "salted_params.json"
    write_json(profile_path, profile)
    write_json(params_path, params)
    print(f"wrote {profile_path}")
    print(f"wrote {params_path}")
    print(
        f"N={params['N']} buffer_elements={params['buffer_elements']} seed={params['seed']}"
    )


if __name__ == "__main__":
    main()
