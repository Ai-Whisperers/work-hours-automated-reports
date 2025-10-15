# Web Interface Setup Guide

This guide covers setting up and running the web interface (FastAPI backend + Next.js frontend).

## Architecture Overview

The web interface consists of two components:

1. **FastAPI Backend** (`src/presentation/api/`) - RESTful API server
2. **Next.js Frontend** (`frontend/`) - React-based web dashboard

## Backend Setup

### Prerequisites

- Python 3.11+
- Virtual environment activated
- Environment variables configured in `.env`

### Installation

Backend dependencies are included in the main `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Running the Backend

```bash
# Start the FastAPI server
python api_server.py
```

The API will be available at:
- **API Endpoints**: http://localhost:8000/api
- **Interactive Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### API Endpoints

#### Health Checks
- `GET /api/health` - Basic health check
- `GET /api/health/services` - External service connectivity

#### Reports
- `POST /api/reports/generate` - Generate a new report
- `GET /api/reports/status/{report_id}` - Check report status
- `GET /api/reports/download/{report_id}` - Download completed report

## Frontend Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend

# Install dependencies
npm install
```

### Running the Frontend

```bash
# Development mode (with hot reload)
npm run dev

# Production build
npm run build
npm start
```

The frontend will be available at: http://localhost:3000

### Environment Configuration

The frontend uses Next.js rewrites to proxy API requests. By default:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

To change the backend URL, edit `frontend/next.config.js`.

## Development Workflow

### Running Both Services

**Terminal 1 - Backend:**
```bash
python api_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Making Changes

#### Backend Changes
- Modify files in `src/presentation/api/`
- Uvicorn auto-reloads on file changes

#### Frontend Changes
- Modify files in `frontend/src/`
- Next.js auto-reloads on file changes

## Features

### Dashboard
- Service health monitoring
- Connection status for Clockify and Azure DevOps
- Real-time status updates

### Report Generation
- Date range selection
- Multiple format support (Excel, HTML, JSON)
- Progress tracking with polling
- Direct download from browser

### Technical Features
- **Backend**: Async processing with background tasks
- **Frontend**: React hooks for state management
- **Styling**: Tailwind CSS with dark theme
- **Icons**: Lucide React
- **HTTP Client**: Axios with TypeScript types

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill the process
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

**API not accessible:**
- Check if `api_server.py` is running
- Verify no firewall blocking port 8000
- Check logs for errors

### Frontend Issues

**Port 3000 already in use:**
```bash
# Change port in package.json
"dev": "next dev -p 3001"
```

**API requests failing:**
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify Next.js rewrites in `next.config.js`

**Dependencies not installing:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Production Deployment

### Backend

```bash
# Using uvicorn directly
uvicorn src.presentation.api.app:app --host 0.0.0.0 --port 8000

# Using gunicorn (recommended for production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.presentation.api.app:app
```

### Frontend

```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start

# Or deploy to Vercel/Netlify
```

### Environment Variables

For production, set:
- `ENVIRONMENT=production`
- `DEBUG=false`
- Update CORS origins in `src/presentation/api/app.py`

## Docker Deployment

Coming soon: Docker Compose configuration for both backend and frontend.

## API Authentication

**Note**: The current implementation does not include authentication. For production use, consider adding:

- JWT tokens (`python-jose` already in requirements)
- API keys
- OAuth2 integration

See `requirements.txt` for security-related packages included for future use.
