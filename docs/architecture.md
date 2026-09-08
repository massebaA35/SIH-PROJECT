# NETRA Architecture

## System Overview

NETRA (Network Exploration, Threat & Relationship Analysis) is a crime investigation decision-support system. The frontend is a Vite single-page application. FastAPI exposes the investigator API. The demo data source is in-memory and deterministic so the graph and analytical story are always available. NetworkX calculates centrality metrics. Entity extraction is rule-based when external NLP is unavailable.

The intended production boundary is PostgreSQL for canonical evidence and review state, Neo4j for graph traversal, and a permissioned integrity ledger adapter for tamper-evident records. Every inferred relationship carries confidence, source, timestamp, case, and evidence metadata.

## Backend Architecture

### Core Modules

1. **main.py** - FastAPI application with RESTful endpoints
2. **config.py** - Centralized configuration management via environment variables
3. **data.py** - Synthetic data generation for demo mode
4. **logging_config.py** - Structured logging configuration
5. **ai/** - AI/ML modules for analysis:
   - entity_extraction.py: NLP entity recognition
   - network_analysis.py: Graph metrics (NetworkX)
   - explanation_engine.py: Insight generation
   - crime_dataset.py: Statistical analysis

### API Layer

**Key Endpoints:**
- Authentication: `/api/auth/login`
- Dashboard: `/api/dashboard`, `/api/cases`
- Graph: `/api/graph/case/{case_id}`
- Entities: `/api/entities`, `/api/entities/{entity_id}`
- Annotations: `/api/entities/{entity_id}/notes`, `/api/relationships/{rel_id}/notes`
- Review: `/api/review`, `/api/relationships/review`
- Documents: `/api/documents/upload`, `/api/evidence/{evidence_id}/verify`
- Reports: `/api/reports/generate`

### Data Persistence

**Synthetic Mode (Default)**
- In-memory data structures
- Deterministic graph generation
- Perfect for demos and testing

**Database Mode (Production)**
- PostgreSQL for relational data
- Persistent entity and relationship storage
- SQL-based search and aggregation

**Graph Mode (Advanced)**
- Neo4j for relationship storage
- Optimized graph traversal queries
- Built-in community detection

## Frontend Architecture

### Technology Stack
- React 18 with Hooks
- Vite for bundling
- Cytoscape.js for graph visualization
- Leaflet for geographic maps
- Tailwind CSS for styling
- Lucide Icons for UI

### Component Hierarchy
```
App
├── Header (Navigation, Auth)
├── Sidebar (Case Selection, Filters)
├── MainView
│   ├── Dashboard (KPIs, Alerts)
│   ├── GraphView (Cytoscape)
│   ├── EntityProfile (Drawer)
│   ├── Timeline (Event List)
│   ├── ReviewPanel (Relationship Approval)
│   └── DocumentUpload (Evidence)
└── Footer (Status, Version)
```

### State Management
- React Context for global state
- Hooks for component logic
- Local storage for UI preferences
- API services for backend communication

## Integration Modes

Set via `INTEGRATION_MODE` environment variable:

**synthetic** (Default)
- No external dependencies
- Fast performance
- Ideal for demos

**database**
- PostgreSQL backend
- Persistent data storage
- SQL-based queries

**neo4j**
- Graph database backend
- Optimized relationship queries
- Community detection

## Security Architecture

### Authentication
- JWT tokens for session management
- Demo credentials for testing (admin/netra-demo)
- Configurable token expiration

### Data Protection
- SHA-256 hashing for evidence integrity
- Input validation on all endpoints
- File type and size validation
- CORS middleware for cross-origin requests

### API Security
- Request validation using Pydantic models
- Error handling without information leakage
- Rate limiting recommended for production

## Scalability Considerations

### Horizontal Scaling
- Stateless API design
- Load balancer support
- Shared database backend
- Multiple frontend instances

### Vertical Scaling
- Server resource increases
- Database connection pooling
- Caching for frequent queries
- Query optimization and indexing

### Performance Optimization
- Lazy loading for graph visualization
- Pagination for entity search
- Database indexing on common fields
- Response compression (gzip)

## Extension Points

### Adding Analysis Modules
1. Create `backend/app/ai/new_module.py`
2. Add API endpoint in `main.py`
3. Create frontend component in React
4. Update documentation

### Adding Database Support
1. Create repository pattern classes
2. Update `config.py` with connection settings
3. Implement data access methods
4. Update main.py to use repositories

### Adding New Entity Types
1. Extend entity types in `data.py`
2. Add frontend filters/UI
3. Update extraction logic
4. Document in API reference

## Monitoring & Operations

### Logging
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Structured logging with timestamps
- Component-level logger instances
- Production-ready log aggregation support

### Health Checks
- `/api/health` endpoint shows system status
- Database connectivity status
- Neo4j availability check
- Integration mode verification

### Performance Metrics
- API response time tracking
- Database query latency
- Graph computation benchmarks
- Document upload statistics
- User session duration

## Deployment Targets

- **Local**: Development with hot reload
- **Docker**: Containerized application stack
- **Docker Compose**: Full stack with optional databases
- **Kubernetes**: Container orchestration
- **Cloud Platforms**: AWS, GCP, Azure, Heroku
- **On-Premise**: Linux servers with Nginx reverse proxy

## Development Workflow

1. **Local Setup**: See DEPLOYMENT.md
2. **Code Changes**: Make modifications to backend/frontend
3. **Testing**: Run pytest for backend, npm test for frontend
4. **API Testing**: Use http://localhost:8000/docs (Swagger UI)
5. **Commit**: Push to version control
6. **Deploy**: Run docker-compose or cloud deployment

## Future Enhancements

- Advanced NLP with transformer models (spaCy, Hugging Face)
- PDF report generation
- Real-time collaboration features
- Mobile app support
- Advanced search with Elasticsearch
- Machine learning model integration
- Audit logging for compliance
- Multi-language support
