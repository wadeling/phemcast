#!/bin/bash

# Deployment script for Industry News Agent

set -e

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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the application"
    echo "  stop      - Stop the application"
    echo "  restart   - Restart the application"
    echo "  status    - Show application status"
    echo "  logs      - Show application logs"
    echo "  build     - Build and start the application"
    echo "  clean     - Stop and remove containers, networks, and volumes"
    echo "  help      - Show this help message"
    echo ""
    echo "Options:"
    echo "  PLATFORM=platform  - Set target platform (default: linux/amd64)"
    echo "  REGISTRY=registry   - Set registry name (default: ccr.ccs.tencentyun.com)"
    echo "  REPO=repo          - Set repository name (default: phemcast)"
    echo ""
    echo "Examples:"
    echo "  $0 start                           # Start the application"
    echo "  $0 start PLATFORM=linux/arm64     # Start with ARM64 platform"
    echo "  $0 build PLATFORM=linux/arm64     # Build and start for ARM64"
    echo "  $0 logs                           # Show logs"
    echo "  $0 restart                        # Restart the application"
}

# Function to start the application
start_app() {
    print_status "Starting Industry News Agent..."
    
    # Show platform information
    if [ -n "$PLATFORM" ]; then
        print_status "Target platform: $PLATFORM"
    else
        print_status "Target platform: linux/amd64 (default)"
    fi
    
    if docker-compose ps | grep -q "Up"; then
        print_warning "Application is already running. Use 'restart' to restart it."
        return
    fi
    
    docker-compose up -d
    print_success "Application started successfully!"
    print_status "Frontend: http://localhost"
    print_status "Backend API: http://localhost:8000"
    print_status "Health check: http://localhost/health"
}

# Function to stop the application
stop_app() {
    print_status "Stopping Industry News Agent..."
    docker-compose down
    print_success "Application stopped successfully!"
}

# Function to restart the application
restart_app() {
    print_status "Restarting Industry News Agent..."
    docker-compose down
    docker-compose up -d
    print_success "Application restarted successfully!"
}

# Function to show application status
show_status() {
    print_status "Application Status:"
    echo ""
    docker-compose ps
    echo ""
    
    # Show resource usage
    print_status "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Function to show application logs
show_logs() {
    print_status "Showing application logs (Press Ctrl+C to exit)..."
    docker-compose logs -f
}

# Function to build and start the application
build_and_start() {
    print_status "Building and starting Industry News Agent..."
    
    # Show platform information
    if [ -n "$PLATFORM" ]; then
        print_status "Target platform: $PLATFORM"
    else
        print_status "Target platform: linux/amd64 (default)"
    fi
    
    # Build the backend image
    print_status "Building backend image..."
    docker-compose build backend
    
    if [ $? -eq 0 ]; then
        print_success "Backend image built successfully!"
        start_app
    else
        print_error "Failed to build backend image!"
        return 1
    fi
}

# Function to clean up everything
clean_up() {
    print_warning "This will stop and remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        docker-compose down -v --remove-orphans
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Main script logic
main() {
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Parse command
    case "${1:-help}" in
        start)
            start_app
            ;;
        stop)
            stop_app
            ;;
        restart)
            restart_app
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        build)
            build_and_start
            ;;
        clean)
            clean_up
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
