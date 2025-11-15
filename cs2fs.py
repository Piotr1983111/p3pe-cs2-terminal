#!/usr/bin/env python3
# cs2_file_terminal.py
# CS2-style terminal with sandbox FS, Wi-Fi scanner, network tools
import sys
import os
import shlex
import shutil
import zipfile
import time
import subprocess
from pathlib import Path
import platform
import socket
import re

# ----------------  biblioteki ----------------
try:
    from colorama import init as colorama_init, Fore, Style, Back
    colorama_init()
except Exception:
    class _F:
        GREEN = CYAN = YELLOW = RED = MAGENTA = RESET = ""
    class _S:
        RESET_ALL = DIM = ""
    class _B:
        YELLOW = ""
    Fore = _F()
    Style = _S()
    Back = _B()

# ---------------- UI / banner ----------------
PROMPT_BASE = "cs2> "
BANNER_TEXT = r"""
██████╗ ███████╗██████╗ ███████╗
██╔══██╗██╔════╝██╔══██╗██╔════╝
██████╔╝█████╗  ██████╔╝█████╗  
██╔═══╝ ██╔══╝  ██╔═══╝ ██╔══╝  
██║     ███████╗██║     ███████╗
╚═╝     ╚══════╝╚═╝     ╚══════╝
            Pepe
"""
HISTORY_FILE = str(Path.home() / ".cs2_terminal_history")

def run_python_script(script_path=None, *args, background=False, default_path=None):
    """
    Uruchamia skrypt Python.
    - script_path: ścieżka do pliku .py (absolutna lub relatywna). Jeśli None -> wyświetla help
    - args: dodatkowe argumenty przekazywane do skryptu
    - background: True -> uruchom w tle (non-blocking)
    - default_path: opcjonalna ścieżka domyślna (jeśli script_path jest None)
    """
    # jeśli nie podano ścieżki, spróbuj default_path lub pokaż pomoc
    if not script_path:
        if default_path and os.path.exists(default_path):
            script_path = default_path
            print(Fore.YELLOW + "[*] Brak argumentu, używam domyślnego skryptu:" + Style.RESET_ALL, script_path)
        else:
            print(Fore.YELLOW + "[USAGE] nmap_scan <ścieżka_do_skryptu.py> [args...]")
            print(Fore.YELLOW + "        albo: nmap_scan --default (jeśli masz skonfigurowany default)" + Style.RESET_ALL)
            return

    # mapowanie relatywnych ścieżek względem sandboxu (jeśli plik tam występuje)
    try:
        if not os.path.isabs(script_path):
            try:
                candidate = _sandbox_path(script_path)
                if os.path.exists(candidate):
                    script_path = candidate
                else:
                    # spróbuj relatywnej ścieżki względem cwd
                    script_path = os.path.normpath(os.path.join(os.getcwd(), script_path))
            except Exception:
                script_path = os.path.normpath(os.path.join(os.getcwd(), script_path))
    except Exception:
        pass

    if not os.path.exists(script_path):
        print(Fore.RED + "[ERROR] Nie znaleziono pliku:" + Style.RESET_ALL, script_path)
        return

    if not script_path.lower().endswith(".py"):
        print(Fore.YELLOW + "[WARN] Plik nie wygląda na .py, mimo to spróbuję uruchomić." + Style.RESET_ALL)

    cmd = [sys.executable, script_path] + list(args)

    try:
        if background:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(Fore.CYAN + "[*] Skrypt uruchomiony w tle:" + Style.RESET_ALL, script_path)
        else:
            proc = subprocess.run(cmd)
            print(Fore.CYAN + "[*] Skrypt zakończył się z kodem:" + Style.RESET_ALL, proc.returncode)
    except Exception as e:
        print(Fore.RED + "[-] Błąd uruchamiania skryptu:" + Style.RESET_ALL, e)


    if not script_path.lower().endswith(".py"):
        print(Fore.YELLOW + "[WARN] Plik nie wygląda na .py, mimo to spróbuję uruchomić." + Style.RESET_ALL)

    cmd = [sys.executable, script_path] + list(args)

    try:
        if background:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(Fore.CYAN + "[*] Skrypt uruchomiony w tle:" + Style.RESET_ALL, script_path)
        else:
            proc = subprocess.run(cmd)
            print(Fore.CYAN + "[*] Skrypt zakończył się z kodem:" + Style.RESET_ALL, proc.returncode)
    except Exception as e:
        print(Fore.RED + "[-] Błąd uruchamiania skryptu:" + Style.RESET_ALL, e)

