.PHONY: help build test lint clean deploy pilot health bench

# Default target
help: ## Show this help message
	@echo "BetFlow Engine v0.9.0 - Production Pilot Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
build: ## Build all services
	@echo "🔨 Building BetFlow Engine..."
	docker-compose build
	@echo "✅ Build complete"

test: ## Run all tests
	@echo "🧪 Running tests..."
	docker-compose run --rm engine python -m pytest tests/ -v --cov=engine --cov-report=html
	@echo "✅ Tests complete"

lint: ## Run linting
	@echo "🔍 Running linting..."
	docker-compose run --rm engine flake8 engine/ --max-line-length=100
	docker-compose run --rm engine black --check engine/
	@echo "✅ Linting complete"

bench: ## Run performance benchmarks
	@echo "⚡ Running benchmarks..."
	docker-compose run --rm engine python benchmarks.py
	@echo "✅ Benchmarks complete"

# Canary Deployment
canary-deploy: ## Start automated canary deployment (10% → 50% → 100%)
	@echo "🚀 Starting automated canary deployment..."
	python scripts/canary_deployment.py --api-url http://localhost:8000 --stage-duration 1800
	@echo "✅ Canary deployment completed"

canary-dry-run: ## Perform canary deployment dry run
	@echo "🧪 Performing canary deployment dry run..."
	python scripts/canary_deployment.py --dry-run --api-url http://localhost:8000
	@echo "✅ Dry run completed"

# Manual Pilot Control (Legacy)
pilot-up: ## Start production pilot (10% traffic)
	@echo "🚀 Starting production pilot (10% traffic)..."
	export PILOT_TRAFFIC=10 && docker-compose -f docker-compose.pilot.yml up -d
	@echo "✅ Pilot started - monitor at http://localhost:8000/health"
	@echo "📊 SLO Monitor: python monitoring/slo_monitor.py"
	@echo "🏥 Health Check: make health"

pilot-scale-50: ## Scale pilot to 50% traffic
	@echo "📈 Scaling pilot to 50% traffic..."
	export PILOT_TRAFFIC=50 && docker-compose -f docker-compose.pilot.yml up -d
	@echo "✅ Scaled to 50% - monitor SLOs"
	@echo "⚠️ Monitor for 1-2 hours before scaling to 100%"

pilot-full: ## Scale to full production (100%)
	@echo "🌟 Scaling to full production..."
	export PILOT_TRAFFIC=100 && docker-compose -f docker-compose.pilot.yml up -d
	@echo "✅ Full production - monitor closely"
	@echo "📊 Continue monitoring SLOs for 24h"

# Rollback Management
rollback-prepare: ## Prepare rollback path (test previous version)
	@echo "🔄 Preparing rollback path..."
	python scripts/rollback_manager.py --action prepare
	@echo "✅ Rollback path prepared"

rollback-execute: ## Execute rollback to previous version
	@echo "🚨 Executing rollback..."
	python scripts/rollback_manager.py --action rollback
	@echo "✅ Rollback executed"

rollback-return: ## Return to current version
	@echo "🔄 Returning to current version..."
	python scripts/rollback_manager.py --action return
	@echo "✅ Returned to current version"

rollback-status: ## Check rollback status
	@echo "📊 Rollback status:"
	python scripts/rollback_manager.py --action status

health: ## Check system health
	@echo "🏥 Checking system health..."
	curl -s http://localhost:8000/health | jq .
	@echo ""

# Monitoring
monitor-slo: ## Start SLO monitoring
	@echo "📊 Starting SLO monitoring..."
	python monitoring/slo_monitor.py --api-url http://localhost:8000 --interval 30
	@echo "✅ SLO monitoring started"

monitor-logs: ## Monitor application logs
	@echo "📋 Monitoring application logs..."
	docker-compose logs -f

monitor-metrics: ## Show current metrics
	@echo "📊 Current metrics:"
	curl -s http://localhost:8000/metrics | jq .

monitor-status: ## Show monitoring status
	@echo "📊 Monitoring status:"
	@echo "🏥 Health: http://localhost:8000/health"
	@echo "📊 Metrics: http://localhost:8000/metrics"
	@echo "📈 Grafana: http://localhost:3001"
	@echo "🔍 Prometheus: http://localhost:9090"

# Deployment
deploy: ## Deploy to production
	@echo "🚀 Deploying to production..."
	@echo "1. Run benchmarks: make bench"
	@echo "2. Start pilot: make pilot-up"
	@echo "3. Monitor SLOs for 24h"
	@echo "4. Scale up: make pilot-scale-50"
	@echo "5. Full production: make pilot-full"
	@echo ""
	@echo "Monitor commands:"
	@echo "  make health          # Health check"
	@echo "  make bench          # Performance benchmarks"
	@echo "  docker logs -f      # Application logs"

# Maintenance
clean: ## Clean up containers and volumes
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Cleanup complete"

logs: ## Show application logs
	docker-compose logs -f

# Build and Package
build-wheels: ## Build Python wheels and source distribution
	@echo "🔨 Building Python wheels..."
	python scripts/build_wheels.py --build-all
	@echo "✅ Wheels built successfully"

build-docker-images: ## Build production Docker images
	@echo "🐳 Building Docker images..."
	docker build -t betflow-engine:0.9.0 ./engine
	docker build -t betflow-api:0.9.0 ./api
	docker build -t betflow-web:0.9.0 ./web
	@echo "✅ Docker images built"

package: build-wheels build-docker-images ## Build all packages
	@echo "📦 All packages built successfully"

# CI/CD
ci: test lint bench ## Run full CI pipeline
	@echo "✅ CI pipeline complete"

ci-build: ci package ## Run CI pipeline and build packages
	@echo "✅ CI build pipeline complete"
