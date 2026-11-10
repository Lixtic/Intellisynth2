# 🚀 AI Flight Recorder - IntelliSynth Solution

> **Comprehensive AI Agent Monitoring and Compliance System**

A powerful monitoring platform for AI agents with real-time dashboards, compliance tracking, anomaly detection, and comprehensive reporting capabilities.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Capabilities

- **📊 Real-time Monitoring**
  - Live agent status and system metrics
  - CPU, memory, and network usage tracking
  - Active agent dashboard with health indicators
  - Real-time activity stream with auto-refresh

- **📋 Activity Logging**
  - Immutable record of all AI agent actions
  - SHA-256 hash verification for data integrity
  - Structured logging with metadata
  - Transparent audit trail

- **🔍 Anomaly Detection**
  - AI-powered pattern recognition
  - Statistical outlier detection
  - Behavioral analysis
  - Cross-agent correlation detection
  - 4 detection methods: statistical, pattern, behavioral, correlation

- **🛡️ Compliance Management**
  - Automated compliance violation detection
  - Rule-based monitoring
  - Severity classification (critical, high, medium, low)
  - Resolution and snooze workflows

- **🤖 AI Data Analyst Chatbot**
  - Natural language queries
  - Log search and analysis
  - System metrics reporting
  - Intelligent error detection
  - Help system and command suggestions

- **📈 Advanced Reporting**
  - Agent activity reports
  - System status reports
  - Compliance reports
  - Security audit reports
  - CSV/JSON export capabilities

- **🔐 Authentication & Security**
  - Demo authentication (extendable to JWT)
  - Role-based access control (RBAC) ready
  - Secure API endpoints
  - Session management

### User Interface

- **Modern Responsive Design**
  - TailwindCSS styling
  - Dark theme optimized
  - Mobile-friendly
  - Interactive charts (Chart.js)
  - Font Awesome icons

- **Interactive Dashboards**
  - Main monitoring dashboard
  - Activity log viewer
  - Compliance management
  - Report generation UI

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### 3-Minute Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd ai_flight_recorder_backend_with_db

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database (optional)
python init_db.py

# 5. Start the server
uvicorn app.main_fixed:app --reload --host 127.0.0.1 --port 8000
```



## 💻 Installation

### Detailed Installation Steps

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai_flight_recorder_backend_with_db
```

#### 2. Set Up Virtual Environment

**Windows**:
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment (Optional)

Create a `.env` file in the root directory:

```env
# Application Settings
APP_NAME=IntelliSynth Solution
APP_VERSION=1.0.0
DEBUG=True

# Server Settings
HOST=127.0.0.1
PORT=8000

# Database Settings
DATABASE_URL=sqlite:///./ai_flight_recorder.db

# Security Settings (for future JWT implementation)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 5. Initialize Database

```bash
python init_db.py
```

This creates the SQLite database and tables.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./logs.db` |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `True` |
| `SECRET_KEY` | JWT secret key | `changeme` |

### Database Configuration

Edit `app/database.py` to change database settings:

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_flight_recorder.db"
# For PostgreSQL:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

---

## 🎯 Usage

### Starting the Server

**Development Mode** (with auto-reload):
```bash
uvicorn app.main_fixed:app --reload --host 127.0.0.1 --port 8000
```

**Production Mode**:
```bash
uvicorn app.main_fixed:app --host 0.0.0.0 --port 8000 --workers 4
```

**With Gunicorn** (Linux/Mac):
```bash
gunicorn app.main_fixed:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### API Usage Examples

#### Log an Activity

```bash
curl -X POST "http://127.0.0.1:8000/api/activity-logs" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "ai-monitor",
    "action_type": "decision",
    "severity": "info",
    "message": "Analyzed system metrics and found optimal configuration",
    "data": {
      "confidence": 0.95,
      "impact_score": 8.5
    }
  }'
```

#### Get Recent Activities

```bash
curl "http://127.0.0.1:8000/api/activity-logs?limit=10"
```

#### Query the Chatbot

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me recent errors"}'
```

#### Detect Anomalies

```bash
curl "http://127.0.0.1:8000/api/monitoring/anomalies"
```

---

## 📚 API Documentation

### Interactive API Docs

Access the interactive Swagger UI documentation:

**http://127.0.0.1:8000/docs**

### API Endpoints Overview

#### Core Application
- `GET /` - Main dashboard (HTML)
- `GET /health` - Health check
- `GET /api/info` - API information

#### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/status` - Auth status

#### Activity Logging
- `GET /api/activity-logs` - List activities
- `POST /api/activity-logs` - Create activity
- `GET /api/activity-logs/latest` - Latest activities
- `GET /api/activity-logs/stats` - Activity statistics
- `GET /api/agents` - List agents

#### Monitoring
- `GET /api/monitoring/dashboard` - Dashboard metrics
- `GET /api/monitoring/metrics` - System metrics
- `GET /api/monitoring/agents` - Agent status
- `GET /api/monitoring/anomalies` - Anomaly detection

#### Compliance
- `GET /api/monitoring/compliance/violations` - Violations
- `GET /api/compliance/rules` - Compliance rules
- `POST /api/compliance/rules` - Create rule
- `PUT /api/compliance/violations/{id}/resolve` - Resolve violation

