.PHONY: up down build test lint logs clean

# Start all services
up:
	docker-compose up -d
	@echo "Services starting..."
	@echo "API: http://localhost:8000"
	@echo "Web: http://localhost:3000"
	@echo "n8n: http://localhost:5678"
	@echo "Grafana: http://localhost:3001"

# Stop all services
down:
	docker-compose down

# Build all services
build:
	docker-compose build

# Run tests
test:
	docker-compose exec api pytest /app/tests/
	docker-compose exec engine python -m pytest /app/tests/

# Run linting
lint:
	docker-compose exec api black /app --check
	docker-compose exec api flake8 /app
	docker-compose exec web npm run lint

# View logs
logs:
	docker-compose logs -f

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

# Seed demo data
seed:
	docker-compose exec api python /app/scripts/seed_demo_data.py

# Generate API docs
docs:
	docker-compose exec api python /app/scripts/generate_openapi.py
