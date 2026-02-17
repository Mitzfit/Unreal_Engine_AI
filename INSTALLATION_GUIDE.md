# ============================================
# INSTALLATION GUIDE
# Unreal AI Platform - Dependencies Setup
# ============================================

## Prerequisites

- **Python 3.11+** (Recommended: Python 3.11.7+)
- **pip** (latest version)
- **git** (for version control)

## System-Level Dependencies

### Windows
```powershell
# Update system packages
winget upgrade

# Install FFmpeg (required for audio/video)
winget install ffmpeg

# Install Visual C++ Build Tools (if needed)
# Download from: https://visualstudio.microsoft.com/downloads/
```

### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install ffmpeg redis python@3.11 postgresql
```

### Linux (Ubuntu/Debian)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    pip \
    ffmpeg \
    redis-server \
    postgresql \
    postgresql-contrib \
    build-essential \
    git

# For GPU support (optional)
sudo apt install -y nvidia-cuda-toolkit nvidia-cudnn
```

## Python Environment Setup

### 1. Create Virtual Environment

```bash
# Using venv (recommended)
python3.11 -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Upgrade pip, setuptools, and wheel

```bash
pip install --upgrade pip setuptools wheel
```

### 3. Install Requirements

```bash
# Basic installation
pip install -r requirements.txt

# With specific Python index (if needed)
pip install -r requirements.txt --index-url https://pypi.org/simple/

# For GPU-accelerated PyTorch (optional)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Service Setup

### Redis (for caching)

**Windows:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Install and start Redis service

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

### PostgreSQL/MySQL (for database)

**Windows:**
- Download from: https://www.postgresql.org/download/windows/

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Docker:**
```bash
# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  --name postgres postgres:latest

# MySQL
docker run -d -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=password \
  --name mysql mysql:latest
```

## Verification

```bash
# Check Python version
python --version  # Should be 3.11+

# Check pip
pip --version

# List installed packages
pip list

# Verify key packages
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"

# Test imports
python -c "
import fastapi
import sqlalchemy
import openai
import redis
print('✓ All core packages imported successfully')
"
```

## Troubleshooting

### Installation Fails

```bash
# 1. Clear pip cache
pip cache purge

# 2. Try with no-cache-dir
pip install --no-cache-dir -r requirements.txt

# 3. Install build dependencies (Linux)
sudo apt install build-essential python3-dev

# 4. Update pip
pip install --upgrade pip

# 5. Install packages individually for debugging
pip install -v package_name
```

### FFmpeg Issues

```bash
# Verify FFmpeg installation
ffmpeg -version

# If not found, reinstall:
# Windows: winget install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

### Database Connection Issues

```bash
# Test PostgreSQL
psql -U postgres -c "SELECT 1"

# Test MySQL
mysql -u root -p

# Test Redis
redis-cli ping  # Should respond with PONG
```

### GPU/CUDA Issues

```bash
# Check CUDA installation
nvidia-smi

# Verify PyTorch sees GPU
python -c "import torch; print(torch.cuda.is_available())"

# If CUDA not found, reinstall PyTorch with CPU-only
pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## Optional Dependencies

### GPU Acceleration
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Development Tools
```bash
pip install jupyter jupyterlab notebook
```

### Audio Processing
```bash
pip install librosa soundfile music21
```

### 3D Processing
```bash
pip install trimesh pygltflib
```

## Production Deployment

### Create Production Requirements
```bash
pip freeze > requirements-prod.txt
```

### Install for Production
```bash
pip install --no-cache-dir -r requirements.txt --compile
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t unreal-ai .
docker run -p 8000:8000 unreal-ai
```

## Environment Variables

Create `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_key_here
AZURE_CONNECTION_STRING=your_connection_string
DEBUG=False
ENVIRONMENT=production
```

## Performance Optimization

### Cython Compilation
```bash
pip install cython
pip install --no-cache-dir -r requirements.txt --compile
```

### Memory Optimization
```bash
# Run with memory limits
python -m memory_profiler your_script.py
```

## Backup & Restore

### Backup Environment
```bash
pip freeze > backup_requirements.txt
```

### Restore from Backup
```bash
pip install -r backup_requirements.txt
```

## Additional Resources

- **Python Documentation**: https://docs.python.org/3.11/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **PyTorch Documentation**: https://pytorch.org/docs/stable/index.html
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Redis Documentation**: https://redis.io/documentation
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

## Support

For issues or questions:
1. Check the documentation
2. Review error logs
3. Consult GitHub issues
4. Contact support team

---

**Last Updated**: February 17, 2026
**Python Version**: 3.11+
**Status**: Production Ready
