# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack FastAPI application template with a React frontend, FastAPI backend, PostgreSQL database, and Docker Compose for development and deployment.

**Technology Stack:**
- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic
- **Frontend**: React + TypeScript + Vite + TanStack Router + TanStack Query + Chakra UI
- **Development**: Docker Compose + uv (Python) + npm (Node.js)
- **Testing**: Pytest (backend) + Playwright (frontend E2E)
- **Code Quality**: pre-commit + Ruff (Python) + Biome (TypeScript)

## Development Commands

### Docker Compose (Recommended for Full Stack)

```bash
# Start the entire stack with hot reload
docker compose watch

# View logs
docker compose logs
docker compose logs backend  # specific service

# Stop services
docker compose stop frontend
docker compose stop backend

# Tear down stack
docker compose down -v
```

**Development URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc
- Adminer (DB): http://localhost:8080
- Traefik UI: http://localhost:8090
- MailCatcher: http://localhost:1080

### Backend Development

From `backend/` directory:

```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run local development server (alternative to Docker)
fastapi dev app/main.py

# Run tests
bash ./scripts/test.sh

# Run tests in running stack
docker compose exec backend bash scripts/tests-start.sh

# Run tests with extra args (e.g., stop on first error)
docker compose exec backend bash scripts/tests-start.sh -x

# Database migrations
docker compose exec backend bash
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Access running backend container
docker compose exec backend bash
```

**Python Requirements:**
- Python >=3.10,<4.0
- Use `uv` for dependency management

### Frontend Development

From `frontend/` directory:

```bash
# Install Node.js version (using fnm or nvm)
fnm install  # or: nvm install
fnm use      # or: nvm use

# Install dependencies
npm install

# Run local development server
npm run dev

# Build for production
npm run build

# Preview production build
npm preview

# Run linter (Biome)
npm run lint

# Generate API client from backend OpenAPI spec
npm run generate-client

# Run E2E tests with Playwright
npx playwright test
npx playwright test --ui  # UI mode
```

**Generating Frontend Client:**

When backend API changes:

```bash
# Option 1: Automated (recommended)
./scripts/generate-client.sh

# Option 2: Manual
# 1. Start Docker Compose stack
# 2. Download http://localhost:8000/api/v1/openapi.json to frontend/openapi.json
# 3. Run: cd frontend && npm run generate-client
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

### Testing

```bash
# Backend tests (builds, runs, tears down)
bash ./scripts/test.sh

