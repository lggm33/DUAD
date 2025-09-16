.PHONY: help setup dev install-deps setup-env setup-db generate-keys generate-migration migrate run clean test lint check-deps

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
FLASK := flask
DATABASE_EXISTS := $(shell psql -U postgres -lqt | cut -d \| -f 1 | grep -qw ecommerce_backend && echo "true" || echo "false")
KEYS_EXIST := $(shell test -f keys/private_key.pem && test -f keys/public_key.pem && echo "true" || echo "false")
ENV_FILE := .env
VENV_DIR := venv

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)🛠️  Ecommerce Backend - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick start: make dev$(NC)"

setup: install-deps setup-env setup-db generate-keys migrate check-redis ## Complete project setup (idempotent)
	@echo "$(GREEN)✅ Project setup completed successfully!$(NC)"
	@echo "$(BLUE)💡 Run 'make run' to start the development server$(NC)"

dev: setup run ## Setup everything and start development server

install-deps: ## Install Python dependencies (idempotent)
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	@echo "$(BLUE)Using Python: python3$(NC)"
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "$(RED)❌ Python3 not found. Please install Python 3.10+ first$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(VENV_DIR)/bin/activate" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		python3 -m venv $(VENV_DIR); \
	fi
	@echo "$(BLUE)Activating virtual environment and installing dependencies...$(NC)"
	@. $(VENV_DIR)/bin/activate && \
		pip install --upgrade pip && \
		pip install -e . && \
		pip install cryptography
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

setup-env: ## Create .env file if it doesn't exist (idempotent)
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "$(BLUE)📝 Creating .env file...$(NC)"; \
		cp env.example $(ENV_FILE) 2>/dev/null || { \
			echo "$(YELLOW)⚠️  .env.example not found, creating basic .env...$(NC)"; \
			echo "DATABASE_URL=postgresql://ecommerce_user:ecommerce_2024_secure@localhost:5432/ecommerce_backend" > $(ENV_FILE); \
			echo "# Redis Cloud Configuration" >> $(ENV_FILE); \
			echo "REDIS_HOST=your-redis-cloud-endpoint.redislabs.com" >> $(ENV_FILE); \
			echo "REDIS_PORT=12345" >> $(ENV_FILE); \
			echo "REDIS_PASSWORD=your-redis-cloud-password" >> $(ENV_FILE); \
			echo "REDIS_USERNAME=default" >> $(ENV_FILE); \
			echo "REDIS_DECODE_RESPONSES=True" >> $(ENV_FILE); \
			echo "JWT_ACCESS_TOKEN_EXPIRES=900" >> $(ENV_FILE); \
			echo "JWT_REFRESH_TOKEN_EXPIRES=604800" >> $(ENV_FILE); \
			echo "FLASK_APP=wsgi.py" >> $(ENV_FILE); \
			echo "FLASK_DEBUG=true" >> $(ENV_FILE); \
		}; \
		echo "$(GREEN)✅ .env file created$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  .env file already exists, skipping...$(NC)"; \
	fi

setup-db: check-deps ## Setup database (idempotent)
	@echo "$(BLUE)🗄️  Setting up database...$(NC)"
	@if ! command -v psql >/dev/null 2>&1; then \
		echo "$(RED)❌ PostgreSQL not found. Please install PostgreSQL first$(NC)"; \
		echo "$(YELLOW)💡 Install with: brew install postgresql$(NC)"; \
		exit 1; \
	fi
	@if [ "$(DATABASE_EXISTS)" = "false" ]; then \
		echo "$(BLUE)Creating database and user...$(NC)"; \
		chmod +x setup_database.sh; \
		./setup_database.sh || { \
			echo "$(YELLOW)⚠️  Database setup had issues, but continuing...$(NC)"; \
		}; \
		echo "$(GREEN)✅ Database created$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Database already exists, skipping creation...$(NC)"; \
	fi

generate-keys: ## Generate JWT RSA keys (idempotent)
	@echo "$(BLUE)🔑 Generating JWT keys...$(NC)"
	@if [ "$(KEYS_EXIST)" = "false" ]; then \
		echo "$(BLUE)Creating RSA key pair...$(NC)"; \
		if [ -f "$(VENV_DIR)/bin/activate" ]; then \
			. $(VENV_DIR)/bin/activate && python3 generate_keys.py; \
		else \
			python3 generate_keys.py; \
		fi; \
		echo "$(GREEN)✅ Keys generated$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  JWT keys already exist, skipping generation...$(NC)"; \
	fi

