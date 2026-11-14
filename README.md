# 🖥️ P3PE CS2 Cyber Analytic Terminal

**P3PE Cyber Analytic Terminal** to autorski, okienkowy terminal diagnostyczny w stylu retro-sci-fi, napisany w Pythonie (Tkinter). Łączy narzędzia sieciowe używane w codziennej pracy **IT Support / Helpdesk** z bezpiecznym systemem zarządzania plikami (sandbox).

![Podgląd aplikacji](screenshot.png)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![GUI](https://img.shields.io/badge/GUI-Tkinter-informational)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Funkcje

- **Okno aplikacji** z dashboardem (siły sygnałów Wi-Fi, status sieci), paskiem postępu i panelem logów w czasie rzeczywistym.
- **Konsola komend** z kolorowym wyjściem – wpisujesz komendy tak jak w terminalu.
- **Diagnostyka sieci:** skan Wi-Fi, `ping`, `traceroute`, aktywne połączenia, wykrywanie urządzeń UPnP/SSDP.
- **Sandbox plików:** operacje na plikach i folderach są ograniczone do katalogu `.terminal_fs`, więc nie da się wyjść poza niego.
- **Uruchamianie własnych skryptów Pythona** (np. skanera) bezpośrednio z terminala.
- **Zero zależności zewnętrznych** – tylko biblioteka standardowa Pythona (`tkinter`, `socket`, `subprocess`, `threading`, `queue`). Nie trzeba niczego instalować przez `pip`.

---

## 🚀 Szybki start

### Wymagania

- Python **3.8 lub nowszy** z modułem `tkinter` (na Windowsie jest w standardowym instalatorze; na Debianie/Ubuntu: `sudo apt install python3-tk`).
- Windows (pełna funkcjonalność, m.in. `netsh`) lub Linux (`nmcli`, `traceroute`, `ss`).

### Uruchomienie ze źródeł

```bash
git clone https://github.com/Piotr1983111/p3pe-cs2-terminal.git
cd p3pe-cs2-terminal
python cs2a.py
```

### Uruchomienie gotowego pliku `.exe` (Windows)

1. Pobierz `cs2a.exe` z repozytorium.
2. Uruchom dwuklikiem.

> ⚠️ Plik `.exe` nie jest podpisany cyfrowo, więc Windows SmartScreen może wyświetlić ostrzeżenie. Został zbudowany z `cs2a.py` przy użyciu PyInstallera (patrz niżej). Jeśli wolisz, uruchom program bezpośrednio ze źródeł.

---

## ⌨️ Komendy

Wpisz `help` w terminalu, aby zobaczyć listę w aplikacji.

### Pliki (sandbox)

| Komenda | Opis | Przykład |
|---|---|---|
| `mkfolder <nazwa>` | Tworzy folder | `mkfolder raporty` |
| `ls [folder]` | Wyświetla zawartość folderu | `ls raporty` |
| `touch <plik>` | Tworzy pusty plik | `touch raporty/log.txt` |
| `write <plik> <tekst>` | Zapisuje tekst do pliku | `write notatka.txt Test sieci OK` |
| `read <plik>` | Wyświetla zawartość pliku | `read notatka.txt` |
| `rm <plik/folder>` | Usuwa plik lub folder | `rm raporty` |

### Sieć

| Komenda | Opis | Przykład |
|---|---|---|
| `wifi_scan` | Skanuje dostępne sieci Wi-Fi (`netsh` / `nmcli`) | `wifi_scan` |
| `ping [host]` | Ping (domyślnie `8.8.8.8`) | `ping 1.1.1.1` |
| `traceroute [host]` | Trasa pakietów (`tracert` / `traceroute`) | `traceroute google.com` |
| `netstat` | Aktywne połączenia (`netstat -ano` / `ss -tulnp`) | `netstat` |
| `systeminfo` | Nazwa hosta, adres IP, system operacyjny | `systeminfo` |
| `upnp` | Wykrywa urządzenia UPnP/SSDP w sieci lokalnej | `upnp` |
| `nmap_scan <skrypt.py> [args]` | Uruchamia zewnętrzny skrypt Pythona | `nmap_scan skan.py 192.168.0.1` |

### Pozostałe

| Komenda | Opis |
|---|---|
| `dashboard` | Odświeża dashboard |
| `help` | Lista dostępnych komend |
| `exit` | Zamyka aplikację |

---

## 🔒 Bezpieczeństwo

- Wszystkie operacje na plikach działają wyłącznie w katalogu `.terminal_fs` (ścieżki wychodzące poza sandbox, np. `..\..\`, są odrzucane).
- Narzędzia sieciowe wywołują standardowe polecenia systemowe i nie wysyłają żadnych danych poza Twoją sieć.
- **Używaj skanowania wyłącznie we własnej sieci lub za zgodą jej właściciela.**