# Frontend E2E tests
cd frontend
docker compose up -d --wait backend
npx playwright test
docker compose down -v
```

## Code Architecture

### Backend Architecture (`backend/app/`)

**Core Structure:**
- `main.py` - FastAPI application entry point with CORS and Sentry configuration
- `models.py` - SQLModel models for database tables and Pydantic schemas (User, Item, Token, etc.)
- `crud.py` - Database operations (create_user, update_user, authenticate, etc.)
- `utils.py` - Utility functions (email sending, token generation)
- `initial_data.py` - Creates first superuser on startup
- `backend_pre_start.py` - Pre-startup checks (database connection)

**API Routes (`app/api/`):**
- `api/main.py` - API router aggregation with `/api/v1` prefix
- `api/deps.py` - FastAPI dependencies (authentication, database sessions)
- `api/routes/` - Route handlers:
  - `login.py` - Authentication endpoints (login, test-token, password recovery)
  - `users.py` - User management (CRUD operations, signup)
  - `items.py` - Item management (CRUD operations)
  - `utils.py` - Utility endpoints (health check, test email)
  - `private.py` - Development-only endpoints (local environment)

**Configuration (`app/core/`):**
- `config.py` - Settings management using Pydantic Settings (loads from `../.env`)
- `db.py` - Database engine and session configuration
- `security.py` - Password hashing and JWT token handling

**Database Migrations (`app/alembic/`):**
- Alembic migrations for schema changes
- Auto-generated from SQLModel changes
- Run inside backend container after model changes

### Frontend Architecture (`frontend/src/`)

**Core Structure:**
- `main.tsx` - Application entry point with providers (QueryClient, Router, ThemeProvider)
- `theme.tsx` - Chakra UI theme configuration with dark mode
- `routeTree.gen.ts` - Auto-generated route tree (do not edit manually)
- `utils.ts` - Utility functions and types

**Components (`components/`):**
- Reusable UI components
- Common patterns like UserMenu, Sidebar, forms

**Routes (`routes/`):**
- File-based routing with TanStack Router
- Each file represents a route/page
- Includes layouts, error boundaries, and loading states

**API Client (`client/`):**
- Auto-generated from OpenAPI spec using `@hey-api/openapi-ts`
- TypeScript types for all API endpoints
- Axios-based HTTP client
- **Important**: Regenerate after backend changes

**Hooks (`hooks/`):**
- Custom React hooks
- TanStack Query hooks for API data fetching

**Theme (`theme/`):**
- Chakra UI component customizations
- Color mode (dark/light) configurations

### Authentication Flow

1. User logs in via `/api/v1/login/access-token` with email/password
2. Backend validates credentials and returns JWT access token
3. Frontend stores token and includes in Authorization header for protected routes
4. Backend dependency `get_current_user` (in `api/deps.py`) validates token on each request
5. Password recovery via email token system (48-hour expiry)

### Database Models

**User Model:**
- UUID primary key
- Email (unique, indexed)
- Hashed password (bcrypt)
- is_active, is_superuser flags
- Relationship: owns multiple Items

**Item Model:**
- UUID primary key
- title, description fields
- owner_id foreign key to User (cascade delete)
- Relationship: belongs to User

All models use SQLModel (combines SQLAlchemy + Pydantic) for validation and ORM.

### Configuration Management

Settings in `.env` file (loaded by `backend/app/core/config.py`):
- **Security**: SECRET_KEY, FIRST_SUPERUSER, FIRST_SUPERUSER_PASSWORD
- **Database**: POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- **CORS**: BACKEND_CORS_ORIGINS (comma-separated)
- **Frontend**: FRONTEND_HOST (for email links)
- **Email**: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_PORT, EMAILS_FROM_EMAIL
- **Monitoring**: SENTRY_DSN
- **Environment**: ENVIRONMENT (local/staging/production)

**Important**: Change `changethis` values before deployment (SECRET_KEY, passwords).

## Development Workflow

### Making Backend Changes

1. Modify models in `backend/app/models.py`
2. Create migration: `docker compose exec backend bash` → `alembic revision --autogenerate -m "message"`
3. Apply migration: `alembic upgrade head`
4. Update CRUD operations in `crud.py` if needed
5. Add/modify API endpoints in `app/api/routes/`
6. Regenerate frontend client: `./scripts/generate-client.sh`
7. Update frontend to use new API types

### Making Frontend Changes

1. Modify components in `frontend/src/components/`
2. Add/update routes in `frontend/src/routes/`
3. Use generated API client types from `src/client/`
4. Test with `npm run dev` or Docker Compose
5. Run E2E tests with Playwright before committing

### Adding New API Endpoints

1. Create route handler in `backend/app/api/routes/`
2. Include router in `backend/app/api/main.py`
3. Use dependencies from `api/deps.py` for auth/db sessions
4. Follow existing patterns (User/Item routes as reference)
5. Regenerate frontend client after changes

### Working with Database

- Use SQLModel for all database models (combines ORM + validation)
- Always create Alembic migrations for schema changes
- Use `session.exec(select(Model).where(...))` for queries
- Follow patterns in `crud.py` for database operations
- Cascade deletes configured in model relationships

## Important Notes

- **Python virtual environment**: Backend uses `uv` for dependency management, virtual env at `backend/.venv/`
- **Node version**: Frontend requires Node.js version specified in `frontend/.nvmrc`
- **API prefix**: All backend routes prefixed with `/api/v1`
- **Auto-reload**: Docker Compose uses `fastapi run --reload` in development
- **Tests location**: Backend tests in `backend/tests/`, frontend E2E in `frontend/tests/`
- **Code coverage**: Generated in `backend/htmlcov/index.html` after tests
- **Private routes**: Routes in `api/routes/private.py` only available in local environment
- **Email templates**: Located in `backend/app/email-templates/`, use MJML for editing
- **Pre-commit hooks**: Run Ruff (Python), Biome (TypeScript), and other checks automatically
