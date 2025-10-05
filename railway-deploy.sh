#!/bin/bash

# Skrypt do zarządzania deploymentem przez Railway CLI
# Autor: Automatycznie wygenerowany
# Data: 2025-10-05

set -e  # Zakończ skrypt przy błędzie

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funkcja do wyświetlania komunikatów
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Sprawdź czy Railway CLI jest zainstalowane
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI nie jest zainstalowane!"
        echo "Zainstaluj Railway CLI używając:"
        echo "npm i -g @railway/cli"
        echo "lub"
        echo "brew install railway"
        exit 1
    fi
    log_info "Railway CLI jest zainstalowane ✓"
}

# Sprawdź czy użytkownik jest zalogowany
check_login() {
    if ! railway whoami &> /dev/null; then
        log_warning "Nie jesteś zalogowany do Railway"
        log_info "Logowanie..."
        railway login
    else
        log_info "Zalogowany jako: $(railway whoami)"
    fi
}

# Funkcja do inicjalizacji projektu Railway
init_project() {
    log_info "Inicjalizacja projektu Railway..."
    railway init
}

# Funkcja do linkowania z istniejącym projektem
link_project() {
    log_info "Dostępne projekty:"
    railway list
    echo ""
    log_info "Linkowanie z projektem..."
    railway link
}

# Funkcja do deploymentu
deploy() {
    log_info "Rozpoczynam deployment..."
    railway up
    log_info "Deployment zakończony pomyślnie! ✓"
}

# Funkcja do wyświetlania logów
show_logs() {
    log_info "Wyświetlanie logów..."
    railway logs
}

# Funkcja do otwierania projektu w przeglądarce
open_project() {
    log_info "Otwieranie projektu w przeglądarce..."
    railway open
}

# Funkcja do ustawiania zmiennych środowiskowych
set_env_vars() {
    log_info "Ustawianie zmiennych środowiskowych..."
    if [ -f .env ]; then
        log_info "Znaleziono plik .env, importowanie..."
        railway variables --set-from-file .env
    else
        log_warning "Nie znaleziono pliku .env"
        echo "Podaj nazwę zmiennej:"
        read var_name
        echo "Podaj wartość:"
        read var_value
        railway variables set "$var_name=$var_value"
    fi
}

# Funkcja do wyświetlania zmiennych środowiskowych
show_env_vars() {
    log_info "Zmienne środowiskowe:"
    railway variables
}

# Funkcja do uruchomienia lokalnie z Railway
run_local() {
    log_info "Uruchamianie lokalnie z konfiguracją Railway..."
    railway run "$@"
}

# Funkcja do wyświetlania statusu
show_status() {
    log_info "Status projektu Railway:"
    railway status
}

# Menu główne
show_menu() {
    echo ""
    echo "=========================================="
    echo "   Railway CLI - Zarządzanie Projektem"
    echo "=========================================="
    echo "1. Inicjalizuj nowy projekt"
    echo "2. Linkuj z istniejącym projektem"
    echo "3. Deploy aplikacji"
    echo "4. Wyświetl logi"
    echo "5. Otwórz projekt w przeglądarce"
    echo "6. Ustaw zmienne środowiskowe"
    echo "7. Pokaż zmienne środowiskowe"
    echo "8. Uruchom lokalnie"
    echo "9. Pokaż status"
    echo "10. Sprawdź informacje o projekcie"
    echo "0. Wyjście"
    echo "=========================================="
    echo -n "Wybierz opcję: "
}

# Funkcja do wyświetlania informacji o projekcie
show_project_info() {
    log_info "Informacje o projekcie:"
    echo ""
    echo "Nazwa użytkownika: $(railway whoami 2>/dev/null || echo 'Nie zalogowany')"
    railway status 2>/dev/null || log_warning "Brak połączenia z projektem"
}

# Główna funkcja
main() {
    check_railway_cli
    check_login
    
    # Jeśli podano argument, wykonaj odpowiednią akcję
    if [ $# -gt 0 ]; then
        case "$1" in
            "init")
                init_project
                ;;
            "link")
                link_project
                ;;
            "deploy")
                deploy
                ;;
            "logs")
                show_logs
                ;;
            "open")
                open_project
                ;;
            "set-env")
                set_env_vars
                ;;
            "show-env")
                show_env_vars
                ;;
            "run")
                shift
                run_local "$@"
                ;;
            "status")
                show_status
                ;;
            "info")
                show_project_info
                ;;
            *)
                log_error "Nieznana komenda: $1"
                echo "Dostępne komendy: init, link, deploy, logs, open, set-env, show-env, run, status, info"
                exit 1
                ;;
        esac
    else
        # Tryb interaktywny
        while true; do
            show_menu
            read choice
            case $choice in
                1) init_project ;;
                2) link_project ;;
                3) deploy ;;
                4) show_logs ;;
                5) open_project ;;
                6) set_env_vars ;;
                7) show_env_vars ;;
                8) 
                    echo "Podaj komendę do uruchomienia:"
                    read cmd
                    run_local $cmd
                    ;;
                9) show_status ;;
                10) show_project_info ;;
                0) 
                    log_info "Do widzenia!"
                    exit 0
                    ;;
                *)
                    log_error "Nieprawidłowa opcja!"
                    ;;
            esac
            echo ""
            read -p "Naciśnij Enter, aby kontynuować..."
        done
    fi
}

# Uruchom główną funkcję
main "$@"

