"""
Capture one raw ADC noise run from the FTA controller using the firmware's `raw_adc_log` command with the controller idle (no dither or gradient loop), save the returned `ra,index,adc` samples to CSV/JSON, generate separate plots and stats for both the full run and the second half only so startup transients can be separated from steady-state behavior, and list detected serial ports if no port is provided. Example usage: `python fta_raw_adc_single_condition.py COM3 --label usb_powered --n-samples 4000 --avg 1 --delay-ms 0`
"""

import argparse
import csv
import json
import re
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import serial
import serial.tools.list_ports

RA_RE = re.compile(r"^ra,(-?\d+),(-?\d+)$")
START_RE = re.compile(r"^raw_adc_log_start")
DONE_RE = re.compile(r"^raw_adc_log_done")


def list_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found.")
        return
    print("Detected serial ports:")
    for p in ports:
        desc = f" - {p.description}" if p.description else ""
        hwid = f" [{p.hwid}]" if p.hwid else ""
        print(f"  {p.device}{desc}{hwid}")


def send(ser, cmd, pause=0.03):
    print(f"-> {cmd}")
    ser.write((cmd.rstrip("\r\n") + "\n").encode("utf-8"))
    ser.flush()
    if pause > 0:
        time.sleep(pause)


def drain(ser, seconds=0.25, verbose=False):
    t_end = time.time() + seconds
    while time.time() < t_end:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.replace(b"\x00", b"").decode("utf-8", errors="replace").strip()
        if verbose and line:
            print(f"<- {line}")


def set_idle(ser):
    send(ser, "stop", pause=0.15)
    drain(ser, 0.2)


def collect_raw_adc(ser, n_samples, avg, delay_ms, verbose=False, timeout_s=None):
    rows = []
    send(ser, f"raw_adc_log {int(n_samples)} {int(avg)} {int(delay_ms)}", pause=0.01)

    started = False
    done = False
    t0 = time.perf_counter()

    if timeout_s is None:
        timeout_s = max(10.0, n_samples * max(delay_ms / 1000.0, 0.0) + 10.0)

    while True:
        if (time.perf_counter() - t0) > timeout_s:
            raise TimeoutError("Timed out waiting for raw_adc_log to finish")

        raw = ser.readline()
        if not raw:
            continue

        line = raw.replace(b"\x00", b"").decode("utf-8", errors="replace").strip()
        if not line:
            continue

        if verbose:
            print(f"<- {line}")

        if START_RE.match(line):
            started = True
            continue

        if DONE_RE.match(line):
            done = True
            break

        m = RA_RE.match(line)
        if m:
            idx, adc = m.groups()
            rows.append(
                {
                    "t_s": time.perf_counter() - t0,
                    "i": int(idx),
                    "adc": int(adc),
                }
            )

    if not started:
        raise RuntimeError("Did not see raw_adc_log_start; firmware may not support raw_adc_log")
    if not done:
        raise RuntimeError("Did not see raw_adc_log_done")

    return rows


def summarize_rows(rows):
    if not rows:
        return {"n": 0}

    adc = np.array([r["adc"] for r in rows], dtype=float)
    ts = np.array([r["t_s"] for r in rows], dtype=float)

    dt = np.diff(ts)
    mean = float(np.mean(adc))
    centered = adc - mean

    return {
        "n": int(len(adc)),
        "duration_s": float(ts[-1] - ts[0]) if len(ts) >= 2 else 0.0,
        "sample_rate_hz_est": float(1.0 / np.mean(dt)) if len(dt) and np.mean(dt) > 0 else None,
        "mean_adc": mean,
        "std_adc": float(np.std(adc, ddof=1)) if len(adc) >= 2 else 0.0,
        "rms_about_mean_adc": float(np.sqrt(np.mean(centered**2))),
        "median_adc": float(np.median(adc)),
        "mad_adc": float(np.median(np.abs(adc - np.median(adc)))),
        "min_adc": int(np.min(adc)),
        "max_adc": int(np.max(adc)),
        "pk_pk_adc": int(np.max(adc) - np.min(adc)),
    }


def print_stats(title, stats):
    print(f"\n=== {title} ===")
    for key, value in stats.items():
        print(f"{key}: {value}")


def save_csv(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["t_s", "i", "adc"])
        w.writeheader()
        w.writerows(rows)


def save_stats_json(path, label, stats, rows_name):
    with open(path, "w") as f:
        json.dump(
            {
                "label": label,
                "segment": rows_name,
                "stats": stats,
            },
            f,
            indent=2,
        )


def plot_trace(rows, out_png, title):
    adc = np.array([r["adc"] for r in rows], dtype=float)
    ts = np.array([r["t_s"] for r in rows], dtype=float)

    plt.figure(figsize=(12, 5))
    plt.plot(ts, adc)
    plt.xlabel("Time (s)")
    plt.ylabel("ADC")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()


def main():
    ap = argparse.ArgumentParser(
        description="Capture one raw ADC noise run and save/print stats for full trace and second half."
    )
    ap.add_argument("port", nargs="?", help="Serial port, e.g. COM3. If omitted, list ports and exit.")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--n-samples", type=int, default=4000)
    ap.add_argument("--avg", type=int, default=1, help="ADC averages per reported sample")
    ap.add_argument("--delay-ms", type=int, default=0, help="Delay between reported samples")
    ap.add_argument("--label", default="condition", help="Name for this run, e.g. usb_powered")
    ap.add_argument("--outdir", default="raw_adc_single_condition")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.port:
        list_ports()
        return

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\nPrepare condition: {args.label}")
    input("Press ENTER when ready to capture... ")

    with serial.Serial(args.port, args.baud, timeout=0.5, write_timeout=0.5) as ser:
        time.sleep(0.2)
        drain(ser, 0.5, verbose=args.verbose)
        set_idle(ser)

        rows = collect_raw_adc(
            ser,
            n_samples=args.n_samples,
            avg=args.avg,
            delay_ms=args.delay_ms,
            verbose=args.verbose,
        )

    if not rows:
        raise RuntimeError("No ADC samples captured")

    half_idx = len(rows) // 2
    second_half_rows = rows[half_idx:]

    full_stats = summarize_rows(rows)
    second_half_stats = summarize_rows(second_half_rows)

    print_stats(f"{args.label} : full trace", full_stats)
    print_stats(f"{args.label} : second half only", second_half_stats)

    base = outdir / args.label

    save_csv(rows, Path(f"{base}_full.csv"))
    save_csv(second_half_rows, Path(f"{base}_second_half.csv"))

    save_stats_json(Path(f"{base}_full.json"), args.label, full_stats, "full")
    save_stats_json(Path(f"{base}_second_half.json"), args.label, second_half_stats, "second_half")

    plot_trace(rows, Path(f"{base}_full.png"), f"Raw ADC trace: {args.label} (full)")
    plot_trace(second_half_rows, Path(f"{base}_second_half.png"), f"Raw ADC trace: {args.label} (second half)")

    print("\nSaved:")
    print(Path(f"{base}_full.csv"))
    print(Path(f"{base}_full.json"))
    print(Path(f"{base}_full.png"))
    print(Path(f"{base}_second_half.csv"))
    print(Path(f"{base}_second_half.json"))
    print(Path(f"{base}_second_half.png"))


if __name__ == "__main__":
    main()