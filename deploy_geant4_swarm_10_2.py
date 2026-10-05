import os
import sys
import time
import json
import subprocess
import requests
from base64 import b64encode
from pathlib import Path
import nacl.encoding
import nacl.public

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(r"C:\antigravity_goat\10.2\Geant4_mac")
STATE_FILE = Path(r"C:\antigravity_goat\control_center\projects_state.json")
OAUTH_FILE = Path(r"C:\antigravity_goat\user_oauth_creds.json")

REPO_NAME = "geant4-benchmark-10-2"
GDRIVE_FOLDER_ID = "1RBUI6lx8yrnTgappHpAvfnZTCzSvR0nM"  # 10.2_Mac / 02_Geant4

ACCOUNTS = [
    'haoidlemystic1', 'vuicho', 'haoidle4zk', '67hao', 'idlemystich',
    'CarwynDuc', 'laolaolaoma09', 'Bethwl', 'coredaohaojack',
    'htvnhe', 'haohue27', 'fewhourtorelax', 'zotactothesun'
]

def set_repo_secret(owner: str, repo: str, token: str, secret_name: str, secret_value: str) -> bool:
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    pk_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    r = requests.get(pk_url, headers=headers)
    if r.status_code != 200:
        print(f"    [ERR] Khong the lay public key cho {owner}/{repo}: {r.status_code}")
        return False
    key_data = r.json()
    public_key = key_data["key"]
    key_id = key_data["key_id"]

    public_key_obj = nacl.public.PublicKey(public_key.encode("utf-8"), nacl.encoding.Base64Encoder)
    sealed_box = nacl.public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    encrypted_b64 = b64encode(encrypted).decode("utf-8")

    sec_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    payload = {"encrypted_value": encrypted_b64, "key_id": key_id}
    r_put = requests.put(sec_url, headers=headers, json=payload)
    return r_put.status_code in [201, 204]

def main():
    print("=" * 80)
    print("🚀 BẮT ĐẦU TRIỂN KHAI GEANT4 CLUSTER 14 TÀI KHOẢN (PAPER 10.2 / 10^6 HẠT)")
    print(f"Target Google Drive Folder: {GDRIVE_FOLDER_ID} (10.2_Mac / 02_Geant4)")
    print(f"Target Repo: {REPO_NAME} trên 14 accounts (140 parallel runners)")
    print("=" * 80)

    with open(STATE_FILE, "r", encoding="utf-8") as sf:
        state_data = json.load(sf)
    acc_config = state_data.get("accounts", {})

    with open(OAUTH_FILE, "r", encoding="utf-8") as of:
        oauth_json_str = of.read()

    # Step 1: Ensure Repos & Secrets on all 14 accounts
    print("\n>>> [BƯỚC 1/3] Kiểm tra Repository và thiết lập Secret Google Drive...")
    for acc in ACCOUNTS:
        tok = acc_config[acc]["pat_token"]
        headers = {"Authorization": f"token {tok}", "Accept": "application/vnd.github.v3+json"}
        
        # Check repo
        repo_url = f"https://api.github.com/repos/{acc}/{REPO_NAME}"
        r = requests.get(repo_url, headers=headers)
        if r.status_code == 404:
            print(f"  + Tạo repo mới: {acc}/{REPO_NAME}...")
            r_create = requests.post("https://api.github.com/user/repos", headers=headers, json={"name": REPO_NAME, "private": False})
            if r_create.status_code != 201:
                print(f"    [ERR] Không thể tạo repo cho {acc}: {r_create.text}")
                continue
        elif r.status_code == 200:
            print(f"  + Repo {acc}/{REPO_NAME} đã tồn tại.")

        # Set secret
        ok_sec = set_repo_secret(acc, REPO_NAME, tok, "GDRIVE_OAUTH_JSON", oauth_json_str)
        if ok_sec:
            print(f"  + Secret GDRIVE_OAUTH_JSON -> {acc}/{REPO_NAME} [OK]")
        else:
            print(f"  + [ERR] Không thể set secret cho {acc}")

    # Step 2: Initialize local git repo and push code to all 14 remotes
    print("\n>>> [BƯỚC 2/3] Commit và Push mã nguồn Geant4 lên 14 tài khoản GitHub...")
    subprocess.run(["git", "init"], cwd=str(BASE_DIR), stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.name", "Geant4Cluster"], cwd=str(BASE_DIR))
    subprocess.run(["git", "config", "user.email", "cluster@antigravity.io"], cwd=str(BASE_DIR))
    subprocess.run(["git", "add", "."], cwd=str(BASE_DIR))
    subprocess.run(["git", "commit", "-m", "Deploy Geant4 10.2 10^6 benchmark on 14 accounts"], cwd=str(BASE_DIR), stdout=subprocess.DEVNULL)
    subprocess.run(["git", "branch", "-M", "main"], cwd=str(BASE_DIR))

    for acc in ACCOUNTS:
        tok = acc_config[acc]["pat_token"]
        remote_url = f"https://{acc}:{tok}@github.com/{acc}/{REPO_NAME}.git"
        remote_name = f"remote_{acc}"

        subprocess.run(["git", "remote", "remove", remote_name], cwd=str(BASE_DIR), stderr=subprocess.DEVNULL)
        subprocess.run(["git", "remote", "add", remote_name, remote_url], cwd=str(BASE_DIR), stdout=subprocess.DEVNULL)

        print(f"  + Pushing to {acc}/{REPO_NAME}...")
        res_push = subprocess.run(["git", "push", "-u", remote_name, "main", "--force"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if res_push.returncode == 0:
            print(f"    -> Push thành công: {acc}/{REPO_NAME}")
        else:
            print(f"    -> [ERR] Push thất bại {acc}: {res_push.stderr[:100]}")

    # Step 3: Dispatch workflows
    print("\n>>> [BƯỚC 3/3] Kích hoạt 10 runners song song trên cả 14 tài khoản (Tổng 140 runners)...")
    primaries_str = "1000000"  # 10^6
    for acc in ACCOUNTS:
        tok = acc_config[acc]["pat_token"]
        headers = {"Authorization": f"token {tok}", "Accept": "application/vnd.github.v3+json"}
        disp_url = f"https://api.github.com/repos/{acc}/{REPO_NAME}/actions/workflows/geant4_parallel.yml/dispatches"
        payload = {
            "ref": "main",
            "inputs": {
                "primaries": primaries_str,
                "gdrive_folder": GDRIVE_FOLDER_ID
            }
        }
        r_disp = requests.post(disp_url, headers=headers, json=payload)
        if r_disp.status_code == 204:
            print(f"  🚀 {acc:<16} -> DISPATCH SUCCESS (204) [10 Runners kích hoạt!]")
        else:
            print(f"  ❌ {acc:<16} -> FAILED ({r_disp.status_code}): {r_disp.text[:80]}")
        time.sleep(0.5)

    print("\n" + "=" * 80)
    print("🎉 TOÀN BỘ 140 RUNNERS TRÊN 14 TÀI KHOẢN ĐÃ ĐƯỢC KÍCH HOẠT THÀNH CÔNG!")
    print("=" * 80)

if __name__ == "__main__":
    main()
