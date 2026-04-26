# Development Guide - Nexus Backend v2.0

## Quick Start

```bash
# Clone and setup
cd backend_v2
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Run development server
python main.py

# Server at http://localhost:8000
# API docs at http://localhost:8000/docs
# ReDoc at http://localhost:8000/redoc
```

## Architecture Overview

### Layered Architecture

```
┌─────────────────────────────────────┐
│      HTTP API Layer (FastAPI)       │  api/routes.py
├─────────────────────────────────────┤
│     Application/Agent Layer         │  agents/*.py
├─────────────────────────────────────┤
│        Business Logic Layer         │  services/*.py
├─────────────────────────────────────┤
│       Data Access Layer             │  repositories/*.py
├─────────────────────────────────────┤
│   Infrastructure/Core Layer         │  core/*.py
└─────────────────────────────────────┘
```

### Key Components

**1. Domain Layer (`core/domain.py`)**
- Pydantic models for type safety
- Enums for constants (Language, Crop, Soil types)
- Data classes for requests/responses
- No business logic - pure data structures

**2. Service Layer (`services/*.py`)**
- Encapsulates external integrations
- Handles retry logic and caching
- Manages resource lifecycle
- Examples:
  - `LLMService`: OpenAI with retry/timeout
  - `CacheService`: Redis/Memory abstraction
  - `SpeechService`: Sarvam AI STT/TTS
  - `WeatherService`: Open-Meteo integration

**3. Repository Layer (`repositories/*.py`)**
- Data access abstraction
- Query builders and filters
- Database connection management
- Examples:
  - `FarmerRepository`: User profiles
  - `SchemeRepository`: Scheme search
  - `InteractionRepository`: Chat history

**4. Agent Layer (`agents/*.py`)**
- Business logic for recommendations
- Multi-turn conversations
- Stateless, pure functions
- Examples:
  - `CropSowingAgent`: Crop recommendations with ICAR scoring
  - `SchemeNavigatorAgent`: Scheme search and form collection

**5. API Layer (`api/routes.py`)**
- HTTP endpoints
- Request/response validation
- Error handling
- Session management

**6. Core Infrastructure (`core/*.py`)**
- Configuration management
- Structured logging
- Exception hierarchy
- Dependency injection container
- Utilities and helpers

## Design Patterns Used

### 1. Dependency Injection

**Pattern:** Constructor injection with container management

```python
class CropSowingAgent:
    def __init__(
        self,
        llm_service: LLMService,
        weather_service: WeatherService,
        gis_service: GISService,
    ):
        self.llm = llm_service
        self.weather = weather_service
        self.gis = gis_service
```

**Benefits:**
- Easy to test (mock dependencies)
- Loose coupling between components
- Container manages lifecycle
- Easy to swap implementations

### 2. Repository Pattern

**Pattern:** Abstract data access behind repository interface

```python
class SchemeRepository:
    async def search(self, query, state, category, limit):
        # Database query logic
        pass

    async def vector_search(self, embedding, state, limit):
        # Vector DB search logic
        pass
```

**Benefits:**
- Decouple business logic from data access
- Easy to switch databases
- Testable with mock repositories
- Centralized query logic

### 3. Service Locator Pattern

**Pattern:** Central container for service management

```python
container = get_container()
service = await container.get("service_name")
```

**Benefits:**
- Single point of service registration
- Lazy loading of services
- Lifecycle management
- Easy to add new services

### 4. Async/Await Pattern

**Pattern:** All I/O operations are async

```python
async def fetch_weather(self, lat, lon):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return WeatherData(...)
```

**Benefits:**
- Handle multiple concurrent requests
- Efficient resource utilization
- Non-blocking operations
- Better performance under load

## Development Workflow

### 1. Adding a New Service

**Step 1: Define the service class**
```python
# services/my_service.py
class MyService:
    def __init__(self, config, dependency):
        self.config = config
        self.dependency = dependency
    
    async def my_method(self, input_data):
        # Business logic
        result = await self.dependency.process(input_data)
        return result
```

**Step 2: Add logging**
```python
from core.logging import get_logger
logger = get_logger(__name__)

async def my_method(self, input_data):
    logger.info(f"Processing {input_data}")
    try:
        result = await self.process(input_data)
        logger.info(f"Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
```

**Step 3: Add error handling**
```python
from core.exceptions import ApplicationException, ExternalServiceException

async def my_method(self, input_data):
    try:
        result = await external_api.call(input_data)
    except Exception as e:
        raise ExternalServiceException(
            message="Failed to fetch data",
            details={"error": str(e)}
        )
```

**Step 4: Register in container**
```python
# core/container.py
async def setup_container():
    my_service = MyService(settings, dependency)
    container.register_singleton("my_service", my_service)
```

**Step 5: Use dependency injection**
```python
# In agents or routes
def __init__(self, my_service: MyService):
    self.my_service = my_service
```

### 2. Adding a New Endpoint

**Step 1: Define request/response models**
```python
# api/routes.py
from pydantic import BaseModel

class MyRequest(BaseModel):
    field1: str
    field2: int

class MyResponse(BaseModel):
    result: str
    status: str
```

**Step 2: Create the endpoint**
```python
@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    session_id = str(uuid4())
    logger.info(f"[{session_id}] Processing request")
    
    try:
        container = get_container()
        service = await container.get("my_service")
        result = await service.process(request.field1)
        
        return MyResponse(
            result=result,
            status="success"
        )
    except ApplicationException as e:
        logger.error(f"[{session_id}] {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
```

