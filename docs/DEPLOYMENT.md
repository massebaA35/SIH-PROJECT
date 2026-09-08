# NETRA Deployment Guide

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git

### Local Setup

1. **Clone repository and install dependencies:**
   ```bash
   cd nexaura
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   npm install --prefix frontend
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env as needed (defaults work for development)
   ```

3. **Run backend:**
   ```bash
   $env:PYTHONPATH = "backend"
   uvicorn app.main:app --app-dir backend --reload --port 8000
   ```

4. **Run frontend** (in another terminal):
   ```bash
   npm run dev --prefix frontend
   ```

5. **Access application:**
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs
   - Credentials: `admin` / `netra-demo`

## Docker Deployment

### Basic Setup (Synthetic Demo)

```bash
docker compose up --build
```

This starts:
- Frontend at http://localhost:5173
- Backend API at http://localhost:8000

### Full Setup with Databases

```bash
docker compose up --build --profile full
```

This also starts:
- PostgreSQL database (localhost:5432)
- Neo4j graph database (localhost:7687)

**Note:** Update `.env` with database connection strings before running.

## Production Deployment

### Environment Configuration

Create `.env.production` with production values:

```env
NETRA_ENV=production
DEBUG=false

BACKEND_PORT=8000
FRONTEND_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com

JWT_SECRET=your-long-random-secret-key-here-min-32-chars

DATABASE_URL=postgresql://user:password@db-host:5432/netra_prod
NEO4J_URI=bolt://neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure-password

MAX_UPLOAD_SIZE_MB=50
INTEGRATION_MODE=database
LOG_LEVEL=WARNING
```

### Backend Deployment Options

#### Option 1: Docker Container
```bash
docker build -t netra-backend ./backend
docker run -p 8000:8000 --env-file .env.production netra-backend
```

#### Option 2: Kubernetes
```bash
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

#### Option 3: Cloud Platform
Deploy to AWS ECS, Google Cloud Run, or Azure Container Instances:
```bash
gcloud run deploy netra-backend --source ./backend --port 8000
```

### Frontend Deployment

#### Option 1: Docker Container
```bash
docker build -t netra-frontend ./frontend
docker run -p 5173:80 netra-frontend
```

#### Option 2: Static Hosting (AWS S3 + CloudFront, Netlify, Vercel)
```bash
npm run build --prefix frontend
# Deploy the 'frontend/dist' directory to your static hosting
```

#### Option 3: Node.js Server
```bash
npm install -g serve
npm run build --prefix frontend
serve -s frontend/dist -l 3000
```

## Database Setup

### PostgreSQL

```bash
createdb netra_prod
psql netra_prod < schema.sql
```

(See `backend/db/schema.sql` for schema)

### Neo4j

Access Neo4j at http://localhost:7687 (if running locally)

Initialize with:
```cypher
CREATE CONSTRAINT ON (p:Person) ASSERT p.id IS UNIQUE;
CREATE CONSTRAINT ON (o:Organization) ASSERT o.id IS UNIQUE;
CREATE INDEX ON (:Person, :Organization)(name);
```

## Reverse Proxy Configuration

### Nginx Example
```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:5173;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Apache Example
```apache
ProxyPreserveHost On
ProxyPass /api/ http://localhost:8000/
ProxyPassReverse /api/ http://localhost:8000/

ProxyPass / http://localhost:5173/
ProxyPassReverse / http://localhost:5173/
```

## SSL/TLS Setup

### Let's Encrypt with Certbot

```bash
sudo certbot certonly --standalone -d your-domain.com
# Update Nginx/Apache to use /etc/letsencrypt/live/your-domain.com/
```

### Update .env
```env
FRONTEND_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com
```

## Monitoring & Logging

### Application Logs

Set `LOG_LEVEL` in .env:
- `DEBUG`: Verbose logging
- `INFO`: Normal operation
- `WARNING`: Important warnings
- `ERROR`: Only errors

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Performance Monitoring

Monitor key metrics:
- API response times
- Database query performance
- Document upload sizes
- Graph computation times

## Backup & Recovery

### Database Backup

PostgreSQL:
```bash
pg_dump -U user -h localhost netra_prod > backup.sql
```

Neo4j:
```bash
bin/neo4j-admin backup --backup-dir=backups --database=neo4j
```

### Document Storage

Backup uploaded documents (if persisting):
```bash
tar -czf documents_backup.tar.gz backend/uploads/
```

## Security Checklist

- [ ] Change JWT_SECRET to a strong random value
- [ ] Use HTTPS in production
- [ ] Configure CORS to allow only trusted origins
- [ ] Set DEBUG=false in production
- [ ] Use strong database passwords
- [ ] Enable database backups
- [ ] Monitor API logs for suspicious activity
- [ ] Keep dependencies updated (`pip install --upgrade`, `npm update`)
- [ ] Run security scans (`bandit`, `npm audit`)

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install --force-reinstall -r backend/requirements.txt

# Check environment variables
echo $env:PYTHONPATH
```

### Database connection errors
```bash
# Test PostgreSQL connection
psql -U user -h localhost -d netra_prod -c "SELECT 1"

# Test Neo4j connection
# Access http://localhost:7687 in browser
```

### Frontend build fails
```bash
# Clear node_modules and reinstall
rm -r frontend/node_modules
npm install --prefix frontend

# Clear npm cache if needed
npm cache clean --force
```

### API timeouts
- Increase database query timeouts in `.env`
- Add caching for frequently accessed data
- Consider horizontal scaling for high traffic

## Support

- API Documentation: http://localhost:8000/docs
- GitHub Issues: [project-repository]
- Email: [support-email]