generate-migration: install-deps setup-env ## Generate new database migration (usage: make generate-migration MSG="description")
	@echo "$(BLUE)📝 Generating new migration...$(NC)"
	@if [ -f "$(VENV_DIR)/bin/activate" ]; then \
		if [ -z "$(MSG)" ]; then \
			echo "$(RED)❌ Migration message required. Usage: make generate-migration MSG=\"description\"$(NC)"; \
			exit 1; \
		fi; \
		. $(VENV_DIR)/bin/activate && \
		export $$(cat $(ENV_FILE) | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' | sed 's/#.*//' | xargs) && \
		flask db migrate -m "$(MSG)" || { \
			echo "$(RED)❌ Migration generation failed$(NC)"; \
			exit 1; \
		}; \
		echo "$(GREEN)✅ Migration '$(MSG)' generated successfully$(NC)"; \
	else \
		echo "$(RED)❌ Virtual environment not found. Run 'make install-deps' first$(NC)"; \
		exit 1; \
	fi

migrate: install-deps setup-env ## Run database migrations (idempotent)
	@echo "$(BLUE)🔄 Running migrations...$(NC)"
	@if [ -f "$(VENV_DIR)/bin/activate" ]; then \
		. $(VENV_DIR)/bin/activate && \
		export $$(cat $(ENV_FILE) | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' | sed 's/#.*//' | xargs) && \
		flask db upgrade 2>/dev/null || { \
			echo "$(YELLOW)⚠️  No migrations to run or migration failed$(NC)"; \
		}; \
	else \
		echo "$(RED)❌ Virtual environment not found. Run 'make install-deps' first$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Migrations completed$(NC)"

run: ## Start the development server
	@echo "$(BLUE)🚀 Starting development server...$(NC)"
	@echo "$(YELLOW)💡 Press Ctrl+C to stop$(NC)"
	@if [ -f "$(VENV_DIR)/bin/activate" ]; then \
		. $(VENV_DIR)/bin/activate && \
		export $$(cat $(ENV_FILE) | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' | sed 's/#.*//' | xargs) && \
		flask run --host=127.0.0.1 --port=5001 --debug; \
	else \
		echo "$(RED)❌ Virtual environment not found. Run 'make install-deps' first$(NC)"; \
		exit 1; \
	fi

test: install-deps ## Run all tests with coverage report
	@echo "$(BLUE)🧪 Running all tests with coverage...$(NC)"
	@if [ -f "$(VENV_DIR)/bin/activate" ]; then \
		. $(VENV_DIR)/bin/activate && \
		pip install -e .[test] 2>/dev/null || echo "$(YELLOW)⚠️  Test dependencies already installed$(NC)" && \
		export $$(cat $(ENV_FILE) | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' | sed 's/#.*//' | xargs) && \
		python3 -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html:htmlcov || { \
			echo "$(RED)❌ Tests failed$(NC)"; \
			exit 1; \
		}; \
		echo "$(GREEN)✅ Tests completed successfully$(NC)"; \
		echo "$(BLUE)📊 HTML coverage report generated: htmlcov/index.html$(NC)"; \
	else \
		echo "$(RED)❌ Virtual environment not found. Run 'make install-deps' first$(NC)"; \
		exit 1; \
	fi

test-cache: install-deps check-redis ## Test cache functionality and performance
	@echo "$(BLUE)⚡ Testing cache functionality...$(NC)"
	@if [ -f "$(VENV_DIR)/bin/activate" ]; then \
		. $(VENV_DIR)/bin/activate && \
		pip install -e .[test] 2>/dev/null || echo "$(YELLOW)⚠️  Test dependencies already installed$(NC)" && \
		export $$(cat $(ENV_FILE) | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' | sed 's/#.*//' | xargs) && \
		python3 -m pytest tests/test_cache_functionality.py -v --tb=short -m cache || { \
			echo "$(RED)❌ Cache tests failed$(NC)"; \
			exit 1; \
		}; \
		echo "$(GREEN)✅ Cache tests completed successfully$(NC)"; \
		echo "$(BLUE)💡 Run with FLASK_DEBUG=true to see cache hit/miss logs$(NC)"; \
	else \
		echo "$(RED)❌ Virtual environment not found. Run 'make install-deps' first$(NC)"; \
		exit 1; \
	fi

lint: install-deps ## Run code linting
	@echo "$(BLUE)🔍 Running linter...$(NC)"
	@if [ -f "$(VENV_DIR)/bin/activate" ]; then \
		. $(VENV_DIR)/bin/activate && \
		python3 -m flake8 app/ --max-line-length=120 || echo "$(YELLOW)⚠️  Linter not installed$(NC)"; \
	else \
		echo "$(RED)❌ Virtual environment not found. Run 'make install-deps' first$(NC)"; \
		exit 1; \
	fi

clean: ## Clean temporary files and caches
	@echo "$(BLUE)🧹 Cleaning temporary files...$(NC)"
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-all: clean ## Clean everything including venv and database
	@echo "$(RED)🗑️  WARNING: This will remove virtual environment!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Removing virtual environment...$(NC)"; \
		rm -rf $(VENV_DIR); \
		echo "$(BLUE)Removing .env file...$(NC)"; \
		rm -f $(ENV_FILE); \
		echo "$(GREEN)✅ Complete cleanup done$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

check-deps: ## Check if required system dependencies are installed
	@echo "$(BLUE)🔍 Checking system dependencies...$(NC)"
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)❌ Python 3 not found$(NC)"; exit 1; }
	@command -v psql >/dev/null 2>&1 || { echo "$(YELLOW)⚠️  PostgreSQL not found. Install with: brew install postgresql$(NC)"; }
	@command -v redis-cli >/dev/null 2>&1 || { echo "$(YELLOW)⚠️  redis-cli not found. Install for testing: brew install redis$(NC)"; }
	@echo "$(GREEN)✅ All dependencies found$(NC)"

check-redis: setup-env ## Check Redis Cloud connection
	@echo "$(BLUE)🔍 Checking Redis Cloud connection...$(NC)"
	@if [ -f "$(ENV_FILE)" ]; then \
		export $$(cat $(ENV_FILE) | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' | sed 's/#.*//' | xargs); \
		if [ -z "$$REDIS_HOST" ] || [ -z "$$REDIS_PORT" ]; then \
			echo "$(RED)❌ Redis configuration missing in .env file$(NC)"; \
			echo "$(YELLOW)💡 Please configure REDIS_HOST, REDIS_PORT, and REDIS_PASSWORD in .env$(NC)"; \
			exit 1; \
		fi; \
		echo "$(BLUE)Connecting to Redis Cloud at $$REDIS_HOST:$$REDIS_PORT...$(NC)"; \
		if [ -n "$$REDIS_PASSWORD" ]; then \
			redis-cli -h "$$REDIS_HOST" -p "$$REDIS_PORT" -a "$$REDIS_PASSWORD" ping >/dev/null 2>&1 && { \
				echo "$(GREEN)✅ Redis Cloud connection successful$(NC)"; \
			} || { \
				echo "$(RED)❌ Failed to connect to Redis Cloud$(NC)"; \
				echo "$(YELLOW)💡 Please check your Redis Cloud credentials in .env file$(NC)"; \
				echo "$(YELLOW)   - REDIS_HOST=your-redis-cloud-endpoint$(NC)"; \
				echo "$(YELLOW)   - REDIS_PORT=your-redis-cloud-port$(NC)"; \
				echo "$(YELLOW)   - REDIS_PASSWORD=your-redis-cloud-password$(NC)"; \
				exit 1; \
			}; \
		else \
			redis-cli -h "$$REDIS_HOST" -p "$$REDIS_PORT" ping >/dev/null 2>&1 && { \
				echo "$(GREEN)✅ Redis Cloud connection successful$(NC)"; \
			} || { \
				echo "$(RED)❌ Failed to connect to Redis Cloud$(NC)"; \
				echo "$(YELLOW)💡 Please check your Redis Cloud credentials in .env file$(NC)"; \
				exit 1; \
			}; \
		fi; \
	else \
		echo "$(RED)❌ .env file not found. Run 'make setup-env' first$(NC)"; \
		exit 1; \
	fi

status: ## Show project status
	@echo "$(BLUE)📊 Project Status$(NC)"
	@echo "$(YELLOW)Virtual Environment:$(NC) $$(if [ -d "$(VENV_DIR)" ]; then echo "$(GREEN)✅ Created$(NC)"; else echo "$(RED)❌ Missing$(NC)"; fi)"
	@echo "$(YELLOW)Environment File:$(NC)    $$(if [ -f "$(ENV_FILE)" ]; then echo "$(GREEN)✅ Exists$(NC)"; else echo "$(RED)❌ Missing$(NC)"; fi)"
	@echo "$(YELLOW)Database:$(NC)            $$(if [ "$(DATABASE_EXISTS)" = "true" ]; then echo "$(GREEN)✅ Created$(NC)"; else echo "$(RED)❌ Missing$(NC)"; fi)"
	@echo "$(YELLOW)JWT Keys:$(NC)            $$(if [ "$(KEYS_EXIST)" = "true" ]; then echo "$(GREEN)✅ Generated$(NC)"; else echo "$(RED)❌ Missing$(NC)"; fi)"
	@echo "$(YELLOW)Redis Cloud:$(NC)         $$(if [ -f "$(ENV_FILE)" ]; then \
		export $$(cat $(ENV_FILE) | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' | sed 's/#.*//' | xargs); \
		if [ -n "$$REDIS_HOST" ] && [ -n "$$REDIS_PORT" ]; then \
			if [ -n "$$REDIS_PASSWORD" ]; then \
				redis-cli -h "$$REDIS_HOST" -p "$$REDIS_PORT" -a "$$REDIS_PASSWORD" ping >/dev/null 2>&1 && echo "$(GREEN)✅ Connected$(NC)" || echo "$(RED)❌ Connection Failed$(NC)"; \
			else \
				redis-cli -h "$$REDIS_HOST" -p "$$REDIS_PORT" ping >/dev/null 2>&1 && echo "$(GREEN)✅ Connected$(NC)" || echo "$(RED)❌ Connection Failed$(NC)"; \
			fi; \
		else \
			echo "$(YELLOW)⚠️  Not Configured$(NC)"; \
		fi; \
	else \
		echo "$(RED)❌ No Config$(NC)"; \
	fi)"
