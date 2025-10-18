# FastAPI CloudRun Kit

A production-ready FastAPI boilerplate template for Google Cloud Run deployment with Firebase integration throughout the entire development lifecycle.

## Features

### 🚀 **Modern Python Stack**
- **FastAPI** with async/await patterns
- **UV** for lightning-fast package management
- **Python 3.11+** with modern typing
- **Pydantic v2** for data validation
- **Structured logging** with rich console output

### 🔥 **Firebase Integration**
- **Firebase Firestore** for database (local emulator + production)
- **Firebase Auth** for authentication and user management
- **Firebase Storage** for file uploads
- **Firebase Emulator Suite** for local development
- **Security rules** for both development and production

### ☁️ **Google Cloud Ready**
- **Google Cloud Run** deployment configuration
- **Google Cloud Build** with CI/CD pipeline
- **Docker** multi-stage builds optimized for UV
- **Cloud-native** logging and monitoring
- **IAM** and security best practices

### 🔧 **Developer Experience**
- **Hot reload** development server
- **Firebase emulators** for offline development
- **Comprehensive testing** with pytest
- **Code quality** tools (ruff, mypy, pre-commit)
- **Development scripts** for common tasks

### 🔐 **Security & Best Practices**
- **JWT tokens** and Firebase Auth integration
- **Role-based access control** (RBAC)
- **Rate limiting** and request validation
- **CORS** configuration
- **Security headers** and middleware

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for Firebase CLI)
- **Docker** (optional, for containerized development)
- **Google Cloud CLI** (for deployment)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/fastapi-cloudrun-kit.git
cd fastapi-cloudrun-kit

# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Copy environment configuration
cp .env.local.example .env
```

### 2. Firebase Setup

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Setup Firebase project
uv run python scripts/firebase.py setup

# Start Firebase emulators
uv run python scripts/firebase.py start
```

### 3. Start Development Server

```bash
# Start development server with Firebase emulators
uv run python scripts/dev.py

# Or use UV script
uv run dev
```

### 4. Explore the API

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Firebase Emulator UI**: http://localhost:4000
- **Health Check**: http://localhost:8000/health

## Project Structure

```
fastapi-cloudrun-kit/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── deps.py             # Dependencies and auth
│   │   └── v1/                 # API version 1
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── users.py        # User management
│   │       └── items.py        # Item CRUD operations
│   ├── core/
│   │   ├── config.py           # Settings and configuration
│   │   ├── security.py         # Security utilities
│   │   └── logging.py          # Logging configuration
│   ├── models/                 # Pydantic data models
│   ├── schemas/                # API request/response schemas
│   ├── services/               # Business logic services
│   └── utils/                  # Utility functions
├── firebase/
│   ├── firebase.json           # Firebase configuration
│   ├── firestore.rules         # Firestore security rules
│   ├── firestore.indexes.json  # Database indexes
│   └── storage.rules           # Storage security rules
├── tests/                      # Test suite
├── scripts/                    # Development scripts
├── deploy/                     # Deployment configurations
├── terraform/
│   ├── main.tf                 # Core infrastructure resources
│   ├── variables.tf            # Input variables for infrastructure
│   ├── outputs.tf              # Deployment outputs
│   ├── backend.tf              # Remote state configuration
│   ├── providers.tf            # Provider definitions
│   ├── example.tfvars          # Sample variable inputs
│   └── scripts/
│       └── tf.sh               # Helper Terraform commands
├── docker-compose.yml          # Local development environment
├── Dockerfile                  # Production container
├── cloudbuild.yaml             # Google Cloud Build
└── pyproject.toml              # UV configuration
```

## Development

### Environment Configuration

Create a `.env` file based on one of the examples:

- **`.env.local.example`** - Local development with emulators
- **`.env.prod.example`** - Production configuration
- **`.env.test`** - Test environment (already configured)

### Development Commands

```bash
# Start development server
uv run dev

# Run tests
uv run test

# Run linting
uv run lint

# Format code
uv run format

# Type checking
uv run typecheck

# Start Firebase emulators
uv run firebase-emulator

# Seed test data
uv run seed-data
```

### Database Operations

```bash
# Start Firebase emulators
python scripts/firebase.py start

# Seed development data
python scripts/seed.py

# Export emulator data
python scripts/firebase.py export

# Import emulator data
python scripts/firebase.py import

# Clear emulator data
python scripts/firebase.py clear
```

### Testing

```bash
# Run all tests
uv run test

# Run specific test file
uv run test tests/test_auth.py

# Run tests with coverage
uv run test-cov

# Run tests without Firebase emulators
python scripts/test.py --no-firebase

# Run only unit tests
pytest -m "unit"

# Run only integration tests
pytest -m "integration"
```

## API Usage

### Authentication

