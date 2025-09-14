# 🐍 Local Development Setup Guide

## Prerequisites

1. **Python 3.11** installed: https://www.python.org/downloads/
2. **Docker Desktop** installed: https://www.docker.com/products/docker-desktop/

## Manual Setup (Step by Step)

### Step 1: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Linux/Mac)
source venv/bin/activate
```

### Step 2: Install Requirements
```bash
# Install all service requirements
pip install -r services/user-service/requirements.txt
pip install -r services/product-service/requirements.txt
pip install -r services/order-service/requirements.txt
pip install -r services/api-gateway/requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio httpx
```

### Step 3: Start External Services
```bash
# Start PostgreSQL, Redis, and RabbitMQ
docker-compose up postgres redis rabbitmq -d

# Check if they're running
docker-compose ps
```

### Step 4: Start Each Service

**Manual commands**
```bash
# Terminal 1 - User Service
call venv\Scripts\activate.bat
cd services\user-service
uvicorn app.main:app --host 0.0.0.0 --port 8031 --reload

# Terminal 2 - Product Service
call venv\Scripts\activate.bat
cd services\product-service
uvicorn app.main:app --host 0.0.0.0 --port 8032 --reload

# Terminal 3 - Order Service
call venv\Scripts\activate.bat
cd services\order-service
uvicorn app.main:app --host 0.0.0.0 --port 8033 --reload

# Terminal 4 - API Gateway
call venv\Scripts\activate.bat
cd services\api-gateway
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Service URLs

Once all services are running:
- **API Gateway**: http://localhost:8000
- **User Service**: http://localhost:8031
- **Product Service**: http://localhost:8032
- **Order Service**: http://localhost:8033
- **RabbitMQ Management**: http://localhost:15672 (app/app)
- **PostgreSQL**: localhost:5432 (app/app/appdb)
- **Redis**: localhost:6379


## Troubleshooting

### Services won't start
1. Check if virtual environment is activated
2. Check if all requirements are installed
3. Check if external services (PostgreSQL, Redis, RabbitMQ) are running

### Database connection errors
1. Make sure PostgreSQL is running: `docker-compose ps`
2. Check database URL in environment variables

### Port conflicts
1. Make sure no other services are using ports 8000-8003
2. Check with: `netstat -an | findstr :8000`

## Development Tips

1. **Hot Reload**: All services run with `--reload` flag for automatic restart on code changes
2. **Logs**: Check terminal output for each service for debugging
3. **API Documentation**: Visit http://localhost:8000/docs for interactive API docs
4. **Database**: Use pgAdmin or any PostgreSQL client to connect to localhost:5432

## Stopping Services

```bash
# Stop external services
docker-compose down

# Stop individual services
# Press Ctrl+C in each terminal window
```


