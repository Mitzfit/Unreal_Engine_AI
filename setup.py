#!/usr/bin/env python3
"""
Quick Setup Script for Unreal AI Platform
setup.py - Initialize project and install dependencies
"""

import os
import sys
import subprocess
from pathlib import Path


class ProjectSetup:
    """Setup project environment"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / 'venv'
    
    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60)
    
    def print_step(self, num: int, text: str):
        """Print step"""
        print(f"\n[{num}] {text}")
    
    def run_command(self, cmd, description: str = "") -> bool:
        """Run shell command"""
        if description:
            print(f"    → {description}")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"    ✓ Success")
                return True
            else:
                print(f"    ✗ Failed")
                if result.stderr:
                    print(f"    Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False
    
    def check_python_version(self) -> bool:
        """Check Python version"""
        self.print_step(1, "Checking Python version...")
        
        version = sys.version_info
        if version >= (3, 11):
            print(f"    ✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
            return True
        else:
            print(f"    ✗ Python {version.major}.{version.minor} (requires 3.11+)")
            return False
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip"""
        self.print_step(2, "Upgrading pip...")
        
        cmd = f"{sys.executable} -m pip install --upgrade pip"
        return self.run_command(cmd, "Running pip install --upgrade pip")
    
    def create_virtual_environment(self) -> bool:
        """Create virtual environment"""
        self.print_step(3, "Creating virtual environment...")
        
        if self.venv_path.exists():
            print(f"    ○ Virtual environment already exists at {self.venv_path}")
            return True
        
        cmd = f"{sys.executable} -m venv {self.venv_path}"
        return self.run_command(cmd, f"Creating venv at {self.venv_path}")
    
    def get_activation_command(self) -> str:
        """Get venv activation command"""
        if sys.platform == 'win32':
            return str(self.venv_path / 'Scripts' / 'activate')
        else:
            return f"source {self.venv_path / 'bin' / 'activate'}"
    
    def install_requirements(self) -> bool:
        """Install requirements"""
        self.print_step(4, "Installing Python dependencies...")
        
        req_file = self.project_root / 'requirements.txt'
        if not req_file.exists():
            print(f"    ✗ Requirements file not found: {req_file}")
            return False
        
        if sys.platform == 'win32':
            pip_path = self.venv_path / 'Scripts' / 'pip'
        else:
            pip_path = self.venv_path / 'bin' / 'pip'
        
        cmd = f"{pip_path} install -r {req_file}"
        return self.run_command(cmd, f"Installing from {req_file}")
    
    def create_env_file(self) -> bool:
        """Create .env file if missing"""
        self.print_step(5, "Setting up environment configuration...")
        
        env_file = self.project_root / '.env'
        if env_file.exists():
            print(f"    ○ .env file already exists")
            return True
        
        env_content = """# Unreal AI Platform Configuration
# Last Generated: $(date)

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/unreal_ai
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Azure Configuration
AZURE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_ACCOUNT_NAME=your_account_name
AZURE_STORAGE_ACCOUNT_KEY=your_key_here

# Environment
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Audio/Video Processing
FFMPEG_PATH=ffmpeg
AUDIO_SAMPLE_RATE=44100

# Dialogue System
VOICE_PROVIDER=google
TTS_LANGUAGE=en-US

# Features
ENABLE_VOICE_GENERATION=True
ENABLE_LIP_SYNC=True
ENABLE_RELATIONSHIP_TRACKING=True
ENABLE_PROCEDURAL_GENERATION=True
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            print(f"    ✓ Created .env file")
            print(f"    ⚠️  Please update .env with your configuration")
            return True
        except Exception as e:
            print(f"    ✗ Failed to create .env: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories"""
        self.print_step(6, "Creating project directories...")
        
        dirs = [
            'voice_output',
            'dialogue_projects',
            'blender_exports',
            'logs',
            'cache',
            'exports',
            'models'
        ]
        
        for dir_name in dirs:
            dir_path = self.project_root / dir_name
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"    ✓ {dir_name}/")
            except Exception as e:
                print(f"    ✗ Failed to create {dir_name}: {e}")
                return False
        
        return True
    
    def verify_installation(self) -> bool:
        """Verify installation"""
        self.print_step(7, "Verifying installation...")
        
        try:
            import fastapi
            print(f"    ✓ FastAPI {fastapi.__version__}")
            
            import sqlalchemy
            print(f"    ✓ SQLAlchemy {sqlalchemy.__version__}")
            
            import torch
            print(f"    ✓ PyTorch {torch.__version__}")
            
            import numpy
            print(f"    ✓ NumPy {numpy.__version__}")
            
            import pandas
            print(f"    ✓ Pandas {pandas.__version__}")
            
            return True
        except ImportError as e:
            print(f"    ✗ Import verification failed: {e}")
            return False
    
    def setup(self) -> bool:
        """Run complete setup"""
        self.print_header("UNREAL AI PLATFORM SETUP")
        
        steps = [
            ("Python Version Check", self.check_python_version),
            ("Upgrade pip", self.upgrade_pip),
            ("Virtual Environment", self.create_virtual_environment),
            ("Install Requirements", self.install_requirements),
            ("Environment Configuration", self.create_env_file),
            ("Create Directories", self.create_directories),
            ("Verify Installation", self.verify_installation),
        ]
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    print(f"\n✗ Setup failed at: {step_name}")
                    return False
            except Exception as e:
                print(f"\n✗ Error during {step_name}: {e}")
                return False
        
        self.print_success()
        return True
    
    def print_success(self):
        """Print success message"""
        self.print_header("✅ SETUP COMPLETED SUCCESSFULLY")
        
        activate_cmd = self.get_activation_command()
        
        print("\n📝 Next Steps:")
        print(f"\n1. Activate virtual environment:")
        print(f"   {activate_cmd}")
        
        print(f"\n2. Update .env file with your configuration:")
        print(f"   Edit {self.project_root / '.env'}")
        
        print(f"\n3. Run the application:")
        if sys.platform == 'win32':
            print(f"   python main.py")
        else:
            print(f"   python main.py")
        
        print(f"\n4. Access the API:")
        print(f"   http://localhost:8000")
        print(f"   http://localhost:8000/docs (Swagger UI)")
        
        print("\n📦 Installed Components:")
        print("  ✓ FastAPI web framework")
        print("  ✓ SQLAlchemy ORM")
        print("  ✓ OpenAI API integration")
        print("  ✓ PyTorch for AI models")
        print("  ✓ Pandas for data processing")
        print("  ✓ Redis for caching")
        print("  ✓ Audio/Video processing tools")
        print("  ✓ Dialogue system")
        print("  ✓ Procedural generation")
        
        print("\n📚 Documentation:")
        print("  - README.md - Project overview")
        print("  - INSTALLATION_GUIDE.md - Detailed setup instructions")
        print("  - DIALOGUE_SYSTEM_GUIDE.md - Dialogue system documentation")
        print("  - PROCEDURAL_GENERATION_GUIDE.md - Procedural generation guide")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Unreal AI Platform")
    parser.add_argument('--skip-pip-upgrade', action='store_true', help='Skip pip upgrade')
    parser.add_argument('--skip-venv', action='store_true', help='Skip virtual environment creation')
    
    args = parser.parse_args()
    
    setup = ProjectSetup()
    
    try:
        if setup.setup():
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Setup error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