def set_console_style():
    try:
        if os.name == "nt":
            os.system("title CS2 Terminal")
            os.system("color 0A")
    except Exception:
        pass

def build_prompt():
    cwd = Path.cwd()
    parts = cwd.parts[-2:] if len(cwd.parts) >= 2 else cwd.parts
    short = "\\".join(parts) if parts else str(cwd)
    return (Fore.GREEN + PROMPT_BASE + Style.DIM + short + Style.RESET_ALL + " ") if Fore else (PROMPT_BASE + short + " ")

# ---------------- SANDBOX FS ----------------
SANDBOX_ROOT = os.path.join(os.getcwd(), ".terminal_fs")
os.makedirs(SANDBOX_ROOT, exist_ok=True)

def _sandbox_path(path):
    if not path:
        return SANDBOX_ROOT
    p = path
    if os.path.isabs(p):
        p = p.lstrip("/\\")
    candidate = os.path.normpath(os.path.join(SANDBOX_ROOT, p))
    sandbox_real = os.path.realpath(SANDBOX_ROOT)
    cand_real = os.path.realpath(candidate)
    if not cand_real.startswith(sandbox_real):
        raise ValueError("Ścieżka poza sandboxem niedozwolona.")
    return candidate

def mkfolder(name):
    try:
        path = _sandbox_path(name)
        os.makedirs(path, exist_ok=True)
        print(Fore.CYAN + f"[+] Folder utworzony: {name}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd mkfolder:" + Style.RESET_ALL, e)

def rm(target):
    try:
        path = _sandbox_path(target)
        if os.path.isfile(path):
            os.remove(path)
            print(Fore.CYAN + f"[+] Plik usunięty: {target}" + Style.RESET_ALL)
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(Fore.CYAN + f"[+] Folder usunięty: {target}" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"[-] Nie istnieje: {target}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd rm:" + Style.RESET_ALL, e)

def rename(src, dst):
    try:
        src_path = _sandbox_path(src)
        dst_path = _sandbox_path(dst)
        if os.path.exists(src_path):
            os.rename(src_path, dst_path)
            print(Fore.CYAN + f"[+] {src} → {dst}" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"[-] Nie istnieje: {src}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd rename:" + Style.RESET_ALL, e)

def move(src, dst):
    try:
        src_path = _sandbox_path(src)
        dst_path = _sandbox_path(dst)
        if os.path.exists(src_path):
            shutil.move(src_path, dst_path)
            print(Fore.CYAN + f"[+] Przeniesiono: {src} → {dst}" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"[-] Nie istnieje: {src}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd move:" + Style.RESET_ALL, e)

def ls(arg=""):
    try:
        path = _sandbox_path(arg)
        if os.path.exists(path):
            items = sorted(os.listdir(path))
            for item in items:
                full = os.path.join(path, item)
                if os.path.isdir(full):
                    print(Style.DIM + Fore.GREEN + f"[DIR] {item}" + Style.RESET_ALL)
                else:
                    print(Fore.GREEN + f"      {item}" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"[-] Nie istnieje: {arg}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd ls:" + Style.RESET_ALL, e)

def touch(filename):
    try:
        path = _sandbox_path(filename)
        parent = os.path.dirname(path)
        os.makedirs(parent, exist_ok=True)
        with open(path, "a", encoding="utf-8"):
            pass
        print(Fore.CYAN + f"[+] Plik utworzony: {filename}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd touch:" + Style.RESET_ALL, e)

