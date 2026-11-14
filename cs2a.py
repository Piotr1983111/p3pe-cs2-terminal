#!/usr/bin/env python3
# cs2_file_terminal_gui.py - Cyber Analytic Terminal (P3PE) - wersja okienkowa (tkinter)
import os
import sys
import shutil
import shlex
import socket
import platform
import subprocess
import threading
import queue
import time
import locale
import tkinter as tk
from tkinter import ttk, simpledialog
from datetime import datetime
from pathlib import Path

# ---------------- KOLORY ----------------
BG = "#050b14"
PANEL = "#0a1626"
CYAN = "#00e5ff"
BLUE = "#3d8bff"
GREEN = "#39ff88"
YELLOW = "#ffd166"
RED = "#ff5c6c"
MAGENTA = "#d67bff"
DIM = "#5f7a93"
FONT = ("Consolas", 10)
FONT_B = ("Consolas", 10, "bold")

# ---------------- SANDBOX FS ----------------
SANDBOX_ROOT = os.path.join(os.getcwd(), ".terminal_fs")
os.makedirs(SANDBOX_ROOT, exist_ok=True)


def sandbox_path(path):
    if not path:
        return SANDBOX_ROOT
    candidate = os.path.realpath(os.path.join(SANDBOX_ROOT, path))
    root = os.path.realpath(SANDBOX_ROOT)
    if os.path.commonpath([candidate, root]) != root:
        raise ValueError("Ścieżka poza sandboxem niedozwolona.")
    return candidate


