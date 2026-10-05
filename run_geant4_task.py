"""
run_geant4_task.py - Parallel worker for Geant4 Simulation on GitHub Actions Cluster
Paper 10.2 (ANE 2024) Benchmark: 141 jobs across 140 runners on 14 accounts.
"""
import argparse
import os
import sys
import time
import json
import subprocess
from pathlib import Path
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gdrive_helper

def parse_args():
    parser = argparse.ArgumentParser(description="Geant4 Parallel Worker for Paper 10.2")
    parser.add_argument("--runner-id", type=int, required=True, help="ID cua runner (1..10)")
    parser.add_argument("--num-runners", type=int, default=10, help="Tong so runner moi account")
    parser.add_argument("--primaries", type=int, default=1000000, help="So hat moi job (mac dinh 10^6)")
    parser.add_argument("--gdrive-folder", type=str, default="1RBUI6lx8yrnTgappHpAvfnZTCzSvR0nM")
    parser.add_argument("--plan-file", type=str, default="geant4_plan_14acc.json")
    parser.add_argument("--github-user", type=str, default=None)
    parser.add_argument("--sim-bin", type=str, default=None)
    parser.add_argument("--timeout-hours", type=float, default=2.0)
    return parser.parse_args()

def ensure_compiled():
    candidates = ["./build/Sim", "./Sim", "/tmp/geant4_build/Sim"]
    for c in candidates:
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    
    print(">>> [BUILD] Bien dich ma nguon Geant4...")
    build_dir = Path("build")
    build_dir.mkdir(parents=True, exist_ok=True)
    res_cmake = subprocess.run(["cmake", "..", "-DCMAKE_BUILD_TYPE=Release"], cwd=str(build_dir))
    if res_cmake.returncode != 0:
        raise RuntimeError("CMake configure that bai!")
    res_make = subprocess.run(["make", f"-j{os.cpu_count() or 2}"], cwd=str(build_dir))
    if res_make.returncode != 0:
        raise RuntimeError("Make build that bai!")
    
    sim_bin = "./build/Sim"
    if not os.path.exists(sim_bin):
        raise FileNotFoundError(f"Khong tim thay binary {sim_bin} sau khi build!")
    return sim_bin

def parse_process_results_last_row(csv_path: Path):
    if not csv_path.exists():
        return 0.0, 0.0
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return 0.0, 0.0
        last = df.iloc[-1]
        tot = float(last.get("CrossFlux_total", 0.0))
        uncoll = float(last.get("CrossFlux_uncollided", 0.0))
        return uncoll, tot
    except Exception as e:
        print(f"    [PARSE ERROR] {e}")
        return 0.0, 0.0

def main():
    args = parse_args()
    acc_name = args.github_user or os.environ.get("GITHUB_REPOSITORY_OWNER") or "runner"

    print("=" * 80)
    print(f"🚀 STARTING GEANT4 RUNNER #{args.runner_id} (Account: {acc_name})")
    print(f"Primaries per job: {args.primaries:,}")
    print(f"Plan file: {args.plan_file}")
    print("=" * 80)

    sim_bin = ensure_compiled()
    print(f">>> Binary Geant4 san sang: {sim_bin}")

    # Connect Google Drive
    drive_service = None
    target_flux_folder = None
    try:
        drive_service = gdrive_helper.get_drive_service()
        # Find 02_Flux_Data inside gdrive_folder
        q = f"'{args.gdrive_folder}' in parents and name = '02_Flux_Data' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_f = drive_service.files().list(q=q, fields="files(id, name)").execute()
        items = res_f.get("files", [])
        if items:
            target_flux_folder = items[0]["id"]
        else:
            target_flux_folder = args.gdrive_folder
        print(f">>> [DRIVE] Ket noi thanh cong Google Drive! Thu muc upload: {target_flux_folder}")
    except Exception as e:
        print(f">>> [WARNING] Ket noi Drive that bai: {e}. Du lieu se luu cuc bo.")

    # Load plan
    with open(args.plan_file, "r", encoding="utf-8") as pf:
        full_plan = json.load(pf)

    matched_acc = None
    for acc in full_plan:
        if acc.lower() == acc_name.lower():
            matched_acc = acc
            break
    if not matched_acc:
        matched_acc = list(full_plan.keys())[0]

    runner_jobs = full_plan[matched_acc].get(str(args.runner_id), [])
    total_jobs = len(runner_jobs)
    print(f"Runner #{args.runner_id} nhan duoc {total_jobs} jobs tu account '{matched_acc}'.")

    out_csv = Path(f"flux_{acc_name}_runner_{args.runner_id:02d}.csv")
    records = []
    if out_csv.exists():
        try:
            df_old = pd.read_csv(out_csv)
            records = df_old.to_dict(orient="records")
        except Exception:
            pass

    completed_jobs = {r["job_name"] for r in records}
    proc_csv = Path("process_results.csv")

    for idx, job in enumerate(runner_jobs, 1):
        jname = job["job_name"]
        if jname in completed_jobs:
            print(f"[{idx}/{total_jobs}] SKIP: {jname} da hoan thanh truoc do.")
            continue

        macro_name = job["macro_file"]
        macro_path = Path("macros") / macro_name
        if not macro_path.exists():
            print(f"[{idx}/{total_jobs}] ERR: Khong tim thay macro {macro_path}!")
            continue

        print(f"[{idx}/{total_jobs}] RUNNING: {jname} | Sample: {job['sample']} | E={job['energy_kev']} keV | Th={job['thickness_cm']} cm")
        
        # Remove old process_results.csv
        if proc_csv.exists():
            proc_csv.unlink()

        t0 = time.time()
        res = subprocess.run([sim_bin, str(macro_path)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - t0

        if res.returncode != 0:
            print(f"    [SIM ERROR]: {res.stderr.strip()[-300:]}")
            continue

        uncoll, tot = parse_process_results_last_row(proc_csv)
        print(f"    ✅ Hoan thanh trong {elapsed:.1f}s | Uncollided Flux: {uncoll:.6e} | Total Flux: {tot:.6e}")

        rec = {
            "job_name": jname,
            "energy_mev": job["energy_mev"],
            "sample": job["sample"],
            "thickness_cm": job["thickness_cm"],
            "peak_flux": uncoll,
            "total_flux": tot,
            "elapsed_s": round(elapsed, 2)
        }
        records.append(rec)
        pd.DataFrame(records).to_csv(out_csv, index=False)

    # Sync to Drive
    if drive_service and target_flux_folder and out_csv.exists():
        try:
            gdrive_helper.upload_file_to_folder(drive_service, str(out_csv), target_flux_folder)
            print(f"\n🎉 [SYNC SUCCESS] Da upload {out_csv.name} len Google Drive!")
        except Exception as e:
            print(f"\n⚠️ [SYNC ERROR] Khong the upload len Drive: {e}")

    print("\n" + "=" * 80)
    print(f"RUNNER #{args.runner_id} HOAN THANH NHIEM VU!")
    print("=" * 80)

if __name__ == "__main__":
    main()
