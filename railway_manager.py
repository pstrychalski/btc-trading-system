#!/usr/bin/env python3
"""
Skrypt Python do zarządzania Railway CLI
Autor: Automatycznie wygenerowany
Data: 2025-10-05
"""

import subprocess
import sys
import os
from typing import Optional, List


class Colors:
    """Kolory ANSI dla terminala"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class RailwayManager:
    """Klasa do zarządzania Railway CLI"""
    
    def __init__(self):
        self.check_railway_cli()
    
    def run_command(self, command: List[str], capture_output: bool = False) -> Optional[str]:
        """Uruchamia komendę Railway"""
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            else:
                subprocess.run(command, check=True)
                return None
        except subprocess.CalledProcessError as e:
            self.log_error(f"Błąd podczas wykonywania komendy: {e}")
            return None
        except FileNotFoundError:
            self.log_error("Railway CLI nie jest zainstalowane!")
            sys.exit(1)
    
    def log_info(self, message: str):
        """Wyświetla informację"""
        print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")
    
    def log_error(self, message: str):
        """Wyświetla błąd"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=sys.stderr)
    
    def log_warning(self, message: str):
        """Wyświetla ostrzeżenie"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
    
    def check_railway_cli(self):
        """Sprawdza czy Railway CLI jest zainstalowane"""
        try:
            subprocess.run(
                ['railway', '--version'],
                capture_output=True,
                check=True
            )
            self.log_info("Railway CLI jest zainstalowane ✓")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_error("Railway CLI nie jest zainstalowane!")
            print("\nZainstaluj Railway CLI używając:")
            print("  npm i -g @railway/cli")
            print("lub")
            print("  brew install railway")
            sys.exit(1)
    
    def check_login(self) -> bool:
        """Sprawdza czy użytkownik jest zalogowany"""
        result = self.run_command(['railway', 'whoami'], capture_output=True)
        if result:
            self.log_info(f"Zalogowany jako: {result}")
            return True
        else:
            self.log_warning("Nie jesteś zalogowany do Railway")
            return False
    
    def login(self):
        """Loguje do Railway"""
        self.log_info("Logowanie do Railway...")
        self.run_command(['railway', 'login'])
    
    def init_project(self):
        """Inicjalizuje nowy projekt Railway"""
        self.log_info("Inicjalizacja projektu Railway...")
        self.run_command(['railway', 'init'])
    
    def link_project(self):
        """Linkuje z istniejącym projektem"""
        self.log_info("Dostępne projekty:")
        self.run_command(['railway', 'list'])
        print()
        self.log_info("Linkowanie z projektem...")
        self.run_command(['railway', 'link'])
    
    def deploy(self):
        """Wdraża aplikację"""
        self.log_info("Rozpoczynam deployment...")
        self.run_command(['railway', 'up'])
        self.log_info("Deployment zakończony pomyślnie! ✓")
    
    def show_logs(self):
        """Wyświetla logi aplikacji"""
        self.log_info("Wyświetlanie logów...")
        self.run_command(['railway', 'logs'])
    
    def open_project(self):
        """Otwiera projekt w przeglądarce"""
        self.log_info("Otwieranie projektu w przeglądarce...")
        self.run_command(['railway', 'open'])
    
    def set_env_vars(self, env_file: str = '.env'):
        """Ustawia zmienne środowiskowe"""
        self.log_info("Ustawianie zmiennych środowiskowych...")
        if os.path.exists(env_file):
            self.log_info(f"Znaleziono plik {env_file}, importowanie...")
            self.run_command(['railway', 'variables', '--set-from-file', env_file])
        else:
            self.log_warning(f"Nie znaleziono pliku {env_file}")
            var_name = input("Podaj nazwę zmiennej: ")
            var_value = input("Podaj wartość: ")
            self.run_command(['railway', 'variables', 'set', f"{var_name}={var_value}"])
    
    def show_env_vars(self):
        """Wyświetla zmienne środowiskowe"""
        self.log_info("Zmienne środowiskowe:")
        self.run_command(['railway', 'variables'])
    
    def run_local(self, command: str):
        """Uruchamia aplikację lokalnie z konfiguracją Railway"""
        self.log_info(f"Uruchamianie lokalnie: {command}")
        self.run_command(['railway', 'run'] + command.split())
    
    def show_status(self):
        """Wyświetla status projektu"""
        self.log_info("Status projektu Railway:")
        self.run_command(['railway', 'status'])
    
    def show_project_info(self):
        """Wyświetla informacje o projekcie"""
        self.log_info("Informacje o projekcie:")
        print()
        whoami = self.run_command(['railway', 'whoami'], capture_output=True)
        if whoami:
            print(f"Nazwa użytkownika: {whoami}")
        self.run_command(['railway', 'status'])
    
    def show_menu(self):
        """Wyświetla menu główne"""
        print("\n" + "=" * 45)
        print("   Railway CLI - Zarządzanie Projektem (Python)")
        print("=" * 45)
        print("1.  Inicjalizuj nowy projekt")
        print("2.  Linkuj z istniejącym projektem")
        print("3.  Deploy aplikacji")
        print("4.  Wyświetl logi")
        print("5.  Otwórz projekt w przeglądarce")
        print("6.  Ustaw zmienne środowiskowe")
        print("7.  Pokaż zmienne środowiskowe")
        print("8.  Uruchom lokalnie")
        print("9.  Pokaż status")
        print("10. Sprawdź informacje o projekcie")
        print("0.  Wyjście")
        print("=" * 45)
    
    def run_interactive(self):
        """Uruchamia tryb interaktywny"""
        if not self.check_login():
            response = input("Czy chcesz się zalogować teraz? (t/n): ")
            if response.lower() in ['t', 'tak', 'y', 'yes']:
                self.login()
        
        while True:
            try:
                self.show_menu()
                choice = input("Wybierz opcję: ").strip()
                
                if choice == '1':
                    self.init_project()
                elif choice == '2':
                    self.link_project()
                elif choice == '3':
                    self.deploy()
                elif choice == '4':
                    self.show_logs()
                elif choice == '5':
                    self.open_project()
                elif choice == '6':
                    self.set_env_vars()
                elif choice == '7':
                    self.show_env_vars()
                elif choice == '8':
                    command = input("Podaj komendę do uruchomienia: ")
                    self.run_local(command)
                elif choice == '9':
                    self.show_status()
                elif choice == '10':
                    self.show_project_info()
                elif choice == '0':
                    self.log_info("Do widzenia!")
                    break
                else:
                    self.log_error("Nieprawidłowa opcja!")
                
                input("\nNaciśnij Enter, aby kontynuować...")
            except KeyboardInterrupt:
                print()
                self.log_info("Przerwano przez użytkownika")
                break
            except Exception as e:
                self.log_error(f"Wystąpił błąd: {e}")


def main():
    """Główna funkcja"""
    manager = RailwayManager()
    
    if len(sys.argv) > 1:
        # Tryb wiersza poleceń
        command = sys.argv[1]
        
        if command == 'init':
            manager.init_project()
        elif command == 'link':
            manager.link_project()
        elif command == 'deploy':
            manager.deploy()
        elif command == 'logs':
            manager.show_logs()
        elif command == 'open':
            manager.open_project()
        elif command == 'set-env':
            env_file = sys.argv[2] if len(sys.argv) > 2 else '.env'
            manager.set_env_vars(env_file)
        elif command == 'show-env':
            manager.show_env_vars()
        elif command == 'run':
            if len(sys.argv) < 3:
                manager.log_error("Podaj komendę do uruchomienia")
                sys.exit(1)
            manager.run_local(' '.join(sys.argv[2:]))
        elif command == 'status':
            manager.show_status()
        elif command == 'info':
            manager.show_project_info()
        elif command == 'login':
            manager.login()
        else:
            manager.log_error(f"Nieznana komenda: {command}")
            print("\nDostępne komendy:")
            print("  init, link, deploy, logs, open,")
            print("  set-env, show-env, run, status, info, login")
            sys.exit(1)
    else:
        # Tryb interaktywny
        manager.run_interactive()


if __name__ == '__main__':
    main()

