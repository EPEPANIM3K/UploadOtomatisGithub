#!/usr/bin/env python3
"""
Simple GitHub Manager
Jalankan: python git_manager.py
"""

import os
import subprocess
import sys

def run_cmd(cmd, cwd=None):
    """Jalankan command shell dan return output"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def cek_repo(path="."):
    """Cek apakah folder adalah git repo"""
    return os.path.isdir(os.path.join(path, ".git"))

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
    if not cek_repo():
        print("❌ Folder ini bukan git repository!")
        return

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
        print(f"⚠️  {out or err}")
        # Kalau tidak ada perubahan, lanjut saja
        if "nothing to commit" not in out.lower():
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
    if not cek_repo():
        print("❌ Folder ini bukan git repository!")
        return
    
    print("\n⬇️  Pull dari remote...")
    rc, out, err = run_cmd("git pull")
    if rc != 0:
        print(f"❌ Pull gagal: {err}")
    else:
        print(f"✅ Pull berhasil:\n{out}")

def delete():
    if not cek_repo():
        print("❌ Folder ini bukan git repository!")
        return
    
    print("\n🗑️  Hapus file/folder dari repository")
    print("Contoh: file.txt  atau  folder/")
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
    
    print(f"\n🔧 Menghapus '{target}'...")
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
    if not cek_repo():
        print("❌ Folder ini bukan git repository!")
        return
    rc, out, err = run_cmd("git status -s")
    branch = run_cmd("git branch --show-current")[1]
    print(f"\n📋 Branch: {branch}")
    print("📋 Status:")
    print(out if out else "  (tidak ada perubahan)")

def main():
    if not cek_repo():
        print("⚠️  Folder saat ini bukan git repository.")
        print("Jalankan: git init && git remote add origin <url>")
        sys.exit(1)
    
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