**Step 3: Add tests**
```python
# tests/test_routes.py
@pytest.mark.asyncio
async def test_my_endpoint():
    client = TestClient(app)
    response = client.post(
        "/my-endpoint",
        json={"field1": "value", "field2": 42}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### 3. Adding a New Agent

**Step 1: Create agent class with DI**
```python
# agents/my_agent.py
class MyAgent:
    def __init__(
        self,
        llm_service: LLMService,
        other_service: OtherService,
    ):
        self.llm = llm_service
        self.other = other_service
    
    async def process(self, request: MyRequest):
        # Use injected services
        result = await self.llm.invoke(messages)
        return result
```

**Step 2: Register in container**
```python
# core/container.py
my_agent = MyAgent(llm_service, other_service)
container.register_singleton("my_agent", my_agent)
```

**Step 3: Use in routes**
```python
# api/routes.py
@router.post("/my-agent-endpoint")
async def use_agent(request: Request):
    container = get_container()
    agent = await container.get("my_agent")
    result = await agent.process(request)
    return result
```

## Testing

### Unit Tests

**Test structure:**
```python
# tests/test_my_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_dependency():
    return AsyncMock()

@pytest.fixture
def my_service(mock_dependency):
    return MyService(MagicMock(), mock_dependency)

@pytest.mark.asyncio
async def test_my_service_success(my_service, mock_dependency):
    mock_dependency.process = AsyncMock(return_value="result")
    
    result = await my_service.my_method("input")
    
    assert result == "result"
    mock_dependency.process.assert_called_once_with("input")

@pytest.mark.asyncio
async def test_my_service_error(my_service, mock_dependency):
    mock_dependency.process = AsyncMock(
        side_effect=Exception("Test error")
    )
    
    with pytest.raises(ApplicationException):
        await my_service.my_method("input")
```

**Run tests:**
```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_my_service.py -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run with markers
pytest -m "not slow"
```

### Integration Tests

**Test databases and external services:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_integration(database_service):
    # Create test data
    result = await database_service.insert(
        "users",
        {"name": "Test", "email": "test@example.com"}
    )
    
    # Query and verify
    user = await database_service.get_one("users", {"id": result["id"]})
    assert user["name"] == "Test"
```

## Logging

### Structured Logging Format

All logs are JSON-formatted for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "services.weather_service",
  "message": "Fetching weather data",
  "latitude": 22.7196,
  "longitude": 75.8577,
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Logging Best Practices

```python
from core.logging import get_logger

logger = get_logger(__name__)

# Info - normal operations
logger.info("Processing request", extra={"user_id": user_id})

# Warning - recoverable errors
logger.warning("Cache miss for key", extra={"key": cache_key})

# Error - errors that should be monitored
logger.error("Database query failed", exc_info=True)

# Debug - development information
logger.debug("Variable value", extra={"value": result})
```

### Access Logs

View logs in real-time:
```bash
# All logs
docker-compose logs -f backend

# Specific service
docker-compose logs -f postgres

# Follow and grep
docker-compose logs -f backend | grep "ERROR"
```

## Configuration Management

### Environment Variables

All configuration via `.env` file:

```env
# Application
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=DEBUG

# Cache
CACHE_BACKEND=redis
CACHE_TTL_SECONDS=3600

# Database
SUPABASE_URL=https://project.supabase.co
SUPABASE_KEY=ey...

# LLM
OPENAI_API_KEY=sk-...

# Speech
SARVAM_API_KEY=...
```

### Configuration Access

```python
from core.config import get_settings

settings = get_settings()

# Access config values
api_key = settings.openai_api_key
cache_ttl = settings.cache_ttl_seconds
is_prod = settings.is_production
```

## Performance Optimization

### Caching Strategy

```python
# Cache for 1 hour
result = await cache_service.get("key")
if not result:
    result = await expensive_operation()
    await cache_service.set("key", result, ttl=3600)
```

### Database Indexing

```sql
-- Composite index for scheme search
CREATE INDEX idx_scheme_state_category 
  ON schemes (state, category);

-- Vector index for embeddings
CREATE INDEX idx_scheme_embedding 
  ON schemes USING ivfflat (embedding vector_cosine_ops);
```

### Connection Pooling

```python
# Automatic connection pooling in services
database_service = await DatabaseService.create(settings)
# Connection pool configured automatically
```

## Debugging

### Debug Breakpoints

```python
# In VSCode, set breakpoint and run with debugger
# Or use pdb
import pdb; pdb.set_trace()

# Or use logging for non-interactive debugging
logger.debug(f"Variable: {variable}", extra={"full_object": obj})
```

### Common Issues

**Issue: "Service not found in container"**
- Solution: Register service in `core/container.py`
- Check service name matches exactly

**Issue: "Async context manager not set up"**
- Solution: Make sure service has `__aenter__` and `__aexit__`
- Or use manual setup/teardown

**Issue: "Type hints not working"**
- Solution: Use `from typing import Optional, List`
- Make sure imports are at top of file

## Deployment Checklist

- [ ] Update version in `main.py`
- [ ] Run full test suite: `pytest --cov`
- [ ] Build Docker image: `docker build -t nexus:v2.0.0 .`
- [ ] Test Docker image locally
- [ ] Update environment variables for production
- [ ] Test database migrations
- [ ] Set up monitoring and alerting
- [ ] Configure SSL/HTTPS
- [ ] Set up log aggregation
- [ ] Test disaster recovery procedures
- [ ] Create deployment rollback plan
- [ ] Document any breaking changes

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)

## Support

For questions or issues:
1. Check README.md for overview
2. Check API_DOCUMENTATION.yaml for API details
3. Review similar implementations in codebase
4. Check logs for error details
5. Ask team lead or create GitHub issue
