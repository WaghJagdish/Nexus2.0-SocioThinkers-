# Nexus Agricultural Advisory API v2.0

Production-grade backend for agricultural recommendations and government scheme navigation using multi-agent orchestration.

## Architecture Overview

**Tech Stack:**
- **FastAPI** - Async HTTP framework
- **LangGraph** - Multi-agent orchestration
- **LangChain** - LLM integration
- **Supabase** - PostgreSQL + pgvector for semantic search
- **Redis** - Optional caching layer
- **Sarvam AI** - Speech synthesis/recognition for 11 Indian languages
- **Open-Meteo** - Weather data (free, no API key required)
- **ISRO Bhuvan** - GIS and soil data

**Core Patterns:**
- Dependency Injection for loose coupling
- Repository pattern for data access
- Service layer for business logic
- Clean Architecture with clear separation of concerns
- Structured JSON logging for production observability

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 13+ (or Supabase account)
- Redis (optional, for caching)
- Docker & Docker Compose (optional)

### Local Development Setup

```bash
cd backend_v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your API keys:
# - OPENAI_API_KEY
# - SARVAM_API_KEY
# - SUPABASE_URL
# - SUPABASE_KEY

# Run migrations (if using Supabase)
# Database schema should be set up in Supabase

# Start development server
python main.py
```

Server runs on `http://localhost:8000`

### Docker Setup

```bash
# Build and run with docker-compose
docker-compose up --build

# First run: initialize database
docker-compose exec backend python scripts/init_db.py
```

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### 1. Text Query Endpoint
**POST** `/text/query`

Request:
```json
{
  "user_id": "farmer_123",
  "text": "What should I grow in Indore?",
  "latitude": 22.7196,
  "longitude": 75.8577,
  "device_language": "hi"
}
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "response_text": "आपके क्षेत्र में गेहूं और सोयाबीन उगाने के लिए अच्छे हैं...",
  "recommended_crop": "wheat",
  "matched_schemes": [
    {
      "id": "scheme_123",
      "name": "PM-KISAN",
      "benefits": "₹6000 per year"
    }
  ]
}
```

### 2. Voice Input Endpoint
**POST** `/voice/sync`

Request (multipart/form-data):
```
- audio_file: <audio_file.wav>
- user_id: farmer_123
- latitude: 22.7196
- longitude: 75.8577
- device_language: hi
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "response_text": "आपके क्षेत्र में गेहूं उगाने के लिए अच्छे समय में...",
  "response_audio_url": "https://nexus.example.com/audio/550e8400.mp3",
  "recommended_crop": "wheat",
  "generated_pdf_url": "https://nexus.example.com/pdfs/550e8400.pdf"
}
```

### 3. Health Check Endpoint
**GET** `/health`

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "services": {
    "database": "healthy",
    "llm": "healthy",
    "cache": "healthy"
  }
}
```

## Supported Languages

The API supports 11 Indian languages:
- `hi` - Hindi
- `mr` - Marathi
- `gu` - Gujarati
- `te` - Telugu
- `ta` - Tamil
- `kn` - Kannada
- `ml` - Malayalam
- `pa` - Punjabi
- `bn` - Bengali
- `as` - Assamese
- `en` - English

## Configuration

Edit `.env` file or environment variables:

```env
# Application
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Cache
CACHE_BACKEND=memory  # or 'redis'
CACHE_TTL_SECONDS=3600
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_MAX_SIZE=1000

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# Speech Services
SARVAM_API_KEY=...

