#!/bin/bash

# BTC Trading System - Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Main functions
build_all() {
    print_status "Building all services..."
    docker-compose build
    print_success "All services built successfully!"
}

start_all() {
    print_status "Starting all services..."
    docker-compose up -d
    print_success "All services started!"
}

stop_all() {
    print_status "Stopping all services..."
    docker-compose down
    print_success "All services stopped!"
}

restart_all() {
    print_status "Restarting all services..."
    docker-compose down
    docker-compose up -d
    print_success "All services restarted!"
}

logs() {
    if [ -z "$1" ]; then
        print_status "Showing logs for all services..."
        docker-compose logs -f
    else
        print_status "Showing logs for $1..."
        docker-compose logs -f "$1"
    fi
}

status() {
    print_status "Service status:"
    docker-compose ps
}

health_check() {
    print_status "Checking service health..."
    
    services=("data-validation:8082" "mlflow-tracking:5000" "freqtrade-integration:8089" "market-memory:8085")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            print_success "$name is healthy"
        else
            print_error "$name is not responding"
        fi
    done
}

clean() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v
    docker system prune -f
    print_success "Cleanup completed!"
}

# Main script
case "$1" in
    "build")
        build_all
        ;;
    "start")
        start_all
        ;;
    "stop")
        stop_all
        ;;
    "restart")
        restart_all
        ;;
    "logs")
        logs "$2"
        ;;
    "status")
        status
        ;;
    "health")
        health_check
        ;;
    "clean")
        clean
        ;;
    *)
        echo "Usage: $0 {build|start|stop|restart|logs|status|health|clean}"
        echo ""
        echo "Commands:"
        echo "  build   - Build all Docker images"
        echo "  start   - Start all services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show logs (optionally for specific service)"
        echo "  status  - Show service status"
        echo "  health  - Check service health"
        echo "  clean   - Clean up Docker resources"
        echo ""
        echo "Examples:"
        echo "  $0 build"
        echo "  $0 start"
        echo "  $0 logs data-validation"
        echo "  $0 health"
        exit 1
        ;;
esac
