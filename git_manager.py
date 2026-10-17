#!/usr/bin/env python3
"""
Simple GitHub Manager (Auto Init + Auto Create Repo + Sensitive File Guard)
Jalankan: python git_manager.py
"""

import os
import subprocess
import sys
import fnmatch

# ============================================================
# Konfigurasi pola file sensitif
# ============================================================
SENSITIVE_PATTERNS = [
    ".env", ".env.*", "*.env",
    "*.key", "*.pem", "*.p12", "*.pfx", "*.keystore",
    "id_rsa", "id_rsa.*", "id_dsa", "id_ecdsa", "id_ed25519",
    "*.secret", "*.secrets",
    "credentials", "credentials.*",
    "*.crt",
    "config.local.*",
    "*.local.json",
]

SENSITIVE_DIRS = [".ssh", ".aws", ".gnupg", ".docker"]

# File yang tidak perlu dianggap sensitif meski namanya cocok
WHITELIST = [".env.example", ".env.sample", ".env.template", "config.example.*"]

# ============================================================
# Helper
# ============================================================
def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def cek_repo(path="."):
    return os.path.isdir(os.path.join(path, ".git"))

def cek_gh():
    rc, out, err = run_cmd("gh auth status")
    return rc == 0

# ============================================================
# Deteksi file sensitif
# ============================================================
def is_sensitive(path):
    base = os.path.basename(path)
    for wl in WHITELIST:
        if fnmatch.fnmatch(base, wl):
            return False
    for pat in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(base, pat):
            return True
    return False

def scan_sensitive():
    """Scan seluruh working directory, kembalikan list path sensitif."""
    hasil = []
    skip_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__",
                 "dist", "build", ".next", ".nuxt", "target", "vendor"}
    for root, dirs, files in os.walk("."):
        # filter folder
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        # skip isi folder sensitif (misal .ssh)
        if any(sd in root for sd in SENSITIVE_DIRS):
            for f in files:
                full = os.path.join(root, f)
                if full.startswith(".\\") or full.startswith("./"):
                    full = full[2:]
                hasil.append(full)
            continue
        for f in files:
            full = os.path.join(root, f)
            if full.startswith(".\\") or full.startswith("./"):
                full = full[2:]
            if is_sensitive(full):
                hasil.append(full)
    return sorted(set(hasil))

def get_tracked_sensitive():
    """Ambil path sensitif yang sudah ter-track git (kalau ada)."""
    rc, out, err = run_cmd("git ls-files")
    if rc != 0:
        return []
    tracked = out.splitlines()
    return [f for f in tracked if is_sensitive(f)]

def konfirmasi_sensitive():
    """
    Tampilkan file sensitif, minta user pilih yang mau di-skip.
    Return list file yang harus di-skip (unstage + gitignore).
    """
    files = scan_sensitive()
    if not files:
        print("\n✅ Tidak ada file sensitif terdeteksi.")
        return []

    print("\n" + "⚠️ " * 15)
    print("  PERINGATAN: FILE SENSITIF TERDETEKSI")
    print("⚠️ " * 15)
    print("\nFile berikut berpotensi berisi data rahasia:")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f}")
    print("\nPilihan:")
    print("  - Ketik nomor yang mau di-SKIP (tidak diupload), pisah koma")
    print("    contoh: 1,2   -> skip file 1 dan 2")
    print("  - Ketik 'all'      -> skip SEMUA file sensitif")
    print("  - Ketik 'none'     -> upload SEMUA (berisiko!)")
    print("  - Tekan Enter      -> skip SEMUA (paling aman)")

    pilihan = input("\nPilihan kamu: ").strip().lower()

    if pilihan == "" or pilihan == "all":
        skip = files
    elif pilihan == "none":
        skip = []
    else:
        skip = []
        for tok in pilihan.split(","):
            tok = tok.strip()
            if tok.isdigit():
                idx = int(tok) - 1
                if 0 <= idx < len(files):
                    skip.append(files[idx])
                else:
                    print(f"⚠️  Nomor {tok} tidak valid, diabaikan.")
    return skip