```python
import requests

# Register a new user
response = requests.post("http://localhost:8000/api/v1/auth/register", json={
    "email": "user@example.com",
    "password": "Password123!",
    "display_name": "John Doe"
})

# Login (for JWT tokens)
response = requests.post("http://localhost:8000/api/v1/auth/login", json={
    "email": "user@example.com", 
    "password": "Password123!"
})
token = response.json()["access_token"]

# Use token in subsequent requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/users/me", headers=headers)
```

### Items Management

```python
# Create an item
response = requests.post("http://localhost:8000/api/v1/items", 
    headers=headers,
    json={
        "title": "My First Item",
        "description": "This is a test item",
        "category": "general",
        "priority": "medium",
        "status": "draft",
        "tags": ["test", "example"],
        "is_public": True
    }
)

# List public items
response = requests.get("http://localhost:8000/api/v1/items")
items = response.json()["items"]
```

## Deployment

### Google Cloud Setup

```bash
# Set your Google Cloud project
export PROJECT_ID=your-project-id
export REGION=us-central1

# Run setup script
./deploy/scripts/setup-gcp.sh

# Deploy to Cloud Run
./deploy/scripts/deploy.sh
```

### Manual Cloud Build

```bash
# Submit build
gcloud builds submit --config cloudbuild.yaml .

# Deploy specific version
gcloud run deploy fastapi-cloudrun-kit \
  --image gcr.io/PROJECT_ID/fastapi-cloudrun-kit:latest \
  --region us-central1 \
  --platform managed
```

### Docker Deployment

```bash
# Build production image
docker build --target production -t fastapi-cloudrun-kit .

# Run with Docker Compose
docker-compose up -d

# Run production container
docker run -p 8000:8000 \
  -e FIREBASE_PROJECT_ID=your-project \
  -e SECRET_KEY=your-secret-key \
  fastapi-cloudrun-kit
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment name | `development` | No |
| `FIREBASE_PROJECT_ID` | Firebase project ID | - | Yes |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `USE_FIREBASE_EMULATOR` | Use emulators | `false` | No |
| `DEBUG` | Enable debug mode | `false` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Firebase Configuration

The application automatically detects whether to use Firebase emulators or production based on:

1. `USE_FIREBASE_EMULATOR` environment variable
2. `ENVIRONMENT` setting (emulators used for `development` and `test`)
3. Presence of emulator environment variables

### Security Rules

Firestore security rules are located in `firebase/firestore.rules` and include:

- **Users**: Can read/write their own data, admins can manage all users
- **Items**: Public items readable by all, private items only by owners
- **Role-based access**: Admin and moderator roles with appropriate permissions

## Architecture

### Application Structure

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Firebase      │    │  Google Cloud   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ API Routes  │ │◄──►│ │ Firestore   │ │    │ │ Cloud Run   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Auth        │ │◄──►│ │ Auth        │ │    │ │ Cloud Build │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Services    │ │◄──►│ │ Storage     │ │    │ │ Secret Mgr  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Request Flow

1. **Client** sends request to FastAPI
2. **Middleware** processes CORS, logging, rate limiting
3. **Authentication** validates Firebase token
4. **API Routes** handle business logic
5. **Services** interact with Firebase/Firestore
6. **Response** returns structured JSON

## Contributing

### Development Workflow

1. **Setup**: Clone repo and install dependencies
2. **Branch**: Create feature branch from main
3. **Develop**: Write code with tests
4. **Quality**: Run linting and formatting
5. **Test**: Ensure all tests pass
6. **Commit**: Use conventional commit messages
7. **PR**: Create pull request with description

### Code Quality

```bash
# Install pre-commit hooks
uv run pre-commit-install

# Run all quality checks
uv run test --no-firebase
uv run lint
uv run format
uv run typecheck
```

### Commit Messages

Use conventional commit format:

```
feat: add user profile endpoints
fix: resolve authentication token validation
docs: update API documentation
test: add integration tests for items
```

## Troubleshooting

### Common Issues

**Firebase Emulators Not Starting**
```bash
# Check if ports are in use
lsof -i :4000 -i :8080 -i :9099 -i :9199

# Kill existing processes
pkill -f firebase

# Restart emulators
python scripts/firebase.py restart
```

**UV Commands Not Working**
```bash
# Ensure UV is installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Clear cache if needed
rm -rf .venv && uv sync
```

**Authentication Errors**
```bash
# Check Firebase emulator status
python scripts/firebase.py status

# Verify environment variables
cat .env | grep FIREBASE
```

### Performance Optimization

- **Use connection pooling** for high-traffic scenarios
- **Enable caching** with Redis for frequently accessed data
- **Optimize Firestore queries** with proper indexing
- **Use pagination** for large result sets
- **Monitor metrics** with Google Cloud Monitoring

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: This README and inline code comments
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and community

---

**Built with ❤️ using FastAPI, Firebase, and Google Cloud**
