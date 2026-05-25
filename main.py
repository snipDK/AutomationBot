import importlib
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import json
import shutil
from urllib.request import urlopen

# =========================================================
# AUTO INSTALL DEPENDENCIES
# =========================================================

def ensure_dependencies():
    dependencies = {
        "cv2": "opencv-python",
        "numpy": "numpy",
        "PIL": "Pillow",
        "pyautogui": "pyautogui",
    }

    for module_name, package_name in dependencies.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            print(f"Mangler {module_name}. Installerer {package_name}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name]
            )

ensure_dependencies()

# =========================================================
# IMPORTS
# =========================================================

import cv2
import numpy as np
from PIL import ImageGrab
import pyautogui

# =========================================================
# VERSION / UPDATE
# =========================================================

APP_VERSION = "1.1.0"

VERSION_URL = "https://raw.githubusercontent.com/snipDK/AutomationBot/main/version.txt"

UPDATE_URL = "https://raw.githubusercontent.com/snipDK/AutomationBot/main/main.py"

# =========================================================
# UPDATE FUNCTIONS
# =========================================================

def version_tuple(version):
    return tuple(map(int, version.strip().split(".")))


def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


# =========================================================
# MAIN GUI
# =========================================================

class AutomationGUI:

    def __init__(self, root):

        self.root = root
        self.root.title(f"Automation Bot v{APP_VERSION}")
        self.root.geometry("950x600")

        self.running = False
        self.rect_start = None
        self.rect = None
        self.overlay = None

        self.templates = []

        self.confidence = tk.DoubleVar(value=0.80)

        self.root.bind("<Escape>", self.stop_automation_hotkey)

        # =====================================================
        # LISTBOX
        # =====================================================

        self.listbox = tk.Listbox(
            root,
            width=100,
            height=20
        )

        self.listbox.pack(padx=10, pady=10)

        self.listbox.bind("<Double-1>", self.toggle_click_type)

        # =====================================================
        # BUTTON FRAME
        # =====================================================

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(
            btn_frame,
            text="🎯 Marker område",
            command=self.start_area_select,
            width=18
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="📂 Tilføj billede",
            command=self.add_image,
            width=18
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="⏸ Tilføj pause",
            command=self.add_pause,
            width=18
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="🗑 Slet valgt",
            command=self.delete_selected,
            width=18
        ).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="⬆ Flyt op",
            command=lambda: self.move_item(-1),
            width=18
        ).grid(row=0, column=4, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="⬇ Flyt ned",
            command=lambda: self.move_item(1),
            width=18
        ).grid(row=0, column=5, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="Enkeltklik",
            command=lambda: self.set_click("single"),
            width=18
        ).grid(row=1, column=0, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="Dobbeltklik",
            command=lambda: self.set_click("double"),
            width=18
        ).grid(row=1, column=1, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="💾 Gem profil",
            command=self.save_profile,
            width=18
        ).grid(row=1, column=2, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="📂 Indlæs profil",
            command=self.load_profile,
            width=18
        ).grid(row=1, column=3, padx=5, pady=5)

        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start",
            bg="green",
            fg="white",
            width=18,
            command=self.toggle_automation
        )

        self.start_btn.grid(row=1, column=4, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="🔄 Søg opdatering",
            command=self.check_for_updates,
            width=18
        ).grid(row=2, column=0, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="🛠 Byg EXE",
            command=self.build_exe,
            width=18
        ).grid(row=2, column=1, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="❌ Luk",
            command=root.quit,
            width=18
        ).grid(row=2, column=2, padx=5, pady=5)

        # =====================================================
        # CONFIDENCE SLIDER
        # =====================================================

        confidence_frame = tk.Frame(root)
        confidence_frame.pack(pady=10)

        tk.Label(
            confidence_frame,
            text="Confidence:"
        ).pack(side=tk.LEFT)

        tk.Scale(
            confidence_frame,
            from_=0.50,
            to=0.99,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            variable=self.confidence,
            length=300
        ).pack(side=tk.LEFT, padx=10)

        # =====================================================
        # CREATE FOLDER
        # =====================================================

        os.makedirs("screens", exist_ok=True)

    # =========================================================
    # AREA SELECT
    # =========================================================

    def start_area_select(self):

        self.root.withdraw()

        time.sleep(0.3)

        self.overlay = tk.Toplevel()

        self.overlay.attributes("-fullscreen", True)

        self.overlay.attributes("-alpha", 0.3)

        self.overlay.configure(bg="black")

        self.canvas = tk.Canvas(
            self.overlay,
            bg="black",
            highlightthickness=0
        )

        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def on_mouse_down(self, event):
        self.rect_start = (event.x, event.y)

    def on_mouse_drag(self, event):

        if self.rect:
            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(
            self.rect_start[0],
            self.rect_start[1],
            event.x,
            event.y,
            outline="red",
            width=2
        )

    def on_mouse_up(self, event):

        x1, y1 = self.rect_start
        x2, y2 = event.x, event.y

        self.overlay.destroy()

        self.root.deiconify()

        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        image = ImageGrab.grab(bbox=(x1, y1, x2, y2))

        filename = f"screens/template_{int(time.time())}.png"

        image.save(filename)

        self.templates.append({
            "type": "click",
            "path": filename,
            "click": "single"
        })

        self.update_list()

    # =========================================================
    # ADD IMAGE
    # =========================================================

    def add_image(self):

        path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg")
            ]
        )

        if not path:
            return

        self.templates.append({
            "type": "click",
            "path": path,
            "click": "single"
        })

        self.update_list()

    # =========================================================
    # ADD PAUSE
    # =========================================================

    def add_pause(self):

        popup = tk.Toplevel(self.root)

        popup.title("Pause")

        popup.geometry("250x120")

        tk.Label(
            popup,
            text="Pause i sekunder:"
        ).pack(pady=10)

        entry = tk.Entry(popup)

        entry.pack(pady=5)

        def save_pause():

            try:
                duration = float(entry.get())

                self.templates.append({
                    "type": "pause",
                    "duration": duration
                })

                self.update_list()

                popup.destroy()

            except:
                messagebox.showerror(
                    "Fejl",
                    "Ugyldigt nummer"
                )

        tk.Button(
            popup,
            text="Gem",
            command=save_pause
        ).pack(pady=10)

    # =========================================================
    # DELETE
    # =========================================================

    def delete_selected(self):

        selected = self.listbox.curselection()

        if not selected:
            return

        del self.templates[selected[0]]

        self.update_list()

    # =========================================================
    # MOVE ITEMS
    # =========================================================

    def move_item(self, direction):

        selected = self.listbox.curselection()

        if not selected:
            return

        index = selected[0]

        new_index = index + direction

        if new_index < 0 or new_index >= len(self.templates):
            return

        self.templates[index], self.templates[new_index] = \
            self.templates[new_index], self.templates[index]

        self.update_list()

        self.listbox.select_set(new_index)

    # =========================================================
    # CLICK TYPE
    # =========================================================

    def set_click(self, click_type):

        selected = self.listbox.curselection()

        if not selected:
            return

        index = selected[0]

        if self.templates[index]["type"] == "click":
            self.templates[index]["click"] = click_type

        self.update_list()

    def toggle_click_type(self, event):

        selected = self.listbox.curselection()

        if not selected:
            return

        index = selected[0]

        item = self.templates[index]

        if item["type"] != "click":
            return

        item["click"] = \
            "double" if item["click"] == "single" else "single"

        self.update_list()

    # =========================================================
    # UPDATE LIST
    # =========================================================

    def update_list(self):

        self.listbox.delete(0, tk.END)

        for item in self.templates:

            if item["type"] == "pause":

                self.listbox.insert(
                    tk.END,
                    f"⏸ Pause ({item['duration']} sek)"
                )

            else:

                name = os.path.basename(item["path"])

                self.listbox.insert(
                    tk.END,
                    f"{name} ({item['click']})"
                )

    # =========================================================
    # SAVE PROFILE
    # =========================================================

    def save_profile(self):

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json")
            ]
        )

        if not path:
            return

        data = {
            "confidence": self.confidence.get(),
            "templates": self.templates
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        messagebox.showinfo(
            "Automation Bot",
            "Profil gemt"
        )

    # =========================================================
    # LOAD PROFILE
    # =========================================================

    def load_profile(self):

        path = filedialog.askopenfilename(
            filetypes=[
                ("JSON files", "*.json")
            ]
        )

        if not path:
            return

        try:

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.templates = data.get("templates", [])

            self.confidence.set(
                float(data.get("confidence", 0.8))
            )

            self.update_list()

            messagebox.showinfo(
                "Automation Bot",
                "Profil indlæst"
            )

        except Exception as e:

            messagebox.showerror(
                "Fejl",
                str(e)
            )

    # =========================================================
    # UPDATE SYSTEM
    # =========================================================

    def check_for_updates(self):

        try:

            latest_version = urlopen(
                VERSION_URL
            ).read().decode().strip()

            if version_tuple(latest_version) > version_tuple(APP_VERSION):

                answer = messagebox.askyesno(
                    "Automation Bot",
                    f"Ny version fundet!\n\n"
                    f"Din version: {APP_VERSION}\n"
                    f"Ny version: {latest_version}\n\n"
                    f"Vil du installere opdateringen?"
                )

                if not answer:
                    return

                with urlopen(UPDATE_URL) as response:
                    new_code = response.read().decode("utf-8")

                current_file = os.path.abspath(__file__)

                backup_file = current_file + ".bak"

                shutil.copyfile(current_file, backup_file)

                with open(current_file, "w", encoding="utf-8") as f:
                    f.write(new_code)

                messagebox.showinfo(
                    "Automation Bot",
                    "Opdatering installeret.\nProgrammet genstarter nu."
                )

                restart_program()

            else:

                messagebox.showinfo(
                    "Automation Bot",
                    "Du har allerede nyeste version."
                )

        except Exception as e:

            messagebox.showerror(
                "Opdaterings fejl",
                str(e)
            )

    # =========================================================
    # BUILD EXE
    # =========================================================

    def build_exe(self):

        try:

            script_path = os.path.abspath(__file__)

            project_dir = os.path.dirname(script_path)

            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "pyinstaller"
            ])

            subprocess.check_call([
                sys.executable,
                "-m",
                "PyInstaller",
                "--onefile",
                "--noconsole",
                "--name",
                "AutomationBot",
                script_path
            ])

            messagebox.showinfo(
                "Automation Bot",
                f"EXE oprettet:\n"
                f"{project_dir}/dist/AutomationBot.exe"
            )

        except Exception as e:

            messagebox.showerror(
                "Build fejl",
                str(e)
            )

    # =========================================================
    # START / STOP
    # =========================================================

    def toggle_automation(self):

        if not self.running:

            self.running = True

            self.start_btn.config(
                text="⛔ Stop",
                bg="red"
            )

            threading.Thread(
                target=self.run_automation,
                daemon=True
            ).start()

        else:

            self.running = False

            self.start_btn.config(
                text="▶ Start",
                bg="green"
            )

    def stop_automation_hotkey(self, event=None):

        if self.running:

            self.running = False

            self.start_btn.config(
                text="▶ Start",
                bg="green"
            )

            messagebox.showinfo(
                "Automation Bot",
                "Bot stoppet med ESC"
            )

    # =========================================================
    # AUTOMATION LOOP
    # =========================================================

    def run_automation(self):

        while self.running:

            for item in self.templates:

                if not self.running:
                    break

                # ---------------- PAUSE ----------------

                if item["type"] == "pause":

                    time.sleep(item["duration"])

                    continue

                path = item["path"]

                click_type = item["click"]

                if not os.path.exists(path):
                    continue

                screen = cv2.cvtColor(
                    np.array(ImageGrab.grab()),
                    cv2.COLOR_RGB2GRAY
                )

                template = cv2.imread(
                    path,
                    cv2.IMREAD_GRAYSCALE
                )

                if template is None:
                    continue

                result = cv2.matchTemplate(
                    screen,
                    template,
                    cv2.TM_CCOEFF_NORMED
                )

                _, max_val, _, max_loc = cv2.minMaxLoc(result)

                if max_val >= self.confidence.get():

                    h, w = template.shape

                    x = max_loc[0] + w // 2
                    y = max_loc[1] + h // 2

                    if click_type == "single":

                        pyautogui.click(x, y)

                    else:

                        pyautogui.doubleClick(x, y)

                time.sleep(0.2)

        self.root.after(
            0,
            lambda: self.start_btn.config(
                text="▶ Start",
                bg="green"
            )
        )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = AutomationGUI(root)

    root.mainloop()
