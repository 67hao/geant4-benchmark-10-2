import re
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 13 ACTIVE accounts (1983huehao excluded because Actions is disabled)
ACCOUNTS = [
    'haoidlemystic1', 'vuicho', 'haoidle4zk', '67hao', 'idlemystich',
    'CarwynDuc', 'laolaolaoma09', 'Bethwl', 'coredaohaojack',
    'htvnhe', 'haohue27', 'fewhourtorelax', 'zotactothesun'
]

NUM_RUNNERS_PER_ACC = 10

def main():
    mac_dir = Path(r"C:\antigravity_goat\10.2\Geant4_mac\macros")
    mac_files = sorted([f for f in mac_dir.glob("*.mac")])
    print(f"Tổng số file macro Geant4: {len(mac_files)}")

    all_jobs = []
    for f in mac_files:
        stem = f.stem
        content = f.read_text(encoding="utf-8")
        
        mat_match = re.search(r"/DetectorConstruction/Sample_Material\s+([A-Za-z0-9_]+)", content)
        mat = mat_match.group(1) if mat_match else "Blank"
        
        th_match = re.search(r"/DetectorConstruction/Sample_Thickness\s+([\d\.]+)\s*mm", content)
        th_mm = float(th_match.group(1)) if th_match else 0.0
        th_cm = th_mm / 10.0
        
        e_match = re.search(r"/gun/energy\s+([\d\.]+)\s*keV", content)
        e_kev = float(e_match.group(1)) if e_match else 0.0
        e_mev = e_kev / 1000.0

        all_jobs.append({
            "job_name": stem,
            "sample": mat,
            "energy_kev": e_kev,
            "energy_mev": e_mev,
            "thickness_cm": th_cm,
            "thickness_mm": th_mm,
            "macro_file": f.name
        })

    all_jobs.sort(key=lambda x: (0 if "blank" in x["job_name"] else 1, x["sample"], x["energy_kev"], x["thickness_cm"]))

    plan = {acc: {str(r): [] for r in range(1, NUM_RUNNERS_PER_ACC + 1)} for acc in ACCOUNTS}

    runner_list = []
    for acc in ACCOUNTS:
        for r in range(1, NUM_RUNNERS_PER_ACC + 1):
            runner_list.append((acc, str(r)))

    for idx, job in enumerate(all_jobs):
        acc, r_id = runner_list[idx % len(runner_list)]
        plan[acc][r_id].append(job)

    plan_file = Path(r"C:\antigravity_goat\10.2\Geant4_mac\geant4_plan_14acc.json")
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print(f"🎉 Đã sinh kế hoạch phân bổ {len(all_jobs)} jobs vào {plan_file} cho 13 accounts:")
    total_check = 0
    for acc in ACCOUNTS:
        total_acc_jobs = sum(len(plan[acc][str(r)]) for r in range(1, NUM_RUNNERS_PER_ACC + 1))
        total_check += total_acc_jobs
        print(f"  - Account: {acc:<16} | Tổng jobs: {total_acc_jobs} (mỗi runner ~ 1 job)")
    print(f"Tổng số jobs đã phân bổ: {total_check} / {len(all_jobs)}")

if __name__ == "__main__":
    main()
