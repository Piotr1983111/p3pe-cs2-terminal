import subprocess
import sys
import os

# Definicja polecenia Nmap, które ma zostać wykonane
# -sV: wykrywanie wersji usług
# -O: wykrywanie systemu operacyjnego (wymaga uprawnień administratora w Windows)
# 192.168.0.1: adres docelowy
# -oN audyt_wyniki.txt: zapisanie wyników do pliku w normalnym formacie
nmap_command = ["nmap", "-sV", "-O", "192.168.0.1", "-oN", "audyt_wyniki.txt"]

print(f"Rozpoczynanie skanowania Nmap: {' '.join(nmap_command)}")
print(f"Wyniki zostaną zapisane w pliku: {os.path.abspath('audyt_wyniki.txt')}")

try:
    # Uruchomienie procesu Nmap
    # stdout=subprocess.PIPE i stderr=subprocess.PIPE przechwytują standardowe wyjście/błędy
    result = subprocess.run(nmap_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
    
    print("\n--- Standardowe wyjście Nmap ---")
    print(result.stdout)
    
    print("Skanowanie Nmap zakończone pomyślnie.")
    print("Sprawdź plik 'audyt_wyniki.txt' w katalogu, z którego uruchomiono skrypt.")

except subprocess.CalledProcessError as e:
    print(f"\n--- Błąd podczas wykonywania Nmap ---")
    print(f"Kod zakończenia: {e.returncode}")
    print(f"Standardowe błędy (stderr): {e.stderr}")
    print(f"Standardowe wyjście (stdout): {e.stdout}")
    print("Upewnij się, że Nmap jest zainstalowany i dostępny w zmiennej PATH.")
    sys.exit(1)
except FileNotFoundError:
    print("\n--- Błąd: Nie znaleziono pliku wykonywalnego Nmap ---")
    print("Upewnij się, że Nmap jest zainstalowany i ścieżka do niego jest dodana do zmiennej systemowej PATH.")
    sys.exit(1)
except Exception as e:
    print(f"\n--- Wystąpił nieoczekiwany błąd: {e} ---")
    sys.exit(1)

