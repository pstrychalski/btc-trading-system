#!/bin/bash

# ==============================================================================
# Deploy to Railway - Automated Deployment Script
# ==============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

# Check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI is not installed!"
        echo "Install it with: npm i -g @railway/cli"
        exit 1
    fi
    log_info "Railway CLI found ✓"
}

# Check if user is logged in
check_login() {
    if ! railway whoami &> /dev/null; then
        log_error "Not logged in to Railway!"
        echo ""
        echo "Please login first:"
        echo "  railway login"
        echo ""
        exit 1
    fi
    log_info "Logged in as: $(railway whoami)"
}

# Initialize Railway project
init_project() {
    log_step "STEP 1: Initialize Railway Project"
    
    if [ -d ".railway" ]; then
        log_info "Railway project already initialized"
    else
        log_info "Initializing new Railway project..."
        railway init
    fi
}

# Create and deploy PostgreSQL
deploy_postgres() {
    log_step "STEP 2: Deploy PostgreSQL Database"
    
    log_info "Creating PostgreSQL service..."
    railway add --plugin postgresql || log_warning "PostgreSQL might already exist"
    
    log_info "PostgreSQL deployed ✓"
}

# Create and deploy Redis
deploy_redis() {
    log_step "STEP 3: Deploy Redis Cache"
    
    log_info "Creating Redis service..."
    railway add --plugin redis || log_warning "Redis might already exist"
    
    log_info "Redis deployed ✓"
}

# Deploy Qdrant
deploy_qdrant() {
    log_step "STEP 4: Deploy Qdrant Vector Database"
    
    log_info "Building and deploying Qdrant..."
    cd services/qdrant
    railway up || log_error "Qdrant deployment failed"
    cd ../..
    
    log_info "Qdrant deployed ✓"
}

# Deploy Data Validation Service
deploy_data_validation() {
    log_step "STEP 5: Deploy Data Validation Service"
    
    log_info "Building and deploying Data Validation..."
    cd services/data-validation
    railway up || log_error "Data Validation deployment failed"
    cd ../..
    
    log_info "Data Validation deployed ✓"
}

# Deploy MLflow
deploy_mlflow() {
    log_step "STEP 6: Deploy MLflow Tracking Server"
    
    log_info "Building and deploying MLflow..."
    cd services/mlflow
    railway up || log_error "MLflow deployment failed"
    cd ../..
    
    log_info "MLflow deployed ✓"
}

# Set environment variables
set_environment_variables() {
    log_step "STEP 7: Set Environment Variables"
    
    if [ ! -f ".env.railway" ]; then
        log_error ".env.railway file not found!"
        echo "Please create .env.railway with your configuration"
        exit 1
    fi
    
    log_info "Setting environment variables from .env.railway..."
    
    # Read .env.railway and set variables
    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        
        # Extract key=value
        if [[ "$line" =~ ^([A-Z_]+)=(.+)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            
            log_info "Setting $key..."
            railway variables set "$key=$value" || log_warning "Failed to set $key"
        fi
    done < .env.railway
    
    log_info "Environment variables set ✓"
}

# Deploy remaining services
deploy_all_services() {
    log_step "STEP 8: Deploy Remaining Services"
    
    services=(
        "data-collector"
        "pathway"
        "market-memory"
        "backtest-engine"
        "market-sim"
        "rl-agent"
        "freqtrade"
    )
    
    for service in "${services[@]}"; do
        if [ -d "services/$service" ]; then
            log_info "Deploying $service..."
            cd "services/$service"
            railway up || log_warning "$service deployment failed (might not be ready yet)"
            cd ../..
        else
            log_warning "$service directory not found, skipping"
        fi
    done
}

# Show deployed services
show_status() {
    log_step "DEPLOYMENT COMPLETE!"
    
    log_info "Checking service status..."
    railway status
    
    echo ""
    log_info "Your services are being deployed!"
    echo ""
    echo "Access your dashboards:"
    echo "  - Railway Dashboard: https://railway.app/dashboard"
    echo "  - MLflow: Check Railway for public URL"
    echo "  - Grafana: Check Railway for public URL"
    echo ""
    echo "To view logs:"
    echo "  railway logs"
    echo ""
    echo "To check status:"
    echo "  railway status"
    echo ""
}

# Main execution
main() {
    log_step "🚀 RAILWAY DEPLOYMENT SCRIPT"
    log_info "Deploying Zaawansowany System Tradingowy BTC"
    
    check_railway_cli
    check_login
    
    # Ask for confirmation
    echo ""
    read -p "This will deploy multiple services to Railway. Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
    
    # Execute deployment steps
    init_project
    deploy_postgres
    deploy_redis
    
    # Data Validation is ready
    deploy_data_validation
    
    # MLflow
    # deploy_mlflow  # Uncomment when ready
    
    # Qdrant
    # deploy_qdrant  # Uncomment when ready
    
    set_environment_variables
    
    # Deploy other services (when ready)
    # deploy_all_services
    
    show_status
    
    log_info "Deployment script completed! ✓"
}

# Run main function
main "$@"

