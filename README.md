\# P3PE CS2-style File \& Network Terminal (`cs2fs.py`)
P3PE CS2-style File & Network Terminal (cs2fs.py) to lekki, konsolowy terminal diagnostyczny napisany w Pythonie, inspirowany klimatem konsoli z CS2.
Projekt łączy prosty, wydzielony sandbox systemu plików z zestawem narzędzi sieciowych i Wi-Fi dla stacji roboczych z Windows.

Terminal pozwala m.in. na:

bezpieczną pracę na plikach i katalogach w wydzielonym sandboxie (tworzenie, usuwanie, przenoszenie, zip/unzip),

wykonywanie podstawowych operacji sieciowych: ping, traceroute, rozszerzony netstat, ipconfig, skan UPnP/SSDP,

szybki podgląd stanu systemu (systeminfo: hostname, IP, OS, CPU, RAM, uptime, interfejsy sieciowe),

obsługę narzędzi Wi-Fi opartych o netsh (skan sieci, profile, sterowniki, siła sygnału, rozłącz/połącz),

uruchamianie zewnętrznych skryptów Python z poziomu terminala (run_py, alias nmap_scan).

Projekt powstał jako narzędzie do nauki oraz element portfolio pod kątem ról takich jak Helpdesk / Service Desk, NOC, SOC Tier 1, Data Center Technician

require is.py on deskop
require cs2_is.py put on any path

Customowy terminal w Pythonie inspirowany konsolą z CS2 – z własnym systemem plików (sandbox), narzędziami sieciowymi (Wi-Fi scan, netstat, UPnP/SSDP), system info i możliwością uruchamiania skryptów Python.



Projekt stworzony jako narzędzie do nauki, diagnostyki i do portfolio (helpdesk / NOC / SOC / data center / junior cybersec).


## Example usage

```text
cs2> mkfolder projekty
cs2> ls
cs2> write projekty/notes.txt Pierwszy zapis w sandboxie
cs2> read projekty/notes.txt

cs2> wifi_scan
cs2> ping 8.8.8.8
cs2> systeminfo
cs2> upnp.scan
cs2> run_py scripts/demo.py


---



\## Funkcje



\### 🗂 Filesystem (sandbox)



\- `ls` – lista plików

\- `mkfolder` / `mkdir` – tworzenie folderów

\- `rm` – usuwanie plików / katalogów

\- `rename` – zmiana nazwy

\- `move` – przenoszenie

\- `touch` – tworzenie pustego pliku

\- `write` – zapis tekstu do pliku

\- `read` – podgląd zawartości

\- `zip` / `unzip` – pakowanie i rozpakowywanie folderów



\### 🌐 Network



\- `wifi\_scan` – skan dostępnych sieci Wi-Fi (Windows, `netsh`)

\- `ping` – sprawdzenie łączności z hostem

\- `traceroute` – trasa pakietów do hosta

\- `netstat` – lista portów i połączeń

\- `upnp.scan` – skan lokalnych urządzeń UPnP/SSDP



\### 💻 System



\- `systeminfo` – podstawowe informacje o systemie (hostname, IP, OS, itd.)



\### 🐍 Python



\- `run\_py` – uruchamianie zewnętrznych skryptów .py z poziomu terminala



---



\## Wymagania



\- Python 3.10+

\- Windows 10/11 (wymagane dla `netsh wlan`, PowerShell itp.)

\- Biblioteki z `requirements.txt`:



```bash

pip install -r requirements.txt



