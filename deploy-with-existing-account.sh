#!/bin/bash

# Deploy Space Bio Engine with existing Elasticsearch Cloud account
# This script configures and deploys the application with your existing ES account

set -e

echo "🚀 Deploying Space Bio Engine with your existing Elasticsearch Cloud account..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "Node.js/npm is required but not installed."
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed."
        exit 1
    fi
    
    print_success "All dependencies are installed."
}

# Get Elasticsearch credentials
get_elasticsearch_credentials() {
    print_status "Configuring Elasticsearch Cloud connection..."
    
    echo ""
    echo "📋 ELASTICSEARCH CLOUD CONFIGURATION:"
    echo "Please provide your Elasticsearch Cloud details:"
    echo ""
    
    read -p "Elasticsearch Endpoint (e.g., https://your-cluster.es.region.aws.found.io:9243): " ES_ENDPOINT
    read -p "API Key (from Security → API Keys): " ES_API_KEY
    
    if [ -z "$ES_ENDPOINT" ] || [ -z "$ES_API_KEY" ]; then
        print_error "Elasticsearch endpoint and API key are required."
        exit 1
    fi
    
    # Create environment file
    cat > backend/.env << EOF
ES_ENDPOINT=$ES_ENDPOINT
ES_API_KEY=$ES_API_KEY
CORS_ORIGIN=http://localhost:3000
DATABASE_PATH=data/papers.db
CSV_PATH=data/papers.csv
EOF
    
    print_success "Elasticsearch configuration saved."
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    cd backend
    pip install -r requirements.txt
    pip install elasticsearch requests
    cd ..
    
    print_success "Python dependencies installed."
}

# Install Node.js dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."
    
    npm install
    
    print_success "Node.js dependencies installed."
}

# Test Elasticsearch connection
test_elasticsearch() {
    print_status "Testing Elasticsearch connection..."
    
    cd backend
    python3 -c "
import os
from elasticsearch_service import es_service
import sys

try:
    # Test connection
    result = es_service.search_papers(query='test', size=1)
    print('✅ Elasticsearch connection successful')
    print(f'📊 Total papers in index: {result.get(\"total\", 0)}')
except Exception as e:
    print(f'❌ Elasticsearch connection failed: {e}')
    print('Please check your endpoint and API key.')
    sys.exit(1)
"
    cd ..
    
    print_success "Elasticsearch connection test passed."
}

# Migrate data to Elasticsearch
migrate_data() {
    print_status "Migrating data to Elasticsearch..."
    
    cd backend
    python3 migrate_to_elasticsearch.py
    cd ..
    
    print_success "Data migration completed."
}

# Start services
start_services() {
    print_status "Starting services..."
    
    # Start backend in background
    cd backend
    python3 app_elasticsearch.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to start
    sleep 5
    
    # Start frontend
    npm run dev &
    FRONTEND_PID=$!
    
    echo ""
    print_success "Services started!"
    echo "🔗 Backend: http://localhost:5001"
    echo "🔗 Frontend: http://localhost:3000"
    echo ""
    echo "📊 Elasticsearch features available:"
    echo "   • Advanced full-text search"
    echo "   • Faceted filtering"
    echo "   • Fuzzy matching"
    echo "   • Relevance scoring"
    echo "   • Search suggestions"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for user to stop
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
}

# Main deployment flow
main() {
    print_status "Starting Space Bio Engine deployment with your Elasticsearch Cloud account..."
    
    check_dependencies
    get_elasticsearch_credentials
    install_python_deps
    install_node_deps
    test_elasticsearch
    migrate_data
    start_services
}

# Run main function
main