def write_file(filename, *content_parts):
    try:
        content = " ".join(content_parts) if content_parts else ""
        path = _sandbox_path(filename)
        parent = os.path.dirname(path)
        os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(Fore.CYAN + f"[+] Zapisano do {filename}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd write:" + Style.RESET_ALL, e)

def read_file(filename):
    try:
        path = _sandbox_path(filename)
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print(Fore.YELLOW + f"[-] Nie istnieje plik: {filename}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd read:" + Style.RESET_ALL, e)

def zip_folder(src, out_zip):
    try:
        src_path = _sandbox_path(src)
        out_path = _sandbox_path(out_zip)
        if os.path.exists(src_path) and os.path.isdir(src_path):
            base = out_path
            if base.lower().endswith(".zip"):
                base = base[:-4]
            shutil.make_archive(base, 'zip', src_path)
            print(Fore.CYAN + f"[+] Folder {src} spakowany do {out_zip}" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"[-] Nie istnieje folder: {src}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd zip:" + Style.RESET_ALL, e)

def unzip_archive(zipfile_name, out_dir=""):
    try:
        zip_path = _sandbox_path(zipfile_name)
        out_path = _sandbox_path(out_dir) if out_dir else SANDBOX_ROOT
        if os.path.exists(zip_path) and zipfile.is_zipfile(zip_path):
            with zipfile.ZipFile(zip_path, "r") as z:
                for member in z.namelist():
                    member_path = (Path(out_path) / Path(member)).resolve()
                    if not str(member_path).startswith(str(Path(out_path).resolve())):
                        print(Fore.YELLOW + f"[-] Pominięto podejrzany wpis w archiwum: {member}" + Style.RESET_ALL)
                        continue
                    z.extract(member, out_path)
            print(Fore.CYAN + f"[+] Rozpakowano {zipfile_name} do {out_dir or 'sandbox root'}" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"[-] Nieprawidłowy plik zip: {zipfile_name}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd unzip:" + Style.RESET_ALL, e)

fs_commands = {
    
    "mkfolder": mkfolder,
    "rm": rm,
    "rename": rename,
    "move": move,
    "ls": ls,
    "touch": touch,
    "write": write_file,
    "read": read_file,
    "zip": zip_folder,
    "unzip": unzip_archive,
}

# ---------------- Wi-Fi / Network Tools ----------------
# ---------------- ROZSZERZONE NARZĘDZIA Wi-Fi ----------------

def wifi_interfaces():
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_interfaces:" + Style.RESET_ALL, e)

def wifi_status():
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_status:" + Style.RESET_ALL, e)

def wifi_profiles():
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "profiles"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_profiles:" + Style.RESET_ALL, e)

def wifi_profile_info(name):
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "profile", name], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_profile_info:" + Style.RESET_ALL, e)

def wifi_strength():
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_strength:" + Style.RESET_ALL, e)

def wifi_channels():
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=Bssid"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_channels:" + Style.RESET_ALL, e)

def wifi_bssid():
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_bssid:" + Style.RESET_ALL, e)