#### Reports
- `GET /api/reports` - List reports
- `POST /api/reports/generate` - Generate report
- `GET /api/reports/{id}` - Get report
- `GET /api/reports/{id}/export` - Export report

#### Chatbot
- `POST /api/chat` - Query the AI chatbot

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                Frontend (Browser)                    │
│  Dashboard | Activity Log | Compliance | Reports    │
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────┴────────────────────────────────┐
│         FastAPI Application (main_fixed.py)         │
│  ┌──────────────────────────────────────────────┐  │
│  │  45 Endpoints across 8 categories            │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
   Service Layer              Data Layer
        │                           │
┌───────┴─────────┐      ┌─────────┴──────────┐
│ - Activity      │      │ - ActivityLog      │
│   Logger        │◄─────┤   (SQLAlchemy)     │
│ - Anomaly       │      │ - SQLite Database  │
│   Detection     │      │                    │
│ - Compliance    │      └────────────────────┘
│ - Chatbot       │
│ - Reports       │
└─────────────────┘
```

### Tech Stack

- **Backend**: FastAPI (async Python web framework)
- **Database**: SQLAlchemy ORM + SQLite
- **Frontend**: Jinja2 templates + TailwindCSS + Chart.js
- **Server**: Uvicorn (ASGI server)
- **Authentication**: Demo auth (JWT-ready)

### Project Structure

```
ai_flight_recorder_backend_with_db/
├── app/
│   ├── main_fixed.py          # Main application (45 routes)
│   ├── database.py            # SQLAlchemy configuration
│   ├── models/                # Database models
│   │   ├── activity_log.py    # Activity log model
│   │   └── ...
│   ├── services/              # Business logic
│   │   ├── activity_logger.py     # Activity logging
│   │   ├── anomaly_detection.py   # Anomaly detection
│   │   ├── data_analyst_chatbot.py # AI chatbot
│   │   └── ...
│   └── api/                   # API route modules
├── static/                    # CSS, JS, assets
│   ├── dashboard.js
│   ├── dashboard.css
│   └── ...
├── templates/                 # HTML templates
│   ├── dashboard.html
│   ├── activity-log.html
│   └── ...
├── requirements.txt           # Python dependencies
├── init_db.py                # Database initialization
└── README.md                 # This file
```

---

## 🔧 Development

### Running in Development Mode

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Start with auto-reload
uvicorn app.main_fixed:app --reload --host 127.0.0.1 --port 8000
```

### Code Quality Tools

**Format Code**:
```bash
black app/
```

**Lint Code**:
```bash
flake8 app/
```

**Type Checking**:
```bash
mypy app/
```

### Adding New Features

1. **Create a Service** in `app/services/`
2. **Define Models** in `app/models/`
3. **Add Routes** in `app/main_fixed.py` or `app/api/`
4. **Update Frontend** in `templates/` and `static/`
5. **Write Tests** in `tests/`

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_activity_logger.py
```

### Test Files

- `test_activity_logger.py` - Activity logging tests
- `test_integration.py` - Integration tests
- `test_server.py` - Server tests
- `test_simple.py` - Simple smoke tests

---

## 🚀 Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main_fixed:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t ai-flight-recorder .
docker run -p 8000:8000 ai-flight-recorder
```

### Cloud Deployment

#### Heroku

```bash
# Create Procfile
echo "web: uvicorn app.main_fixed:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create ai-flight-recorder
git push heroku main
```

#### AWS EC2 / Azure / GCP

1. Set up a virtual machine
2. Install Python 3.10+
3. Clone repository
4. Install dependencies
5. Run with Gunicorn + Nginx reverse proxy

---

## 📊 Monitoring & Logging

### Application Logs

Logs are written to:
- Console (stdout)
- `logs/` directory (if configured)

### Health Checks

- **Endpoint**: `GET /health`
- **Response**: `{"status": "healthy", "timestamp": "...", "uptime": "99.9%"}`

### Metrics

Access Prometheus metrics (if enabled):
- **Endpoint**: `GET /metrics`

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Code Standards

- Follow PEP 8 style guide
- Write docstrings for all functions/classes
- Add type hints
- Write unit tests for new features
- Update documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework
- **TailwindCSS** - Utility-first CSS framework
- **Chart.js** - Interactive charts
- **Font Awesome** - Icon library

---

## 📞 Support

- **Documentation**: http://127.0.0.1:8000/docs
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: support@intellisynth.com

---

## 🗺️ Roadmap

### Version 1.1
- [ ] JWT authentication
- [ ] User management
- [ ] WebSocket support for real-time updates
- [ ] PostgreSQL support

### Version 1.2
- [ ] Multi-tenant support
- [ ] Advanced ML anomaly detection
- [ ] Grafana integration
- [ ] Kubernetes deployment

### Version 2.0
- [ ] Microservices architecture
- [ ] GraphQL API
- [ ] React/Vue frontend
- [ ] Mobile app

---

**Built with ❤️ by the IntelliSynth Team**

**Last Updated**: November 16, 2025  
**Version**: 1.0.0
