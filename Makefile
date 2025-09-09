# Makefile for Industry News Agent Docker builds

registryname=ccr.ccs.tencentyun.com
reponame=phemcast
imagetag=latest
platform=linux/arm64

.PHONY: help build-frontend build-backend build-all clean build-multi-platform

# Default target
help:
	@echo "Industry News Agent Docker Build Commands"
	@echo "========================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make build-frontend  - Build frontend Docker image"
	@echo "  make build-backend   - Build backend Docker image"
	@echo "  make build-all       - Build both frontend and backend images"
	@echo "  make build-multi-platform - Build for multiple platforms (amd64, arm64)"
	@echo "  make clean           - Remove all built images"
	@echo "  make help            - Show this help message"
	@echo ""
	@echo "Parameters:"
	@echo "  platform=PLATFORM    - Target platform (default: linux/amd64)"
	@echo "  imagetag=TAG         - Image tag (default: latest)"
	@echo "  registryname=REGISTRY - Registry name (default: ccr.ccs.tencentyun.com)"
	@echo "  reponame=REPO        - Repository name (default: phemcast)"
	@echo ""
	@echo "Examples:"
	@echo "  make build-frontend                    # Build frontend for x86_64"
	@echo "  make build-frontend platform=linux/arm64  # Build frontend for ARM64"
	@echo "  make build-backend platform=linux/arm64   # Build backend for ARM64"
	@echo "  make build-all platform=linux/arm64       # Build both for ARM64"
	@echo "  make build-all imagetag=v1.0.0            # Build with custom tag"

# Build frontend Docker image
build-frontend:
	@echo "🚀 Building frontend Docker image for platform: ${platform}..."
	docker build --platform ${platform} -f build/frontend/Dockerfile -t ${registryname}/${reponame}/frontend:${imagetag} .
	@echo "✅ Frontend image built successfully: ${registryname}/${reponame}/frontend:${imagetag} (${platform})"

# Build backend Docker image
build-backend:
	@echo "📦 Building backend Docker image for platform: ${platform}..."
	docker build --platform ${platform} -f build/backend/Dockerfile -t ${registryname}/${reponame}/backend:${imagetag} .
	@echo "✅ Backend image built successfully: ${registryname}/${reponame}/backend:${imagetag} (${platform})"

# Build both images
build-all: build-frontend build-backend
	@echo ""
	@echo "🎉 All Docker images built successfully for platform: ${platform}!"
	@echo ""
	@echo "Images created:"
	@echo "  - ${registryname}/${reponame}/frontend:${imagetag} (${platform})"
	@echo "  - ${registryname}/${reponame}/backend:${imagetag} (${platform})"
	@echo ""
	@echo "To run the application:"
	@echo "  cd deploy && ./deploy.sh start"

# Clean up Docker images
clean:
	@echo "🧹 Cleaning up Docker images..."
	@if docker images | grep -q "industry-news-agent-frontend"; then \
		docker rmi ${registryname}/${reponame}/frontend:latest; \
		echo "✅ Removed frontend image"; \
	else \
		echo "ℹ️  Frontend image not found"; \
	fi
	@if docker images | grep -q "industry-news-agent-backend"; then \
		docker rmi ${registryname}/${reponame}/backend:latest; \
		echo "✅ Removed backend image"; \
	else \
		echo "ℹ️  Backend image not found"; \
	fi
	@echo "🧹 Cleanup completed!"

# Show Docker images
images:
	@echo "🐳 Current Docker images:"
	docker images | grep "${reponame}" || echo "No ${reponame} images found"

# Quick start (build and run)
start: build-all
	@echo ""
	@echo "🚀 Starting application..."
	cd deploy && ./deploy.sh start

# Stop application
stop:
	@echo "🛑 Stopping application..."
	cd deploy && ./deploy.sh stop

# Show application status
status:
	@echo "📊 Application status:"
	cd deploy && ./deploy.sh status

# Show application logs
logs:
	@echo "📝 Application logs:"
	cd deploy && ./deploy.sh logs

# Build for multiple platforms
build-multi-platform:
	@echo "🌍 Building for multiple platforms..."
	@echo "Building for linux/amd64..."
	@$(MAKE) build-all platform=linux/amd64 imagetag=${imagetag}
	@echo "Building for linux/arm64..."
	@$(MAKE) build-all platform=linux/arm64 imagetag=${imagetag}-arm64
	@echo ""
	@echo "🎉 Multi-platform build completed!"
	@echo ""
	@echo "Images created:"
	@echo "  - ${registryname}/${reponame}/frontend:${imagetag} (linux/amd64)"
	@echo "  - ${registryname}/${reponame}/backend:${imagetag} (linux/amd64)"
	@echo "  - ${registryname}/${reponame}/frontend:${imagetag}-arm64 (linux/arm64)"
	@echo "  - ${registryname}/${reponame}/backend:${imagetag}-arm64 (linux/arm64)"