def wifi_disconnect():
    try:
        out = subprocess.check_output(["netsh", "wlan", "disconnect"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_disconnect:" + Style.RESET_ALL, e)

def wifi_reconnect(name):
    try:
        out = subprocess.check_output(["netsh", "wlan", "connect", f"name={name}"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_reconnect:" + Style.RESET_ALL, e)

def wifi_driver():
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "drivers"], encoding="utf-8")
        print(out)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_driver:" + Style.RESET_ALL, e)


def wifi_scan():
    print(Fore.MAGENTA + "[*] Skanowanie sieci Wi-Fi..." + Style.RESET_ALL)
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=Bssid"], encoding='utf-8')
            print(result)
        elif system == "Linux":
            result = subprocess.check_output(["nmcli", "dev", "wifi"], encoding='utf-8')
            print(result)
        elif system == "Darwin":
            result = subprocess.check_output(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"], encoding='utf-8')
            print(result)
        else:
            print(Fore.YELLOW + "[-] System nieobsługiwany." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd wifi_scan:" + Style.RESET_ALL, e)

def ping(host):
    try:
        param = "-n" if platform.system() == "Windows" else "-c"
        subprocess.call(["ping", param, "4", host])
    except Exception as e:
        print(Fore.RED + "[-] Błąd ping:" + Style.RESET_ALL, e)

def traceroute(host):
    try:
        cmd = ["tracert", host] if platform.system() == "Windows" else ["traceroute", host]
        subprocess.call(cmd)
    except Exception as e:
        print(Fore.RED + "[-] Błąd traceroute:" + Style.RESET_ALL, e)

# ---------------- PODŚWIETLONA ZMIANA: Rozszerzony netstat ----------------
try:
    import psutil
    PSUTIL_AVAILABLE = True
except Exception:
    PSUTIL_AVAILABLE = False

def netstat_enriched(limit=300):
    """<-- ZMIANA: rozbudowany netstat z PID, nazwa procesu, właściciel, host zdalny -->
    """
    system = platform.system()
    lines = []
    try:
        if system == "Windows":
            proc = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=False)
            lines = proc.stdout.splitlines()
        else:
            try:
                proc = subprocess.run(["ss", "-tunap"], capture_output=True, text=True, check=False)
                lines = proc.stdout.splitlines()
                if not lines:
                    raise Exception("empty ss")
            except Exception:
                proc = subprocess.run(["netstat", "-tunap"], capture_output=True, text=True, check=False)
                lines = proc.stdout.splitlines()
    except Exception as e:
        print(Fore.RED + "[-] Błąd uruchamiania netstat/ss:" + Style.RESET_ALL, e)
        return

    # ... parsowanie podobnie jak w poprzedniej instrukcji
    # dla uproszczenia tutaj wypiszę tylko surową listę linii
    for l in lines[:limit]:
        print(l)


def run_python_script(script_path=None, *args, background=False, default_path=None):
    """
    Uruchamia skrypt Python.
    - script_path: ścieżka do pliku .py (absolutna lub relatywna). Jeśli None -> wyświetla help
    - args: dodatkowe argumenty przekazywane do skryptu
    - background: True -> uruchom w tle (non-blocking)
    - default_path: opcjonalna ścieżka domyślna (jeśli script_path jest None)
    """
    # jeśli nie podano ścieżki, spróbuj default_path lub pokaż pomoc
    if not script_path:
        if default_path and os.path.exists(default_path):
            script_path = default_path
            print(Fore.YELLOW + "[*] Brak argumentu, używam domyślnego skryptu:" + Style.RESET_ALL, script_path)
        else:
            print(Fore.YELLOW + "[USAGE] run_py <ścieżka_do_skryptu.py> [args...]") 
            print(Fore.YELLOW + "        albo: run_py --default (jeśli masz skonfigurowany default)" + Style.RESET_ALL)
            return

    # mapowanie relatywnych ścieżek względem sandboxu (jeśli plik tam występuje)
    try:
        if not os.path.isabs(script_path):
            try:
                candidate = _sandbox_path(script_path)
                if os.path.exists(candidate):
                    script_path = candidate
                else:
                    # spróbuj relatywnej ścieżki względem cwd
                    script_path = os.path.normpath(os.path.join(os.getcwd(), script_path))
            except Exception:
                script_path = os.path.normpath(os.path.join(os.getcwd(), script_path))
    except Exception:
        pass

    if not os.path.exists(script_path):
        print(Fore.RED + "[ERROR] Nie znaleziono pliku:" + Style.RESET_ALL, script_path)
        return

    if not script_path.lower().endswith(".py"):
        print(Fore.YELLOW + "[WARN] Plik nie wygląda na .py, mimo to spróbuję uruchomić." + Style.RESET_ALL)

    cmd = [sys.executable, script_path] + list(args)

    try:
        if background:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(Fore.CYAN + "[*] Skrypt uruchomiony w tle:" + Style.RESET_ALL, script_path)
        else:
            proc = subprocess.run(cmd)
            print(Fore.CYAN + "[*] Skrypt zakończył się z kodem:" + Style.RESET_ALL, proc.returncode)
    except Exception as e:
        print(Fore.RED + "[-] Błąd uruchamiania skryptu:" + Style.RESET_ALL, e)

def system_info():
    """
    Wyświetla zbiorcze informacje o systemie.
    Best-effort: używa psutil jeśli jest zainstalowany, inaczej fallbacków z stdlib i poleceń systemowych.
    """
    import platform, socket, os, time, shutil, subprocess

    # try psutil for nicer values (optional)
    try:
        import psutil
    except Exception:
        psutil = None

    def get_local_ip():
        # metoda bez łączenia — otwiera UDP socket do publicznego IP by poznać lokalne IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # fallback
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "unknown"

    info = {}
    info["Hostname"] = socket.gethostname()
    info["FQDN"] = socket.getfqdn()
    info["Local IP"] = get_local_ip()
    info["OS"] = f"{platform.system()} {platform.release()} ({platform.version()})"
    info["Platform"] = platform.platform()
    info["Arch"] = platform.machine()
    info["Python"] = platform.python_version()
    info["CPU count"] = os.cpu_count() or "unknown"

    # Uptime
    try:
        if psutil:
            boot_ts = psutil.boot_time()
            uptime_s = int(time.time() - boot_ts)
        else:
            if platform.system() == "Linux":
                with open("/proc/uptime", "r") as f:
                    uptime_s = int(float(f.readline().split()[0]))
            elif platform.system() == "Windows":
                # try wmic
                out = subprocess.check_output(["wmic", "os", "get", "LastBootUpTime"], text=True, errors="ignore")
                # parse YYYYMMDDHHMMSS...
                m = None
                for line in out.splitlines():
                    if line.strip() and not line.lower().startswith("lastbootuptime"):
                        m = line.strip()
                        break
                if m:
                    # convert to timestamp roughly
                    try:
                        # take yyyy mm dd hh mm ss
                        yyyy = int(m[0:4]); mm = int(m[4:6]); dd = int(m[6:8])
                        hh = int(m[8:10]); minu = int(m[10:12]); ss = int(m[12:14])
                        boot_ts = time.mktime((yyyy, mm, dd, hh, minu, ss, 0, 0, -1))
                        uptime_s = int(time.time() - boot_ts)
                    except Exception:
                        uptime_s = None
                else:
                    uptime_s = None
            else:
                uptime_s = None
    except Exception:
        uptime_s = None

    def human_time(s):
        if not s:
            return "unknown"
        m, sec = divmod(s, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        parts = []
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        parts.append(f"{sec}s")
        return " ".join(parts)

    info["Uptime"] = human_time(uptime_s)

    # Memory & disk via psutil or shutil
    if psutil:
        try:
            vm = psutil.virtual_memory()
            info["Memory total"] = f"{int(vm.total/1024/1024)} MB"
            info["Memory available"] = f"{int(vm.available/1024/1024)} MB"
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            info["Disk total"] = f"{int(disk.total/1024/1024/1024)} GB"
            info["Disk free"] = f"{int(disk.free/1024/1024/1024)} GB"
        except Exception:
            pass
    else:
        try:
            du = shutil.disk_usage(os.path.abspath(os.sep))
            info["Disk total"] = f"{int(du.total/1024/1024/1024)} GB"
            info["Disk free"] = f"{int(du.free/1024/1024/1024)} GB"
        except Exception:
            pass

    # Optional: small network summary (Windows: ipconfig / Linux: ip addr show)
    net_summary = []
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output(["ipconfig"], text=True, errors="ignore")
            # take lines with IPv4 Address or IPv6
            for line in out.splitlines():
                if "IPv4 Address" in line or "IPv6 Address" in line or "Adres IPv4" in line:
                    net_summary.append(line.strip())
        else:
            out = subprocess.check_output(["ip", "addr", "show"], text=True, errors="ignore")
            # take lines with inet (IPv4) from ip addr
            for line in out.splitlines():
                if "inet " in line and "127.0.0.1" not in line:
                    net_summary.append(line.strip())
    except Exception:
        # fallback minimal
        try:
            net_summary.append("Interfaces: " + ", ".join(os.listdir("/sys/class/net")))  # linux-only fallback
        except Exception:
            pass

    # Print nicely
    print(Fore.CYAN + "\n=== System Information ===" + Style.RESET_ALL)
    for k, v in info.items():
        print(Fore.GREEN + f"{k:18}" + Style.RESET_ALL + " : ", v)
    if net_summary:
        print(Fore.CYAN + "\n--- Network (summary) ---" + Style.RESET_ALL)
        for l in net_summary[:8]:
            print(" ", l)
    print()  # newline

def print_table(rows, headers):
    # wypisz nagłówki
    print(" | ".join(headers))
    print("-" * (len(headers) * 20))
    for row in rows:
        print(" | ".join(str(row.get(h,"")) for h in headers))

# ---------------- UPNP / SSDP ----------------
def cmd_upnp_scan():
    ...
    print_table(rows, headers)
# ----------------- NEW COMMAND: upnp.scan -----------------
def cmd_upnp_scan():
    """
    upnp.scan - attempt PowerShell Get-SsdpDevice first (Windows).
               If not available -> SSDP M-SEARCH fallback via Python UDP.
    """
    print(Fore.MAGENTA + "[*] Skanowanie UPnP/SSDP..." + Style.RESET_ALL)
    
    # Spróbuj PowerShell (Windows)
    ps_cmd = (
        "Get-SsdpDevice -ErrorAction SilentlyContinue | "
        "Select-Object DeviceType,Location,FriendlyName,Server,USN | ConvertTo-Json"
    )
    data, err = powershell_json(ps_cmd)
    rows = []

    if data is not None:
        items = data if isinstance(data, list) else [data]
        for it in items:
            rows.append({
                "FriendlyName": it.get("FriendlyName",""),
                "DeviceType": it.get("DeviceType",""),
                "Location": it.get("Location",""),
                "Server": it.get("Server",""),
                "USN": it.get("USN","")
            })
        headers = ["FriendlyName","DeviceType","Location","Server","USN"]
        print_table(rows, headers)
        return

    # Fallback SSDP przez UDP (cross-platform)
    print(Fore.YELLOW + "[*] PowerShell Get-SsdpDevice niedostępne — używam SSDP M-SEARCH (fallback)." + Style.RESET_ALL)
    try:
        responses = ssdp_discover(timeout=2.0, mx=1, st="ssdp:all")
        for r in responses:
            rows.append({
                "ST": r.get("ST",""),
                "USN": r.get("USN",""),
                "LOCATION": r.get("LOCATION",""),
                "SERVER": r.get("SERVER",""),
                "FROM": r.get("_from","")
            })
        if rows:
            headers = ["ST","USN","LOCATION","SERVER","FROM"]
            print_table(rows, headers)
        else:
            print(Fore.YELLOW + "[*] Brak odpowiedzi SSDP." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[-] Błąd podczas SSDP discovery:" + Style.RESET_ALL, e)
def powershell_json(command: str):
    """
    Uruchamia PowerShell i parsuje wynik do JSON.
    Działa tylko na Windows.
    """
    import subprocess, json, platform

    if platform.system() != "Windows":
        return None, "PowerShell JSON helper only available on Windows."
    try:
        full_cmd = ["powershell", "-NoProfile", "-Command", command]
        proc = subprocess.run(full_cmd, capture_output=True, text=True, timeout=10)
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if proc.returncode != 0:
            return None, f"PowerShell returned rc={proc.returncode}: {err}"
        if not out:
            return None, "PowerShell returned empty output."
        try:
            parsed = json.loads(out)
            return parsed, None
        except Exception:
            return None, f"JSON parse error; raw output: {out[:400]}"
    except Exception as e:
        return None, f"PowerShell error: {e}"


def ssdp_discover(timeout=2.0, mx=1, st="ssdp:all"):
    """
    Wysyła zapytanie SSDP M-SEARCH i zbiera odpowiedzi.
    Zwraca listę słowników z nagłówkami urządzeń.
    """
    MCAST_GRP = ("239.255.255.250", 1900)
    message = "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        f'HOST: {MCAST_GRP[0]}:{MCAST_GRP[1]}',
        'MAN: "ssdp:discover"',
        f'MX: {mx}',
        f'ST: {st}',
        '', ''
    ]).encode("utf-8")

    results = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(timeout)
    try:
        sock.sendto(message, MCAST_GRP)
        start = time.time()
        while True:
            try:
                data, addr = sock.recvfrom(65507)
                text = data.decode(errors="ignore")
                headers = {}
                for line in text.splitlines():
                    if ":" in line:
                        k,v = line.split(":",1)
                        headers[k.strip().upper()] = v.strip()
                headers["_from"] = addr[0]
                results.append(headers)
            except socket.timeout:
                break
            if time.time() - start > timeout + mx:
                break
    finally:
        sock.close()
    return results


# ---------------- KOMENDY SIECI ----------------
network_commands = {
    "wifi_scan": wifi_scan,
    "ping": ping,
    "traceroute": traceroute,
    "netstat": netstat_enriched,
    "systeminfo": system_info,
    "upnp.scan": cmd_upnp_scan,
    "ssdp_discover": ssdp_discover,
    "nmap_scan": lambda *p: run_python_script(*(p if p else (None,))),
    "wifi_interfaces": wifi_interfaces,
    "wifi_status": wifi_status,
    "wifi_profiles": wifi_profiles,
    "wifi_profile_info": wifi_profile_info,
    "wifi_strength": wifi_strength,
    "wifi_channels": wifi_channels,
    "wifi_bssid": wifi_bssid,
    "wifi_disconnect": wifi_disconnect,
    "wifi_reconnect": wifi_reconnect,
    "wifi_driver": wifi_driver,
}



# jeśli chcesz możliwość uruchomienia dowolnego skryptu:
network_commands["run_py"] = lambda *p: run_python_script(*(p if p else (None,)))

# lub, lepiej: wrapper z domyślną ścieżką do IS.py na pulpicie
#def run_is_wrapper(*p):
 ###     run_python_script(default_path=desktop_path, background=True, *p[1:])
      #     run_python_script(default_path=desktop_path)





# ---------------- MAIN LOOP ----------------
def main():
    set_console_style()
    print(Fore.CYAN + BANNER_TEXT + Style.RESET_ALL)
    while True:
        try:
            cmd_input = input(build_prompt())
            if not cmd_input.strip():
                continue
            args = shlex.split(cmd_input)
            cmd = args[0].lower()
            params = args[1:]

            if cmd == "exit":
                break
            elif cmd in fs_commands:
                fs_commands[cmd](*params)
            elif cmd in network_commands:
                network_commands[cmd](*params)
            elif cmd == "help":
                print(Fore.CYAN + "Dostępne komendy FS: " + ", ".join(fs_commands.keys()) + Style.RESET_ALL)
                print(Fore.MAGENTA + "Dostępne komendy sieciowe: " + ", ".join(network_commands.keys()) + Style.RESET_ALL)
                print(Fore.GREEN + "Inne: help, exit" + Style.RESET_ALL)
            else:
                print(Fore.YELLOW + f"Nieznana komenda: {cmd}" + Style.RESET_ALL)
        except KeyboardInterrupt:
            print("\n" + Fore.MAGENTA + "[*] Przerwano Ctrl+C" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + "[-] Błąd w main loop:" + Style.RESET_ALL, e)

if __name__ == "__main__":
    main()