def tangani_skip(skip_files):
    """Unstage & gitignore file yang di-skip."""
    if not skip_files:
        print("\n✅ Semua file diupload (kamu sudah konfirmasi).")
        return

    print(f"\n🚫 Akan di-skip {len(skip_files)} file:")
    for f in skip_files:
        print(f"   - {f}")

    # Tulis ke .gitignore
    gitignore_path = ".gitignore"
    existing = set()
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as fh:
            existing = set(l.strip() for l in fh if l.strip())

    added = []
    with open(gitignore_path, "a", encoding="utf-8") as fh:
        for f in skip_files:
            if f not in existing:
                fh.write(f + "\n")
                added.append(f)

    # Unstage kalau sudah terlanjur ter-add
    for f in skip_files:
        run_cmd(f'git rm --cached -r "{f}" 2>nul')

    if added:
        print(f"✅ Ditambahkan ke .gitignore: {len(added)} file")
    print("✅ File sensitif aman, tidak akan ikut ter-upload.")

# ============================================================
# Setup otomatis
# ============================================================
def auto_setup():
    print("\n🔧 Memulai setup otomatis...")

    if not cek_repo():
        print("📁 Inisialisasi Git repository...")
        rc, out, err = run_cmd("git init -b main")
        if rc != 0:
            print(f"❌ Gagal git init: {err}")
            return False
        print("✅ Git init berhasil (branch: main)")
    else:
        print("ℹ️  Git repository sudah ada, skip init.")
        run_cmd("git branch -M main")

    # Cek commit awal
    rc, out, err = run_cmd("git rev-parse --verify HEAD")
    if rc != 0:
        # SEBELUM commit awal, cek file sensitif dulu!
        skip = konfirmasi_sensitive()
        tangani_skip(skip)

        print("\n💾 Membuat commit awal...")
        run_cmd("git add .")
        rc, out, err = run_cmd('git commit -m "Initial commit"')
        if rc != 0 and "nothing to commit" not in out.lower():
            print(f"⚠️  Commit awal: {out or err}")
        else:
            print("✅ Commit awal berhasil")

    # Cek remote origin
    rc, out, err = run_cmd("git remote get-url origin")
    if rc == 0:
        print(f"ℹ️  Remote origin sudah ada: {out}")
        return True

    # Minta nama repo
    default_name = os.path.basename(os.getcwd())
    print(f"\n🌐 Membuat repository GitHub baru")
    print(f"   Nama folder saat ini: {default_name}")
    repo_name = input(f"Nama repository [default: {default_name}]: ").strip()
    if not repo_name:
        repo_name = default_name

    # Validasi sederhana
    if " " in repo_name:
        print("⚠️  Nama repo tidak boleh ada spasi, spasi diganti '-'")
        repo_name = repo_name.replace(" ", "-")

    vis = input("Tipe repo? (public/private) [default: private]: ").strip().lower()
    if vis not in ("public", "private"):
        vis = "private"

    print(f"\n🚀 Membuat repo '{repo_name}' ({vis}) dan push...")
    cmd = f"gh repo create {repo_name} --{vis} --source=. --remote=origin --push"
    rc, out, err = run_cmd(cmd)

    if rc != 0:
        print(f"❌ Gagal membuat repo GitHub: {err}")
        return False

    print(f"✅ Repository GitHub berhasil dibuat dan di-push!")
    print(f"   {out}")
    return True

# ============================================================
# Menu utama
# ============================================================
def menu():
    print("\n" + "="*40)
    print("       SIMPLE GITHUB MANAGER")
    print("="*40)
    print("1. Upload (add, commit, push)")
    print("2. Pull (ambil update terbaru)")
    print("3. Delete (hapus file/folder dari repo)")
    print("4. Status repository")
    print("5. Scan file sensitif sekarang")
    print("6. Keluar")
    print("="*40)