# CORS
CORS_ORIGINS=["http://localhost:3000","https://example.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

## Project Structure

```
backend_v2/
├── core/
│   ├── config.py          # Configuration management
│   ├── logging.py         # Structured logging setup
│   ├── exceptions.py      # Exception hierarchy
│   ├── container.py       # Dependency injection
│   └── domain.py          # Domain models & enums
├── services/
│   ├── llm_service.py     # OpenAI integration with retry logic
│   ├── database_service.py # Supabase abstraction
│   ├── cache_service.py   # Redis/Memory caching
│   ├── speech_service.py  # Sarvam AI STT/TTS
│   ├── weather_service.py # Open-Meteo weather data
│   ├── gis_service.py     # Soil & land-use data
│   └── scheme_service.py  # Scheme search & retrieval
├── repositories/
│   ├── farmer_repository.py       # Farmer profile CRUD
│   ├── interaction_repository.py  # Interaction logging
│   └── scheme_repository.py       # Scheme queries
├── agents/
│   ├── crop_agent.py      # Crop recommendations (ICAR scoring)
│   └── scheme_agent.py    # Scheme navigation & form collection
├── api/
│   └── routes.py          # FastAPI endpoints
├── tests/
│   ├── conftest.py
│   ├── test_crop_agent.py
│   ├── test_services.py
│   └── test_routes.py
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── Dockerfile            # Container image definition
└── docker-compose.yml    # Multi-container orchestration
```

## Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_crop_agent.py -v

# With asyncio support
pytest tests/ -v --asyncio-mode=auto
```

## Development Workflow

### Adding a New Service

1. Create service class in `services/`:
```python
class MyService:
    def __init__(self, config, cache):
        self.config = config
        self.cache = cache
    
    async def my_method(self):
        pass
```

2. Register in `core/container.py`:
```python
my_service = MyService(settings, cache_service)
container.register_singleton("my_service", my_service)
```

3. Inject into agents/routes via constructor

### Adding a New Endpoint

1. Create route in `api/routes.py`:
```python
@router.post("/my-endpoint")
async def my_endpoint(request_data: MyRequest):
    container = get_container()
    service = await container.get("my_service")
    result = await service.process(request_data)
    return MyResponse(result)
```

2. Add request/response models with Pydantic
3. Add exception handlers for service errors
4. Write tests in `tests/test_routes.py`

## Debugging & Monitoring

### Structured Logging

All logs are JSON-formatted for easy parsing:
```json
{"timestamp":"2024-01-15T10:30:00Z","level":"INFO","message":"Recommending crops","user_id":"farmer_123"}
```

### Request Tracing

Every request has a `session_id` that appears in logs and responses for end-to-end tracing.

### Error Codes

Standardized error codes for client handling:
- `VALIDATION_ERROR` - Input validation failed
- `TRANSCRIPTION_FAILED` - Speech-to-text error
- `SYNTHESIS_FAILED` - Text-to-speech error
- `AGENT_ERROR` - Agent processing failed
- `DATABASE_ERROR` - Database operation failed
- `EXTERNAL_API_ERROR` - Third-party service failed
- `TIMEOUT` - Request exceeded timeout
- `RATE_LIMIT_EXCEEDED` - Too many requests

## Performance Optimizations

**Caching Strategy:**
- Weather data: 1 hour TTL
- Scheme search results: 24 hours TTL
- Crop recommendations: 6 hours TTL (varies by location)
- LLM responses: 24 hours TTL

**Database Indexing:**
- pgvector indexes on scheme embeddings
- Composite index on (state, category) for schemes
- Index on user_id for interactions

**Async Operations:**
- All I/O is async (database, API calls, file operations)
- Connection pooling for PostgreSQL
- Redis connection reuse

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `CORS_ORIGINS` with specific domains
- [ ] Enable `RATE_LIMIT_ENABLED=true`
- [ ] Set up monitoring/alerting
- [ ] Configure automated backups for Supabase
- [ ] Review CloudFlare/CDN configuration
- [ ] Test disaster recovery procedures

### Scaling Strategies

1. **Horizontal Scaling:**
   - Run multiple backend instances behind load balancer
   - Use shared Redis for caching
   - Use managed Supabase (auto-scaling)

2. **Caching:**
   - Pre-compute crop recommendations for grid locations
   - Cache scheme data in Redis
   - Use CDN for static assets

3. **Database:**
   - Enable read replicas for scale
   - Archive old interactions to cold storage
   - Vacuum tables regularly

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Follow PEP 8 style guide
3. Add tests for new functionality
4. Submit pull request with description

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: [Link]
- Email: support@nexus.example.com
- Documentation: [Link]