def console_encoding():
    """Kodowanie wyjścia narzędzi konsolowych (na Windows to strona OEM)."""
    if os.name == "nt":
        try:
            import ctypes
            return f"cp{ctypes.windll.kernel32.GetOEMCP()}"
        except Exception:
            pass
    return locale.getpreferredencoding(False)


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # nic nie wysyła, tylko wybiera interfejs
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "N/A"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("P3PE CS2 Cyber Analytic Terminal")
        self.geometry("1150x760")
        self.minsize(900, 600)
        self.configure(bg=BG)

        self.q = queue.Queue()
        self.proc = None
        self.history = []
        self.hist_idx = 0

        self.fs_commands = {
            "mkfolder": self.mkfolder, "ls": self.ls, "touch": self.touch,
            "write": self.write_file, "read": self.read_file, "rm": self.rm,
        }
        self.net_commands = {
            "wifi_scan": self.wifi_scan, "ping": self.ping,
            "traceroute": self.traceroute, "systeminfo": self.system_info,
            "netstat": self.netstat, "nmap_scan": self.run_python_script,
            "upnp": self.ssdp_discover,
        }

        self._style()
        self._build_ui()
        self.after(50, self._poll_queue)
        self.after(200, self._startup_scan)

    # ------------------------------------------------ UI
    def _style(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                     foreground=CYAN, rowheight=22, font=FONT, borderwidth=0)
        st.configure("Treeview.Heading", background="#10243d", foreground=BLUE,
                     font=FONT_B, relief="flat")
        st.map("Treeview", background=[("selected", "#16406b")])
        st.configure("Cyber.Horizontal.TProgressbar", troughcolor=PANEL,
                     background=CYAN, bordercolor=PANEL, lightcolor=CYAN,
                     darkcolor=CYAN)
        st.configure("Cyber.TButton", background="#10243d", foreground=CYAN,
                     font=FONT_B, borderwidth=1, padding=4)
        st.map("Cyber.TButton", background=[("active", "#16406b")])
        st.configure("Stop.TButton", background="#3a1620", foreground=RED,
                     font=FONT_B, padding=4)
        st.map("Stop.TButton", background=[("active", "#5a1f2d")])

    def _build_ui(self):
        # --- nagłówek
        header = tk.Frame(self, bg=PANEL, highlightbackground=CYAN, highlightthickness=1)
        header.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(header, text="NETWORK // CYBER ANALYTIC TERMINAL", bg=PANEL,
                 fg=BLUE, font=("Consolas", 14, "bold")).pack(side="left", padx=10, pady=6)
        self.clock = tk.Label(header, text="", bg=PANEL, fg=DIM, font=FONT)
        self.clock.pack(side="right", padx=10)
        tk.Label(header, text="CONSOLE DIAGNOSTIC TOOL  📶 ⚡ LAN 100%", bg=PANEL,
                 fg=DIM, font=FONT).pack(side="right", padx=10)
        self._tick_clock()

        # --- dashboard
        dash = tk.Frame(self, bg=BG)
        dash.pack(fill="x", padx=8, pady=4)
        dash.columnconfigure(0, weight=3)
        dash.columnconfigure(1, weight=2)

        wf = tk.LabelFrame(dash, text=" Wi-Fi Signal Strength ", bg=BG, fg=CYAN, font=FONT_B)
        wf.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        cols = ("ssid", "signal", "dbm", "sec", "status")
        self.wifi_tree = ttk.Treeview(wf, columns=cols, show="headings", height=5)
        for c, t, w in zip(cols, ("SSID", "Signal", "dBm", "Security", "Status"),
                           (110, 80, 50, 90, 60)):
            self.wifi_tree.heading(c, text=t)
            self.wifi_tree.column(c, width=w, anchor="center")
        self.wifi_tree.pack(fill="both", expand=True, padx=4, pady=4)
        for row in [("papke1", "[||||]", -17, "CPSN", "Conn"),
                    ("papke2", "[||| ]", -26, "WPA2-Ent", "Diag"),
                    ("papke3", "[||  ]", -23, "WPA2-Ent", "Norm"),
                    ("ü3unccoh", "[|   ]", -29, "WPA2-Ent", "Syst"),
                    ("p3pne5", "[|   ]", -15, "VCrkdard", "Enst")]:
            self.wifi_tree.insert("", "end", values=row)

        nf = tk.LabelFrame(dash, text=" Network Status ", bg=BG, fg=CYAN, font=FONT_B)
        nf.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.net_tree = ttk.Treeview(nf, columns=("m", "v"), show="headings", height=5)
        self.net_tree.heading("m", text="Metric")
        self.net_tree.heading("v", text="Current Value")
        self.net_tree.column("m", width=120)
        self.net_tree.column("v", width=200)
        self.net_tree.pack(fill="both", expand=True, padx=4, pady=4)
        self.refresh_dashboard()

        # --- pasek postępu
        pf = tk.Frame(self, bg=BG)
        pf.pack(fill="x", padx=8, pady=2)
        self.progress_label = tk.Label(pf, text="SYSTEM SCAN IN PROGRESS...", bg=BG,
                                       fg=CYAN, font=FONT)
        self.progress_label.pack(side="left")
        self.progress = ttk.Progressbar(pf, style="Cyber.Horizontal.TProgressbar",
                                        maximum=100, length=300)
        self.progress.pack(side="left", fill="x", expand=True, padx=8)

        # --- przyciski szybkich komend
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=8, pady=4)
        for name in ("wifi_scan", "ping", "traceroute", "systeminfo", "netstat", "upnp", "ls"):
            ttk.Button(bf, text=name, style="Cyber.TButton",
                       command=lambda n=name: self.quick(n)).pack(side="left", padx=2)
        ttk.Button(bf, text="clear", style="Cyber.TButton",
                   command=self.clear_console).pack(side="left", padx=2)
        ttk.Button(bf, text="■ STOP", style="Stop.TButton",
                   command=self.stop_proc).pack(side="right", padx=2)

        # --- konsola + logi
        mid = tk.PanedWindow(self, orient="horizontal", bg=BG, sashwidth=4, bd=0)
        mid.pack(fill="both", expand=True, padx=8, pady=4)

        cf = tk.LabelFrame(mid, text=" Console ", bg=BG, fg=CYAN, font=FONT_B)
        self.console = tk.Text(cf, bg=PANEL, fg=GREEN, font=FONT, wrap="word",
                               insertbackground=GREEN, relief="flat", state="disabled")
        sb = ttk.Scrollbar(cf, command=self.console.yview)
        self.console.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.console.pack(fill="both", expand=True, padx=4, pady=4)
        mid.add(cf, stretch="always", minsize=400)

        lf = tk.LabelFrame(mid, text=" P3PE_LOG (Real-time Stream) | Status: Active ",
                           bg=BG, fg=BLUE, font=FONT_B)
        self.log = tk.Text(lf, bg=PANEL, fg=DIM, font=("Consolas", 9), wrap="word",
                           width=38, relief="flat", state="disabled")
        self.log.pack(fill="both", expand=True, padx=4, pady=4)
        mid.add(lf, minsize=250)

        for w in (self.console, self.log):
            w.tag_config("ok", foreground=GREEN)
            w.tag_config("info", foreground=CYAN)
            w.tag_config("err", foreground=RED)
            w.tag_config("warn", foreground=YELLOW)
            w.tag_config("mag", foreground=MAGENTA)
            w.tag_config("dim", foreground=DIM)
            w.tag_config("cmd", foreground=CYAN, font=FONT_B)

        # --- wiersz wprowadzania
        ef = tk.Frame(self, bg=BG)
        ef.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(ef, text="> scan network_", bg=BG, fg=GREEN, font=FONT_B).pack(side="left")
        self.entry = tk.Entry(ef, bg=PANEL, fg=GREEN, insertbackground=GREEN,
                              font=FONT, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, padx=6, ipady=4)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<Up>", self.hist_up)
        self.entry.bind("<Down>", self.hist_down)
        self.entry.focus_set()

        self.out("[+] Terminal gotowy do pracy. Wpisz 'help', aby zobaczyć komendy.", "ok")

    def _tick_clock(self):
        self.clock.config(text="🕒 " + datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._tick_clock)

    def _startup_scan(self):
        self._prog = 0
        self.log_line("[P3PE] Diagnostic activity started", "dim")

        def step():
            self._prog += 3
            self.progress["value"] = min(self._prog, 100)
            if self._prog < 100:
                self.after(30, step)
            else:
                self.progress_label.config(text="SYSTEM SCAN COMPLETE")
                self.log_line("[P3PE] System Scanning... done", "ok")
        step()

    def refresh_dashboard(self):
        for i in self.net_tree.get_children():
            self.net_tree.delete(i)
        ip = local_ip()
        rows = [("Connection Type", "LAN"),
                ("Host", socket.gethostname()),
                ("IP Address", ip),
                ("OS", f"{platform.system()} {platform.release()}"),
                ("Link Speed", "1000 Mbps")]
        for r in rows:
            self.net_tree.insert("", "end", values=r)

    # ------------------------------------------------ wyjście (bezpieczne wątkowo)
    def out(self, text, tag="ok"):
        self.q.put(("console", text, tag))

    def log_line(self, text, tag="dim"):
        self.q.put(("log", text, tag))

    def _poll_queue(self):
        try:
            while True:
                target, text, tag = self.q.get_nowait()
                w = self.console if target == "console" else self.log
                w.config(state="normal")
                if target == "log":
                    text = f"[{datetime.now():%H:%M:%S}] {text}"
                w.insert("end", text + "\n", tag)
                w.see("end")
                w.config(state="disabled")
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)

    def clear_console(self):
        self.console.config(state="normal")
        self.console.delete("1.0", "end")
        self.console.config(state="disabled")

    # ------------------------------------------------ wejście
    def quick(self, name):
        if name in ("ping", "traceroute"):
            host = simpledialog.askstring(name, "Host:", initialvalue="8.8.8.8", parent=self)
            if not host:
                return
            self.execute(f"{name} {host}")
        else:
            self.execute(name)

    def on_enter(self, _e=None):
        line = self.entry.get()
        self.entry.delete(0, "end")
        if line.strip():
            self.execute(line)

    def hist_up(self, _e):
        if self.history and self.hist_idx > 0:
            self.hist_idx -= 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.history[self.hist_idx])

    def hist_down(self, _e):
        self.entry.delete(0, "end")
        if self.hist_idx < len(self.history) - 1:
            self.hist_idx += 1
            self.entry.insert(0, self.history[self.hist_idx])
        else:
            self.hist_idx = len(self.history)

    def execute(self, line):
        self.history.append(line)
        self.hist_idx = len(self.history)
        self.out(f"> scan network_ {line}", "cmd")
        try:
            args = shlex.split(line)
        except ValueError as e:
            self.out(f"[-] Błąd składni: {e}", "err")
            return
        cmd, params = args[0].lower(), args[1:]
        try:
            if cmd == "exit":
                self.destroy()
            elif cmd == "clear":
                self.clear_console()
            elif cmd == "dashboard":
                self.refresh_dashboard()
                self.out("[+] Dashboard odświeżony.", "info")
            elif cmd in self.fs_commands:
                self.fs_commands[cmd](*params)
            elif cmd in self.net_commands:
                self.log_line(f"Running: {cmd}", "info")
                self.net_commands[cmd](*params)
            elif cmd == "help":
                self.out("Dostępne komendy FS: " + ", ".join(self.fs_commands), "info")
                self.out("Dostępne komendy sieciowe: " + ", ".join(self.net_commands), "info")
                self.out("Inne: dashboard, clear, help, exit", "info")
            else:
                self.out(f"Nieznana komenda: {cmd}. Wpisz 'help'.", "warn")
        except TypeError:
            self.out(f"[-] Zła liczba argumentów dla '{cmd}'.", "err")
        except Exception as e:
            self.out(f"[-] Błąd: {e}", "err")

    # ------------------------------------------------ FS
    def mkfolder(self, name):
        try:
            os.makedirs(sandbox_path(name), exist_ok=True)
            self.out(f"[+] Folder utworzony: {name}", "info")
        except Exception as e:
            self.out(f"[-] Błąd mkfolder: {e}", "err")

    def ls(self, arg=""):
        try:
            path = sandbox_path(arg)
            if not os.path.exists(path):
                self.out(f"[-] Nie istnieje: {arg}", "warn")
                return
            items = sorted(os.listdir(path))
            if not items:
                self.out("(pusto)", "dim")
            for item in items:
                if os.path.isdir(os.path.join(path, item)):
                    self.out(f"[DIR] {item}", "dim")
                else:
                    self.out(f"      {item}", "ok")
        except Exception as e:
            self.out(f"[-] Błąd ls: {e}", "err")

    def touch(self, filename):
        try:
            path = sandbox_path(filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            Path(path).touch()
            self.out(f"[+] Plik utworzony: {filename}", "info")
        except Exception as e:
            self.out(f"[-] Błąd touch: {e}", "err")

    def write_file(self, filename, *content_parts):
        try:
            path = sandbox_path(filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(" ".join(content_parts))
            self.out(f"[+] Zapisano do {filename}", "info")
        except Exception as e:
            self.out(f"[-] Błąd write: {e}", "err")

    def read_file(self, filename):
        try:
            path = sandbox_path(filename)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    self.out(f.read(), "ok")
            else:
                self.out(f"[-] Nie istnieje plik: {filename}", "warn")
        except Exception as e:
            self.out(f"[-] Błąd read: {e}", "err")

    def rm(self, target):
        try:
            path = sandbox_path(target)
            if os.path.isfile(path):
                os.remove(path)
                self.out(f"[+] Plik usunięty: {target}", "info")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                self.out(f"[+] Folder usunięty: {target}", "info")
            else:
                self.out(f"[-] Nie istnieje: {target}", "warn")
        except Exception as e:
            self.out(f"[-] Błąd rm: {e}", "err")

    # ------------------------------------------------ SIEĆ
    def run_external(self, cmd, label=None):
        """Uruchamia polecenie w tle i strumieniuje wynik do konsoli."""
        if self.proc and self.proc.poll() is None:
            self.out("[!] Inne polecenie jeszcze działa. Użyj STOP.", "warn")
            return

        def worker():
            try:
                flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                self.proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    encoding=console_encoding(), errors="replace",
                    creationflags=flags)
                for line in self.proc.stdout:
                    self.out(line.rstrip("\n"), "ok")
                self.proc.wait()
                self.log_line(f"{label or cmd[0]} zakończone (kod {self.proc.returncode})", "dim")
            except FileNotFoundError:
                self.out(f"[-] Nie znaleziono programu: {cmd[0]}", "err")
            except Exception as e:
                self.out(f"[-] Błąd: {e}", "err")
        threading.Thread(target=worker, daemon=True).start()

    def stop_proc(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.out("[*] Przerwano proces.", "warn")
        else:
            self.out("[*] Brak działającego procesu.", "dim")

    def wifi_scan(self):
        self.out("[*] Skanowanie sieci Wi-Fi...", "mag")
        if platform.system() == "Windows":
            self.run_external(["netsh", "wlan", "show", "networks", "mode=Bssid"])
        else:
            self.run_external(["nmcli", "dev", "wifi"])

    def ping(self, host="8.8.8.8"):
        param = "-n" if platform.system() == "Windows" else "-c"
        self.run_external(["ping", param, "4", host])

    def traceroute(self, host="8.8.8.8"):
        cmd = ["tracert", host] if platform.system() == "Windows" else ["traceroute", host]
        self.run_external(cmd)

    def netstat(self):
        self.out("[*] Wyświetlanie aktywnych połączeń...", "mag")
        cmd = ["netstat", "-ano"] if platform.system() == "Windows" else ["ss", "-tulnp"]
        self.run_external(cmd)

    def system_info(self):
        self.out(f"[Host] {socket.gethostname()} | [IP] {local_ip()} | "
                 f"[OS] {platform.system()} {platform.release()}", "info")

    def run_python_script(self, *args):
        if not args:
            self.out("[USAGE] nmap_scan <skrypt.py> [args...]", "warn")
            return
        script, rest = args[0], list(args[1:])
        try:
            sp = sandbox_path(script)
            resolved = sp if os.path.exists(sp) else script
        except ValueError:
            resolved = script
        self.out(f"[*] Uruchamianie skryptu: {script}...", "mag")
        self.run_external([sys.executable, resolved] + rest, label=script)

    def ssdp_discover(self):
        self.out("[*] Skanowanie UPnP/SSDP...", "mag")

        def worker():
            try:
                msearch = ('M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n'
                           'MAN: "ssdp:discover"\r\nMX: 2\r\nST: upnp:rootdevice\r\n\r\n'
                           ).encode()
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                s.settimeout(3)
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                s.sendto(msearch, ("239.255.255.250", 1900))
                found = {}
                while True:
                    try:
                        data, addr = s.recvfrom(65535)
                        lines = data.decode("utf-8", errors="ignore").split("\r\n")
                        loc = next((l for l in lines if l.lower().startswith("location:")),
                                   "Location: Brak")
                        found[addr[0]] = loc
                    except socket.timeout:
                        break
                s.close()
                if not found:
                    self.out("[-] Nie wykryto urządzeń UPnP w sieci.", "warn")
                    return
                self.out(f"{'IP ADRES':<16} | USŁUGA / NAGŁÓWEK", "info")
                self.out("-" * 60, "dim")
                for ip, loc in found.items():
                    self.out(f"{ip:<16} | {loc}", "ok")
            except Exception as e:
                self.out(f"[-] Błąd skanowania UPnP: {e}", "err")
        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()