def upload():
    # Scan & konfirmasi file sensitif dulu
    skip = konfirmasi_sensitive()
    tangani_skip(skip)

    pesan = input("\nPesan commit: ").strip()
    if not pesan:
        pesan = "update otomatis"

    print("\n📦 Menambahkan semua perubahan...")
    rc, out, err = run_cmd("git add .")
    if rc != 0:
        print(f"❌ Gagal add: {err}")
        return
    print("✅ Add berhasil")

    print("\n💾 Commit...")
    rc, out, err = run_cmd(f'git commit -m "{pesan}"')
    if rc != 0:
        if "nothing to commit" not in out.lower():
            print(f"⚠️  {out or err}")
            return
    else:
        print("✅ Commit berhasil")

    print("\n🚀 Push ke remote...")
    rc, out, err = run_cmd("git push")
    if rc != 0:
        print(f"❌ Push gagal: {err}")
    else:
        print("✅ Push berhasil!")

def pull():
    print("\n⬇️  Pull dari remote...")
    rc, out, err = run_cmd("git pull")
    if rc != 0:
        print(f"❌ Pull gagal: {err}")
    else:
        print(f"✅ Pull berhasil:\n{out}")

def delete():
    print("\n🗑️  Hapus file/folder dari repository")
    target = input("Path yang mau dihapus: ").strip()
    if not target:
        print("❌ Path kosong!")
        return
    if not os.path.exists(target):
        print(f"❌ '{target}' tidak ditemukan!")
        return

    konfirmasi = input(f"Yakin hapus '{target}'? (y/n): ").strip().lower()
    if konfirmasi != 'y':
        print("❌ Dibatalkan")
        return

    rc, out, err = run_cmd(f'git rm -r "{target}"')
    if rc != 0:
        print(f"❌ Gagal rm: {err}")
        return
    print("✅ File terhapus dari git")

    pesan = input("Pesan commit (kosongkan untuk default): ").strip()
    if not pesan:
        pesan = f"hapus {target}"

    run_cmd(f'git commit -m "{pesan}"')
    print("✅ Commit berhasil")

    print("\n🚀 Push...")
    rc, out, err = run_cmd("git push")
    if rc != 0:
        print(f"❌ Push gagal: {err}")
    else:
        print("✅ Push berhasil!")

def status():
    rc, out, err = run_cmd("git status -s")
    branch = run_cmd("git branch --show-current")[1]
    print(f"\n📋 Branch: {branch}")
    print("📋 Status:")
    print(out if out else "  (tidak ada perubahan)")

def scan_menu():
    """Menu khusus scan file sensitif tanpa upload."""
    files = scan_sensitive()
    if not files:
        print("\n✅ Tidak ada file sensitif terdeteksi.")
        return
    print(f"\n⚠️  Terdeteksi {len(files)} file sensitif:")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f}")
    print("\nFile di atas BELUM otomatis di-gitignore.")
    tanya = input("Tambahkan semua ke .gitignore sekarang? (y/n): ").strip().lower()
    if tanya == "y":
        tangani_skip(files)

# ============================================================
# Main
# ============================================================
def main():
    if not cek_gh():
        print("❌ GitHub CLI belum login atau belum terinstall.")
        print("   Jalankan: gh auth login")
        sys.exit(1)

    if not auto_setup():
        print("\n❌ Setup otomatis gagal. Periksa error di atas.")
        sys.exit(1)

    while True:
        menu()
        pilih = input("Pilih menu (1-6): ").strip()

        if pilih == "1":
            upload()
        elif pilih == "2":
            pull()
        elif pilih == "3":
            delete()
        elif pilih == "4":
            status()
        elif pilih == "5":
            scan_menu()
        elif pilih == "6":
            print("\n👋 Sampai jumpa!")
            break
        else:
            print("❌ Pilihan tidak valid!")

        input("\nTekan Enter untuk lanjut...")

if __name__ == "__main__":
    main()