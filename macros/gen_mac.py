#!/usr/bin/env python3
"""
gen_mac.py - Tu dong tao file .mac cho Geant4 tu bang be day Paper 10.2
Tao day du 61 file macro:
- 7 file Blank (80, 238, 356, 662, 1173, 1333, 2614 keV)
- 54 file cho 5 mau TPCB (TPCB00, TPCB02, TPCB04, TPCB06, TPCB10)
- 1 file master macro: run_all.mac

Cach dung:
    python gen_mac.py thickness_table.xlsx --outdir ./mac_output --beamon 1000000
"""
import argparse
import re
import sys
from pathlib import Path
import pandas as pd

MAT_MAP = {
    "tpcb00": "TPCB00",
    "tpcb02": "TPCB02",
    "tpcb04": "TPCB04",
    "tpcb06": "TPCB06",
    "tpcb10": "TPCB10",
}


def _fmt_thickness(th: float) -> str:
    s = f"{th:.3f}"
    return s if s else "0"


def _parse_thickness_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    s = str(value).strip()
    if not s:
        return []
    parts = [p for p in re.split(r"[,;\s]+", s) if p]
    return [float(p) for p in parts]


def make_macro(mat_name: str, th_cm: float, energy_kev: float, histname: str, beamon: int) -> str:
    th_mm = th_cm * 10.0
    return f"""/control/verbose 2
/DetectorConstruction/Sample_Material {mat_name}
/DetectorConstruction/Sample_Thickness {th_mm:.4f} mm
/DetectorConstruction/update

/gun/energy {energy_kev:.4f} keV
/analysis/setFileName {histname}
/run/beamOn {beamon}
"""


def main():
    parser = argparse.ArgumentParser(description="Sinh cac file .mac cho Geant4 (Paper 10.2)")
    parser.add_argument("excel", nargs="?", default="../thickness_table.xlsx", help="File Excel be day")
    parser.add_argument("--outdir", default="./mac_output", help="Thu muc xuat cac file .mac")
    parser.add_argument("--beamon", type=int, default=1000000, help="So hat ban (beamOn)")
    args = parser.parse_args()

    excel_path = Path(args.excel)
    if not excel_path.exists():
        # Thu tim tai thu muc hien tai
        if Path("thickness_table.xlsx").exists():
            excel_path = Path("thickness_table.xlsx")
        elif Path("../thickness_table.xlsx").exists():
            excel_path = Path("../thickness_table.xlsx")

    df = pd.read_excel(excel_path)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    materials = [c for c in df.columns if c.lower() != "energy"]
    count_jobs = 0
    blank_generated = set()
    all_macro_files = []

    print("=" * 65)
    print("DANG TAO CAC FILE MACRO .MAC CHO GEANT4 (PAPER 10.2)...")
    print(f"Excel:   {excel_path}")
    print(f"Outdir:  {outdir}")
    print(f"BeamOn:  {args.beamon} particles")
    print("=" * 65)

    for _, row in df.iterrows():
        energy_kev = float(row["Energy"])
        e_int = int(round(energy_kev))

        # 1. Blank macro
        if e_int not in blank_generated:
            th_blank_cm = 0.5
            blank_name = f"blank_{e_int}keV"
            mac_file = f"{blank_name}.mac"
            mac_content = make_macro("Blank", th_blank_cm, energy_kev, blank_name, args.beamon)
            (outdir / mac_file).write_text(mac_content, encoding="utf-8")
            all_macro_files.append(mac_file)
            blank_generated.add(e_int)
            count_jobs += 1

        # 2. Sample macros
        for mat_col in materials:
            mat_key = mat_col.lower()
            if mat_key not in MAT_MAP:
                continue
            g4_mat = MAT_MAP[mat_key]

            th_list = _parse_thickness_list(row[mat_col])
            for th_cm in th_list:
                th_str = _fmt_thickness(th_cm)
                job_name = f"{mat_key}_{e_int}keV_th{th_str}cm"
                mac_file = f"{job_name}.mac"
                mac_content = make_macro(g4_mat, th_cm, energy_kev, job_name, args.beamon)
                (outdir / mac_file).write_text(mac_content, encoding="utf-8")
                all_macro_files.append(mac_file)
                count_jobs += 1

    # Tao file run_all.mac
    master_content = "/control/verbose 2\n\n"
    for mf in all_macro_files:
        master_content += f"/control/execute {mf}\n"
    (outdir / "run_all.mac").write_text(master_content, encoding="utf-8")

    print(f"DA TAO THANH CONG {count_jobs} FILE .MAC + run_all.mac VAO {outdir}")
    print("=" * 65)


if __name__ == "__main__":
    main()
