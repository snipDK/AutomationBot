import importlib
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from urllib.request import urlopen
import os

# =========================================================
# AUTO INSTALL DEPENDENCIES
# =========================================================

def ensure_package(module_name, package_name):
    try:
        importlib.import_module(module_name)
    except ImportError:
        print(f"Installerer {package_name}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package_name]
        )

ensure_package("requests", "requests")

# =========================================================
# VERSION INFO
# =========================================================

APP_VERSION = "1.0.0"

# RAW GITHUB LINKS
VERSION_URL = "https://github.com/snipDK/AutomationBot/edit/main/version.txt"

UPDATE_URL = "https://github.com/snipDK/AutomationBot/blob/main/main.py"

# =========================================================
# UPDATE SYSTEM
# =========================================================

def version_tuple(version):
    return tuple(map(int, version.strip().split(".")))

def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)

def check_for_updates():
    try:
        print("Checker efter opdateringer...")

        latest_version = urlopen(VERSION_URL).read().decode().strip()

        print(f"Lokal version : {APP_VERSION}")
        print(f"Nyeste version: {latest_version}")

        if version_tuple(latest_version) > version_tuple(APP_VERSION):

            answer = messagebox.askyesno(
                "Opdatering fundet",
                f"Ny version {latest_version} fundet.\n\n"
                f"Din version: {APP_VERSION}\n\n"
                "Vil du opdatere nu?"
            )

            if not answer:
                return

            print("Downloader ny version...")

            new_code = urlopen(UPDATE_URL).read().decode("utf-8")

            current_file = os.path.abspath(__file__)
            backup_file = current_file + ".bak"

            # backup
            if os.path.exists(current_file):
                with open(current_file, "r", encoding="utf-8") as f:
                    old_code = f.read()

                with open(backup_file, "w", encoding="utf-8") as f:
                    f.write(old_code)

            # skriv ny version
            with open(current_file, "w", encoding="utf-8") as f:
                f.write(new_code)

            messagebox.showinfo(
                "Opdatering færdig",
                "Programmet er opdateret.\n\n"
                "Programmet genstarter nu."
            )

            restart_program()

        else:
            messagebox.showinfo(
                "Ingen opdatering",
                "Du har allerede nyeste version."
            )

    except Exception as e:
        messagebox.showerror(
            "Opdaterings fejl",
            f"Kunne ikke hente opdatering:\n\n{e}"
        )

# =========================================================
# GUI
# =========================================================

class App:

    def __init__(self, root):

        self.root = root
        self.root.title("Automation Bot")
        self.root.geometry("500x250")

        title = tk.Label(
            root,
            text=f"Automation Bot\nVersion {APP_VERSION}",
            font=("Arial", 18)
        )
        title.pack(pady=20)

        update_btn = tk.Button(
            root,
            text="🔄 Søg efter opdatering",
            font=("Arial", 12),
            command=check_for_updates,
            width=25,
            height=2
        )
        update_btn.pack(pady=20)

        exit_btn = tk.Button(
            root,
            text="❌ Luk",
            font=("Arial", 12),
            command=root.destroy,
            width=25,
            height=2
        )
        exit_btn.pack(pady=10)

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = App(root)

    root.mainloop()
