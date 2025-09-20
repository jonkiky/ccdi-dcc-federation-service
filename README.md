# CCDI Federation Service

A REST API service for querying the CCDI (Childhood Cancer Data Initiative) graph database. This service provides endpoints for retrieving subjects, samples, files, and metadata from a Memgraph graph database.

## Features

- **REST API**: FastAPI-based service with automatic OpenAPI documentation
- **Graph Database**: Memgraph integration with Cypher query support  
- **Caching**: Redis-based caching for count and summary endpoints
- **Pagination**: RFC 5988 compliant pagination with Link headers
- **Field Validation**: Allowlist-based field filtering for security
- **Error Handling**: Comprehensive error handling matching OpenAPI specification
- **Logging**: Structured logging with correlation IDs
- **Docker Support**: Full Docker Compose setup for development
- **Type Safety**: Full Pydantic models and type hints

## Architecture

```
├── app/
│   ├── api/v1/               # API layer
│   │   ├── deps.py          # FastAPI dependencies
│   │   └── endpoints/       # Route handlers
│   ├── core/                # Core utilities
│   │   ├── config.py        # Configuration management
│   │   ├── logging.py       # Structured logging
│   │   ├── pagination.py    # Pagination utilities
│   │   └── cache.py         # Redis caching
│   ├── db/                  # Database layer
│   │   └── memgraph.py      # Memgraph connection
│   ├── lib/                 # Shared libraries
│   │   ├── cypher_builder.py # Query construction
│   │   └── field_allowlist.py # Field validation
│   ├── models/              # Data models
│   │   ├── dto.py           # Pydantic models
│   │   └── errors.py        # Error classes
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic layer
│   └── main.py              # Application entry point
```

## API Endpoints

### Subjects

- `GET /api/v1/subject` - List subjects with pagination and filtering
- `GET /api/v1/subject/{org}/{ns}/{name}` - Get specific subject by identifier
- `GET /api/v1/subject/by/{field}/count` - Count subjects by field value
- `GET /api/v1/subject/summary` - Get subject summary statistics
- `GET /api/v1/subject/diagnosis/search` - Search subjects by diagnosis
- `GET /api/v1/subject/diagnosis/by/{field}/count` - Count subjects by field with diagnosis
- `GET /api/v1/subject/diagnosis/summary` - Subject summary with diagnosis filtering

### Health

- `GET /health` - Service health check
- `GET /` - Service information

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ccdi-dcc-federation-service
   ```

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the services**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Memgraph Lab: http://localhost:3000
   - Redis: localhost:6379

### Manual Setup

#### Option 1: Using Poetry (Recommended)

1. **Install dependencies**:
   ```bash
   pip install poetry
   poetry install
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start external services**:
   ```bash
   # Start Memgraph
   docker run -p 7687:7687 -p 7444:7444 memgraph/memgraph:2.11.1

   # Start Redis (optional, for caching)
   docker run -p 6379:6379 redis:7.2-alpine
   ```

4. **Run the application**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

#### Option 2: Using Virtual Environment

1. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start external services**:
   ```bash
   # Start Memgraph
   docker run -p 7687:7687 -p 7444:7444 memgraph/memgraph:2.11.1

   # Start Redis (optional, for caching)
   docker run -p 6379:6379 redis:7.2-alpine
   ```

5. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Deactivate virtual environment when done**:
   ```bash
   deactivate
   ```

## Configuration

The service uses environment variables for configuration. See `.env.example` for all available options.

### Key Configuration Sections

#### Database (Memgraph)
```bash
DB_URI=bolt://localhost:7687
DB_USER=
DB_PASSWORD=
DB_DATABASE=memgraph
```

#### Cache (Redis)
```bash
CACHE_ENABLED=true
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_COUNT_TTL=300
```

#### CORS
```bash
CORS_ENABLED=true
CORS_ALLOWED_ORIGINS=["http://localhost:3000"]
```

## Development

### Project Structure

The service follows a layered architecture:

1. **API Layer** (`app/api/`): Route handlers and dependencies
2. **Service Layer** (`app/services/`): Business logic and caching
3. **Repository Layer** (`app/repositories/`): Data access with Cypher queries
4. **Database Layer** (`app/db/`): Connection management

### Adding New Endpoints

1. **Create repository** in `app/repositories/`
2. **Create service** in `app/services/`
3. **Add routes** in `app/api/v1/endpoints/`
4. **Update models** in `app/models/dto.py`
5. **Include router** in `app/main.py`

### Code Quality

The project uses several tools for code quality:

```bash
# Format code
poetry run black app/

# Lint code
poetry run ruff check app/

# Type check
poetry run mypy app/

# Run tests
poetry run pytest
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_subjects.py
```

## Data Model

The service works with the following entities:

### Subject
```python
{
  "id": "string",
  "identifiers": ["org.namespace.name"],
  "sex": "string",
  "race": "string", 
  "ethnicity": "string",
  "vital_status": "string",
  "age_at_vital_status": "string",
  "depositions": ["string"],
  "metadata": {...}
}
```

### Sample
```python
{
  "id": "string",
  "identifiers": ["string"],
  "disease_phase": "string",
  "anatomical_sites": ["string"],
  "tissue_type": "string",
  # ... additional fields
}
```

### File
```python
{
  "id": "string", 
  "identifiers": ["string"],
  "type": "string",
  "size": "integer",
  "checksums": {...},
  "description": "string"
}
```

## Filtering

All list endpoints support filtering through query parameters:

```bash
# Filter subjects by sex
GET /api/v1/subject?sex=Male

# Filter with multiple parameters
GET /api/v1/subject?sex=Male&race=White

# Filter with unharmonized metadata
GET /api/v1/subject?metadata.unharmonized.custom_field=value
```

## Pagination

All list endpoints support pagination:

```bash
# Get second page with 50 items per page
GET /api/v1/subject?page=2&per_page=50
```

Response includes RFC 5988 compliant Link header:
```
Link: <http://localhost:8000/api/v1/subject?page=1&per_page=20>; rel="prev",
      <http://localhost:8000/api/v1/subject?page=3&per_page=20>; rel="next"
```

## Error Handling

The API returns structured error responses:

```json
{
  "error_code": "INVALID_PARAMETERS",
  "message": "Invalid pagination parameters",
  "details": {
    "page": "Must be a positive integer",
    "per_page": "Cannot exceed maximum of 100"
  }
}
```

## Monitoring

### Health Checks

```bash
# Basic health check
GET /health

# Returns: {"status": "healthy", "service": "ccdi-federation-service"}
```

### Logging

The service provides structured JSON logging:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO", 
  "message": "Request completed",
  "path": "/api/v1/subject",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 45
}
```

## Deployment

### Production Environment

1. **Build Docker image**:
   ```bash
   docker build -t ccdi-federation-service .
   ```

2. **Run with production settings**:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e APP_DEBUG=false \
     -e DB_URI=bolt://your-memgraph:7687 \
     ccdi-federation-service
   ```

### Kubernetes

Example deployment configuration available in `k8s/` directory.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:

- Create an issue in the repository
- Contact the CCDI team
- Check the API documentation at `/docs`
