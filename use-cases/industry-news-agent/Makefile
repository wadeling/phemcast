# Makefile for Industry News Agent Docker builds

.PHONY: help build-frontend build-backend build-all clean

# Default target
help:
	@echo "Industry News Agent Docker Build Commands"
	@echo "========================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make build-frontend  - Build frontend Docker image"
	@echo "  make build-backend   - Build backend Docker image"
	@echo "  make build-all       - Build both frontend and backend images"
	@echo "  make clean           - Remove all built images"
	@echo "  make help            - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make build-frontend  # Build only frontend"
	@echo "  make build-backend   # Build only backend"
	@echo "  make build-all       # Build both images"

# Build frontend Docker image
build-frontend:
	@echo "🚀 Building frontend Docker image..."
	docker build -f build/frontend/Dockerfile -t industry-news-agent-frontend:latest .
	@echo "✅ Frontend image built successfully: industry-news-agent-frontend:latest"

# Build backend Docker image
build-backend:
	@echo "📦 Building backend Docker image..."
	docker build -f build/backend/Dockerfile -t industry-news-agent-backend:latest .
	@echo "✅ Backend image built successfully: industry-news-agent-backend:latest"

# Build both images
build-all: build-frontend build-backend
	@echo ""
	@echo "🎉 All Docker images built successfully!"
	@echo ""
	@echo "Images created:"
	@echo "  - industry-news-agent-frontend:latest"
	@echo "  - industry-news-agent-backend:latest"
	@echo ""
	@echo "To run the application:"
	@echo "  cd build && ./deploy.sh start"

# Clean up Docker images
clean:
	@echo "🧹 Cleaning up Docker images..."
	@if docker images | grep -q "industry-news-agent-frontend"; then \
		docker rmi industry-news-agent-frontend:latest; \
		echo "✅ Removed frontend image"; \
	else \
		echo "ℹ️  Frontend image not found"; \
	fi
	@if docker images | grep -q "industry-news-agent-backend"; then \
		docker rmi industry-news-agent-backend:latest; \
		echo "✅ Removed backend image"; \
	else \
		echo "ℹ️  Backend image not found"; \
	fi
	@echo "🧹 Cleanup completed!"

# Show Docker images
images:
	@echo "🐳 Current Docker images:"
	docker images | grep "industry-news-agent" || echo "No industry-news-agent images found"

# Quick start (build and run)
start: build-all
	@echo ""
	@echo "🚀 Starting application..."
	cd build && ./deploy.sh start

# Stop application
stop:
	@echo "🛑 Stopping application..."
	cd build && ./deploy.sh stop

# Show application status
status:
	@echo "📊 Application status:"
	cd build && ./deploy.sh status

# Show application logs
logs:
	@echo "📝 Application logs:"
	cd build && ./deploy.sh logs
