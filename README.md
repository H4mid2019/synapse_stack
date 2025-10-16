# Flask React Monorepo

Full-stack file management system with Flask backend and React frontend in a Turborepo monorepo.

## Online example app

[synapse-stack.darabi.website](https://synapse-stack.darabi.website/)

## Key Features

- **PDF File Management** - Upload, organize, and download PDF files
- **Smart Search** - Search by filename and PDF text content
- **Automatic Text Extraction** - PDFs are processed automatically for searchable content
- **Folder Organization** - Create nested folder structures up to 25 levels deep
- **Real-time Updates** - Instant UI updates using Preact Signals
- **Multi-Service Architecture** - Scalable microservices design with load balancing
- **Auth0 Integration** - Secure authentication and authorization
- **Production Ready** - CI/CD pipeline with automated testing and Docker deployment

## Quick Navigation

- [Quick Start](#quick-start) - Get running in 5 minutes
- [Platform-Specific Setup](#platform-specific-setup) - Windows, Mac, Linux instructions
- [Architecture Overview](#architecture-overview) - How the app works
- [Testing](#testing) - Run tests
- [Deployment](#deployment) - Production setup
- [API Reference](#api-reference) - Available endpoints

## Tech Stack

Backend: Python 3.12 + Flask + SQLAlchemy
Frontend: React 18 + TypeScript + Vite + Tailwind CSS
Database: PostgreSQL (dev) / CockroachDB (production)
State: Preact Signals
Testing: pytest + Playwright
Deployment: Docker + GitHub Actions

## Quick Start

Choose your setup method:

**Option 1: Docker (Recommended)**

```bash
git clone <repository-url>
cd flask-react-monorepo
docker-compose up --build
```

Access: http://localhost:3000

**Option 2: Local Development**

```bash
git clone <repository-url>
cd flask-react-monorepo
npm install
cd apps/backend
python -m venv .venv
# Activate venv (see platform-specific instructions below)
pip install -r requirements.txt
cd ../..
npm run dev
```

Access: http://localhost:5173

## Platform-Specific Setup

### Windows

**Python Virtual Environment:**

```powershell
cd apps/backend
python -m venv .venv
.venv\Scripts\activate.ps1          # PowerShell
# OR
.venv\Scripts\activate.bat          # CMD
pip install -r requirements.txt
```

**PostgreSQL Setup:**

```powershell
# Using scoop package manager
scoop install postgresql
pg_ctl -D "C:\Program Files\PostgreSQL\data" start
createdb flask_react_db

# OR download from postgresql.org and use pgAdmin GUI
```

**Environment Variables:**
Create `apps/backend/.env`:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/flask_react_db
SECRET_KEY=your-secret-key-here
```

**Run Migrations:**

```powershell
cd apps/backend
python run_migration.py
# Or with Flask CLI (requires FLASK_APP env var):
$env:FLASK_APP="app_factory:create_app('operations')"; flask db upgrade
```

### Mac

**Python Virtual Environment:**

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**PostgreSQL Setup:**

```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15
createdb flask_react_db
```

**Environment Variables:**
Create `apps/backend/.env`:

```
DATABASE_URL=postgresql://username@localhost:5432/flask_react_db
SECRET_KEY=your-secret-key-here
```

**Run Migrations:**

```bash
cd apps/backend
flask db upgrade
```

### Linux

**Python Virtual Environment:**

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**PostgreSQL Setup:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb flask_react_db

# Arch
sudo pacman -S postgresql
sudo systemctl start postgresql
sudo -u postgres createdb flask_react_db
```

**Environment Variables:**
Create `apps/backend/.env`:

```
DATABASE_URL=postgresql://postgres@localhost:5432/flask_react_db
SECRET_KEY=your-secret-key-here
```

**Run Migrations:**

```bash
cd apps/backend
python run_migration.py
# Or with Flask CLI:
FLASK_APP="app_factory:create_app('operations')" flask db upgrade
```

## Architecture Overview

**Multi-Service Backend:**
The backend runs 5 separate Flask instances in production:

- 2x READ services (GET requests, load balanced)
- 1x WRITE service (POST requests)
- 1x OPERATIONS service (PUT/DELETE requests)
- 1x TEXT EXTRACTOR service (PDF text extraction)

All services share the same PostgreSQL/CockroachDB database. Nginx routes requests based on HTTP method.

```mermaid
graph TB
    Client[Client Browser]

    subgraph Production
        Nginx[Nginx Reverse Proxy<br/>Port 80]
        Read1[READ Service 1<br/>GET requests]
        Read2[READ Service 2<br/>GET requests]
        Write[WRITE Service<br/>POST requests]
        Ops[OPERATIONS Service<br/>PUT/DELETE requests]
        Extractor[TEXT EXTRACTOR Service<br/>PDF text extraction]
        DB[(PostgreSQL/<br/>CockroachDB)]
    end

    subgraph Local Dev
        Proxy[Local Proxy<br/>Port 5000]
        ReadDev[READ Service<br/>Port 6001]
        WriteDev[WRITE Service<br/>Port 6002]
        OpsDev[OPERATIONS Service<br/>Port 6003]
        ExtractorDev[TEXT EXTRACTOR Service<br/>Port 6004]
        DBDev[(PostgreSQL<br/>Port 5432)]
    end

    Client -->|Production| Nginx
    Client -->|Development| Proxy

    Nginx -->|GET| Read1
    Nginx -->|GET| Read2
    Nginx -->|POST| Write
    Nginx -->|PUT/DELETE| Ops

    Proxy -->|GET| ReadDev
    Proxy -->|POST| WriteDev
    Proxy -->|PUT/DELETE| OpsDev

    Ops -->|Extract PDF Text| Extractor
    OpsDev -->|Extract PDF Text| ExtractorDev

    Read1 --> DB
    Read2 --> DB
    Write --> DB
    Ops --> DB
    Extractor --> DB

    ReadDev --> DBDev
    WriteDev --> DBDev
    OpsDev --> DBDev
    ExtractorDev --> DBDev

    style Nginx fill:#4CAF50
    style Proxy fill:#2196F3
    style DB fill:#FF9800
    style DBDev fill:#FF9800
    style Extractor fill:#9C27B0
    style ExtractorDev fill:#9C27B0
```

**Local Development:**
Single proxy routes to all backend services running on different ports.

**Database:**

- Tables: users, filesystem_items, file_permissions
- Search columns: name (VARCHAR), content_text (TEXT) for full-text search
- PDF extraction tracking: content_extracted (BOOLEAN), extraction_error (VARCHAR)
- Unique constraint per user: prevents duplicate filenames in same folder
- Cascade delete: deleting folder removes all nested items
- See `docs_local/` for detailed architecture docs

**Frontend:**

- React with TypeScript
- Preact Signals for state management (lightweight, no re-render issues)
- Tailwind CSS for styling
- Vite for fast dev server and builds

## Project Structure

```
apps/
  backend/
    app_factory.py       # Creates Flask apps (read/write/operations)
    run_bjoern.py        # Production WSGI server
    local_proxy.py       # Dev reverse proxy
    routes_read.py       # GET endpoints
    routes_write.py      # POST endpoints
    routes_operations.py # PUT/DELETE endpoints
    models.py            # Database models
    database.py          # DB initialization
    tests/               # Backend tests
  frontend/
    src/
      components/        # React components
      pages/            # Page components
      store/            # Preact Signals state
      services/         # API client
      types/            # TypeScript types
docker-compose.yml      # Production container setup
turbo.json             # Monorepo task runner
```

## API Reference

**File System Operations:**

- `GET /api/filesystem` - List items in folder (query: parent_id)
- `POST /api/filesystem` - Create folder
- `GET /api/filesystem/{id}` - Get item details
- `PUT /api/filesystem/{id}` - Rename item
- `DELETE /api/filesystem/{id}` - Delete item (cascade)
- `POST /api/filesystem/upload` - Upload PDF file (max 100MB)
- `GET /api/filesystem/{id}/download` - Download file
- `GET /api/filesystem/search` - Search files and folders (query params: q, type, page, limit)

**Search Parameters:**

- `q` (required) - Search query text
- `type` (optional) - Filter by type: "file" or "folder"
- `page` (optional) - Page number (default: 1)
- `limit` (optional) - Results per page (default: 50, max: 100)

**Search Features:**

- Searches file/folder names
- Searches PDF text content (extracted automatically on upload)
- Returns paginated results with metadata

**File Upload Restrictions:**

- Only PDF files allowed
- Maximum file size: 100MB
- Files validated for PDF format and content
- Text automatically extracted from PDFs for search functionality

**System:**

- `GET /api/health` - Health check

All endpoints require authentication (Auth0 JWT) except in test mode.

## Development Commands

**Root Directory:**

```bash
npm run dev          # Start all services
npm run build        # Build everything
npm run lint         # Check code quality
npm run test         # Run all tests
npm run test:e2e     # Run E2E tests
```

**Backend (apps/backend):**

```bash
npm run dev          # Start Flask dev server
npm run test         # Run pytest
npm run lint         # Run flake8
npm run format       # Format with black + isort
python run_migration.py        # Apply migrations
FLASK_APP="app_factory:create_app('operations')" flask db migrate -m "description"  # Generate migration
```

**Frontend (apps/frontend):**

```bash
npm run dev          # Start Vite dev server
npm run build        # Build for production
npm run lint         # Run ESLint
npm run preview      # Preview production build
```

## Testing

**Run All Tests:**

```bash
npm run test         # Backend + E2E tests
```

**Backend Unit Tests:**

```bash
cd apps/backend
pytest tests/ -v
```

**E2E Tests (Playwright):**

For local E2E testing, you need both backend and frontend running in test mode:

```bash
# Windows - Terminal 1: Start backend in test mode
.\start-backend-test.bat

# Windows - Terminal 2: Start frontend in test mode
.\start-frontend-test.bat

# Terminal 3: Run E2E tests
npm run test:e2e           # Headless
npm run test:e2e:ui        # Interactive UI
npm run test:e2e:headed    # See browser
```

```bash
# Mac/Linux - Terminal 1: Start backend in test mode
TEST_MODE=true cd apps/backend && python start_local.py

# Mac/Linux - Terminal 2: Start frontend in test mode
VITE_TEST_MODE=true cd apps/frontend && npm run dev

# Terminal 3: Run E2E tests
npm run test:e2e           # Headless
npm run test:e2e:ui        # Interactive UI
npm run test:e2e:headed    # See browser
```

**Prerequisites for local E2E tests:**

- PostgreSQL running on localhost:5432
- Database `flask_react_db` created
- All dependencies installed (`npm install` in root)

**Test Mode (Bypass Auth):**

Set environment variables to skip Auth0:

- Backend: `TEST_MODE=true`
- Frontend: `VITE_TEST_MODE=true`

Uses mock user "Test User" instead of real authentication. Playwright sets these automatically.

## Environment Variables

**Backend (apps/backend/.env):**

```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/flask_react_db
TEST_MODE=false                    # Set to true to bypass Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=your-api-identifier

# Text Extractor Service URL
TEXT_EXTRACTOR_URL=http://localhost:6004                    # Local dev
# TEXT_EXTRACTOR_URL=http://text-extractor:6004            # Docker Compose (use service name)

# Optional: Google Cloud Storage for file uploads
GCS_BUCKET_NAME=your-bucket-name   # Leave empty to use local storage
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

**Frontend (apps/frontend/.env):**

```bash
VITE_API_URL=http://localhost:5000/api
VITE_TEST_MODE=false               # Set to true to bypass Auth0
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=your-api-identifier
```

## File Storage

The app supports two storage options for uploaded files:

**Local Storage (Default):**
Files are stored in the `uploads/` folder on your server. Good for development and small deployments.

**Google Cloud Storage (Optional):**
Files are stored in a Google Cloud Storage bucket. Better for production and scaling.

To use GCS:

1. Create a Google Cloud Storage bucket
2. Set up authentication (service account key file)
3. Add to your environment:
   ```bash
   GCS_BUCKET_NAME=your-bucket-name
   ```

The app automatically detects which storage to use. If `GCS_BUCKET_NAME` is set, it uses cloud storage. Otherwise, it uses local files.

## Deployment

**Production Database:**

Use CockroachDB for production (free tier available):

1. Create CockroachDB Cloud cluster
2. Get connection string
3. Set environment variable:
   ```bash
   DATABASE_URL=cockroachdb://user:pass@host:26257/db?sslmode=verify-full
   ```
4. Run migrations:
   ```bash
   python add_search_columns.py  # Adds search columns (run once)
   python run_migration.py        # Run Flask-Migrate migrations
   ```

See `docs_local/COCKROACHDB_SETUP.md` for details.

**Docker Deployment:**

**Option 1: Build from source**

```bash
docker-compose up --build -d
```

**Option 2: Use pre-built images from Docker Hub**

```bash
# Pull latest images
docker pull hamid2019/flask-react-backend:main
docker pull hamid2019/flask-react-frontend:main

# Run with docker-compose (update image names in docker-compose.yml)
docker-compose up -d
```

**Published Images:**

- Backend: `hamid2019/flask-react-backend:main`
- Frontend: `hamid2019/flask-react-frontend:main`

Images are automatically built and pushed to Docker Hub when code is pushed to the main branch.

Services:

- Frontend: Port 3000
- Backend: Port 5000 (nginx routes to read/write/operations services)
- Database: Port 5432

**CI/CD Pipeline:**

GitHub Actions workflow runs on every push:

1. Lint checks (flake8, black, isort, ESLint, Prettier)
2. Backend tests (pytest with PostgreSQL)
3. E2E tests (Playwright)
4. Build Docker images (on main branch)

Required secrets:

- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `DATABASE_URL`

## Troubleshooting

**Database connection fails:**

- Check PostgreSQL is running
- Verify DATABASE_URL format
- Ensure database exists: `createdb flask_react_db`

**Migrations fail:**

- Delete `apps/backend/migrations/` folder
- Re-run: `flask db init && flask db migrate && flask db upgrade`

**Port already in use:**

- Change ports in docker-compose.yml or package.json scripts
- Kill existing process: `lsof -ti:5000 | xargs kill` (Mac/Linux)

**Auth0 errors:**

- Set TEST_MODE=true to bypass authentication during development
- Check Auth0 domain and client ID match

## Documentation

Additional docs in `docs_local/`:

- CODE_CONSOLIDATION.md - Multi-app architecture
- RACE_CONDITIONS_ANALYSIS.md - Database safety
- COCKROACHDB_SETUP.md - Production database setup
- DATABASE_MIGRATIONS.md - Migration guide
- CI_CD_NGINX_SETUP.md - Deployment details

## License

MIT

See [LICENSE](LICENSE) for details.
