#!/usr/bin/env python3
"""
Simple GitHub Manager (Auto Init + Auto Create Repo)
Jalankan: python git_manager.py
"""

import os
import subprocess
import sys

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
    """Cek apakah GitHub CLI terinstall dan sudah login"""
    rc, out, err = run_cmd("gh auth status")
    if rc != 0:
        print("❌ GitHub CLI belum login atau belum terinstall.")
        print("   Jalankan: gh auth login")
        return False
    return True

def auto_setup():
    """
    Otomatis:
    1. git init (jika belum)
    2. git add + commit awal (jika belum ada commit)
    3. gh repo create + set remote origin + push
    """
    print("\n🔧 Memulai setup otomatis...")

    # 1. Git init jika belum
    if not cek_repo():
        print("📁 Inisialisasi Git repository...")
        rc, out, err = run_cmd("git init -b main")
        if rc != 0:
            print(f"❌ Gagal git init: {err}")
            return False
        print("✅ Git init berhasil (branch: main)")
    else:
        print("ℹ️  Git repository sudah ada, skip init.")
        # Pastikan branch main
        run_cmd("git branch -M main")

    # 2. Cek apakah sudah ada commit
    rc, out, err = run_cmd("git rev-parse --verify HEAD")
    if rc != 0:
        # Belum ada commit, buat commit awal
        print("💾 Membuat commit awal...")
        run_cmd("git add .")
        rc, out, err = run_cmd('git commit -m "Initial commit"')
        if rc != 0 and "nothing to commit" not in out.lower():
            print(f"⚠️  Commit awal: {out or err}")
        else:
            print("✅ Commit awal berhasil")

    # 3. Cek apakah sudah ada remote origin
    rc, out, err = run_cmd("git remote get-url origin")
    if rc == 0:
        print(f"ℹ️  Remote origin sudah ada: {out}")
        return True

    # 4. Buat repo GitHub otomatis
    # Nama repo default = nama folder saat ini
    repo_name = os.path.basename(os.getcwd())
    print(f"🌐 Membuat repository GitHub: {repo_name}")

    # Tanya public/private
    vis = input("Tipe repo? (public/private) [default: private]: ").strip().lower()
    if vis not in ("public", "private"):
        vis = "private"

    # gh repo create dengan --source . --remote origin --push
    cmd = f"gh repo create {repo_name} --{vis} --source=. --remote=origin --push"
    rc, out, err = run_cmd(cmd)

    if rc != 0:
        print(f"❌ Gagal membuat repo GitHub: {err}")
        return False

    print(f"✅ Repository GitHub berhasil dibuat dan di-push!")
    print(f"   {out}")
    return True

def menu():
    print("\n" + "="*40)
    print("       SIMPLE GITHUB MANAGER")
    print("="*40)
    print("1. Upload (add, commit, push)")
    print("2. Pull (ambil update terbaru)")
    print("3. Delete (hapus file/folder dari repo)")
    print("4. Status repository")
    print("5. Keluar")
    print("="*40)

def upload():
    pesan = input("Pesan commit: ").strip()
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

def main():
    # Cek gh CLI
    if not cek_gh():
        sys.exit(1)

    # Auto setup: init, create repo, remote, push
    if not auto_setup():
        print("\n❌ Setup otomatis gagal. Periksa error di atas.")
        sys.exit(1)

    # Masuk menu utama
    while True:
        menu()
        pilih = input("Pilih menu (1-5): ").strip()

        if pilih == "1":
            upload()
        elif pilih == "2":
            pull()
        elif pilih == "3":
            delete()
        elif pilih == "4":
            status()
        elif pilih == "5":
            print("\n👋 Sampai jumpa!")
            break
        else:
            print("❌ Pilihan tidak valid!")

        input("\nTekan Enter untuk lanjut...")

if __name__ == "__main__":
    main()