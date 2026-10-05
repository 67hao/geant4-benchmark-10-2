import os
import sys
import json
import time
from pathlib import Path
import pandas as pd
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, r"C:\antigravity_goat\10.2\Geant4_mac")
import gdrive_helper

STATE_FILE = Path(r"C:\antigravity_goat\control_center\projects_state.json")
GDRIVE_FLUX_FOLDER_ID = "1UF8WDpf-E_ocj7IkT9KREB7Ih7O2l6Na"  # 10.2_Mac / 02_Geant4 / 02_Flux_Data
TOTAL_JOBS = 141

ACCOUNTS = [
    'haoidlemystic1', 'vuicho', 'haoidle4zk', '67hao', 'idlemystich',
    'CarwynDuc', 'laolaolaoma09', 'Bethwl', 'coredaohaojack', '1983huehao',
    'htvnhe', 'haohue27', 'fewhourtorelax', 'zotactothesun'
]

def check_github_actions_status():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state_data = json.load(f)
    acc_config = state_data.get("accounts", {})

    status_summary = {}
    for acc in ACCOUNTS:
        tok = acc_config[acc]["pat_token"]
        headers = {"Authorization": f"token {tok}", "Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{acc}/geant4-benchmark-10-2/actions/runs?per_page=1"
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                runs = r.json().get("workflow_runs", [])
                if runs:
                    run = runs[0]
                    status_summary[acc] = f"{run['status']} ({run['conclusion'] or 'in_progress'})"
                else:
                    status_summary[acc] = "no_runs"
            else:
                status_summary[acc] = f"HTTP {r.status_code}"
        except Exception as e:
            status_summary[acc] = f"ERR: {e}"
    return status_summary

def check_drive_flux_files():
    service = gdrive_helper.get_drive_service()
    q = f"'{GDRIVE_FLUX_FOLDER_ID}' in parents and trashed = false"
    res = service.files().list(q=q, pageSize=200, fields="files(id, name, size)").execute()
    files = res.get("files", [])
    return files

def main():
    print("=" * 80)
    print("📊 TIẾN ĐỘ THỰC THI GEANT4 CLUSTER (PAPER 10.2 - 10^6 HẠT)")
    print(f"Tổng số jobs mục tiêu: {TOTAL_JOBS}")
    print(f"Thư mục Google Drive Flux: {GDRIVE_FLUX_FOLDER_ID}")
    print("=" * 80)

    # 1. Trạng thái GitHub Actions
    gh_status = check_github_actions_status()
    print("\n🔍 Trạng thái Workflow trên 14 tài khoản GitHub:")
    for acc, st in gh_status.items():
        print(f"  - {acc:<16} : {st}")

    # 2. File kết quả flux trên Drive
    files = check_drive_flux_files()
    print(f"\n📂 Tổng số file flux đã upload lên Drive: {len(files)} / 140 runners")
    for f in sorted(files, key=lambda x: x['name']):
        print(f"  + [{f['id']}] {f['name']} ({int(f.get('size',0)):,} bytes)")

if __name__ == "__main__":
    main()
