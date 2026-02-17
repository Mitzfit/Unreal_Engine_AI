#!/usr/bin/env python3
"""
Dependency Checker and Installer
verify_dependencies.py - Check and validate all dependencies
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class DependencyChecker:
    """Check and verify all project dependencies"""
    
    # Core packages that must be installed
    REQUIRED_PACKAGES = {
        'fastapi': 'FastAPI',
        'sqlalchemy': 'SQLAlchemy',
        'openai': 'OpenAI',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'pydantic': 'Pydantic',
        'redis': 'Redis',
        'torch': 'PyTorch',
    }
    
    # Optional packages
    OPTIONAL_PACKAGES = {
        'azure.identity': 'Azure SDK',
        'elasticsearch': 'Elasticsearch',
        'stripe': 'Stripe',
        'PIL': 'Pillow',
    }
    
    # System-level dependencies
    SYSTEM_PACKAGES = {
        'ffmpeg': 'FFmpeg',
        'redis-server': 'Redis Server',
        'psql': 'PostgreSQL',
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Tuple[bool, str]] = {}
    
    def check_python_version(self) -> bool:
        """Check if Python version is 3.11+"""
        version = sys.version_info
        required_version = (3, 11)
        
        if version >= required_version:
            status = f"✓ Python {version.major}.{version.minor}.{version.micro}"
            self.results['python_version'] = (True, status)
            if self.verbose:
                print(status)
            return True
        else:
            status = f"✗ Python {version.major}.{version.minor} (requires 3.11+)"
            self.results['python_version'] = (False, status)
            if self.verbose:
                print(status)
            return False
    
    def check_pip_version(self) -> bool:
        """Check if pip is up to date"""
        try:
            result = subprocess.run(
                ['pip', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                status = f"✓ {result.stdout.strip()}"
                self.results['pip_version'] = (True, status)
                if self.verbose:
                    print(status)
                return True
        except Exception as e:
            status = f"✗ pip not found: {e}"
            self.results['pip_version'] = (False, status)
            if self.verbose:
                print(status)
        return False
    
    def check_package(self, package_name: str, display_name: str) -> bool:
        """Check if a Python package is installed"""
        try:
            __import__(package_name)
            status = f"✓ {display_name}"
            self.results[package_name] = (True, status)
            if self.verbose:
                print(status)
            return True
        except ImportError:
            status = f"✗ {display_name} not installed"
            self.results[package_name] = (False, status)
            if self.verbose:
                print(status)
            return False
    
    def check_required_packages(self) -> Tuple[int, int]:
        """Check all required packages"""
        print("\n📦 Checking Required Packages:")
        print("=" * 50)
        
        installed = 0
        missing = 0
        
        for package, display_name in self.REQUIRED_PACKAGES.items():
            if self.check_package(package, display_name):
                installed += 1
            else:
                missing += 1
        
        return installed, missing
    
    def check_optional_packages(self) -> Tuple[int, int]:
        """Check optional packages"""
        print("\n📦 Checking Optional Packages:")
        print("=" * 50)
        
        installed = 0
        missing = 0
        
        for package, display_name in self.OPTIONAL_PACKAGES.items():
            try:
                __import__(package)
                status = f"✓ {display_name}"
                self.results[package] = (True, status)
                installed += 1
                if self.verbose:
                    print(status)
            except ImportError:
                status = f"○ {display_name} (optional)"
                self.results[package] = (False, status)
                missing += 1
                if self.verbose:
                    print(status)
        
        return installed, missing
    
    def check_system_packages(self) -> Dict[str, bool]:
        """Check system-level packages"""
        print("\n⚙️  Checking System Packages:")
        print("=" * 50)
        
        results = {}
        
        for package, display_name in self.SYSTEM_PACKAGES.items():
            try:
                result = subprocess.run(
                    [package, '--version'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    status = f"✓ {display_name} installed"
                    results[package] = True
                    if self.verbose:
                        print(status)
                else:
                    status = f"✗ {display_name} not found or not in PATH"
                    results[package] = False
                    if self.verbose:
                        print(status)
            except FileNotFoundError:
                status = f"✗ {display_name} not installed"
                results[package] = False
                if self.verbose:
                    print(status)
            except subprocess.TimeoutExpired:
                status = f"✗ {display_name} check timeout"
                results[package] = False
                if self.verbose:
                    print(status)
        
        return results
    
    def run_all_checks(self) -> bool:
        """Run all dependency checks"""
        print("\n" + "=" * 50)
        print("🔍 DEPENDENCY VERIFICATION")
        print("=" * 50)
        
        # Python version
        if not self.check_python_version():
            print("\n❌ Python version is too old. Please install Python 3.11+")
            return False
        
        # pip
        if not self.check_pip_version():
            print("\n❌ pip is not available")
            return False
        
        # Required packages
        req_installed, req_missing = self.check_required_packages()
        
        # Optional packages
        opt_installed, opt_missing = self.check_optional_packages()
        
        # System packages
        sys_results = self.check_system_packages()
        sys_found = sum(1 for v in sys_results.values() if v)
        sys_total = len(sys_results)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        print(f"Required Packages: {req_installed}/{len(self.REQUIRED_PACKAGES)}")
        print(f"Optional Packages: {opt_installed}/{len(self.OPTIONAL_PACKAGES)}")
        print(f"System Packages: {sys_found}/{sys_total}")
        
        all_required = req_missing == 0
        
        if all_required:
            print("\n✅ All required dependencies are installed!")
            if opt_missing > 0:
                print(f"⚠️  {opt_missing} optional packages not installed (non-critical)")
            if sys_total - sys_found > 0:
                print(f"⚠️  {sys_total - sys_found} system packages not installed (recommended)")
        else:
            print(f"\n❌ Missing {req_missing} required package(s)")
            print("\nRun: pip install -r requirements.txt")
        
        return all_required
    
    def get_summary(self) -> Dict:
        """Get check results summary"""
        return {
            'total_checks': len(self.results),
            'passed': sum(1 for v in self.results.values() if v[0]),
            'failed': sum(1 for v in self.results.values() if not v[0]),
            'results': self.results
        }


class DependencyInstaller:
    """Install and update dependencies"""
    
    @staticmethod
    def install_requirements(requirements_file: str = "requirements.txt", verbose: bool = False) -> bool:
        """Install requirements from file"""
        
        if not Path(requirements_file).exists():
            print(f"❌ Requirements file not found: {requirements_file}")
            return False
        
        print(f"\n📦 Installing from {requirements_file}...")
        
        try:
            cmd = [sys.executable, '-m', 'pip', 'install', '-r', requirements_file]
            if not verbose:
                cmd.append('-q')
            
            result = subprocess.run(cmd, capture_output=not verbose)
            
            if result.returncode == 0:
                print(f"✅ Installation successful")
                return True
            else:
                print(f"❌ Installation failed")
                if result.stderr:
                    print(result.stderr.decode())
                return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False
    
    @staticmethod
    def upgrade_pip() -> bool:
        """Upgrade pip to latest version"""
        print("\n🔄 Upgrading pip...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                capture_output=True
            )
            
            if result.returncode == 0:
                print("✅ pip upgraded successfully")
                return True
            else:
                print("❌ pip upgrade failed")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    @staticmethod
    def update_packages() -> bool:
        """Update all installed packages"""
        print("\n🔄 Updating packages...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                import json
                outdated = json.loads(result.stdout)
                print(f"Found {len(outdated)} outdated packages")
                
                for pkg in outdated:
                    print(f"  Updating {pkg['name']}...")
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', '--upgrade', pkg['name']],
                        capture_output=True
                    )
                
                print("✅ Packages updated")
                return True
            else:
                print("❌ Failed to check outdated packages")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    @staticmethod
    def generate_freeze() -> bool:
        """Generate frozen requirements"""
        print("\n📝 Generating frozen requirements...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'freeze'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                with open('requirements-frozen.txt', 'w') as f:
                    f.write(result.stdout)
                print("✅ Frozen requirements saved to requirements-frozen.txt")
                return True
            else:
                print("❌ Failed to generate frozen requirements")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dependency Manager")
    parser.add_argument('--check', action='store_true', help='Check dependencies')
    parser.add_argument('--install', action='store_true', help='Install requirements')
    parser.add_argument('--upgrade-pip', action='store_true', help='Upgrade pip')
    parser.add_argument('--update', action='store_true', help='Update packages')
    parser.add_argument('--freeze', action='store_true', help='Generate frozen requirements')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--requirements', '-r', default='requirements.txt', help='Requirements file')
    
    args = parser.parse_args()
    
    if not any([args.check, args.install, args.upgrade_pip, args.update, args.freeze]):
        args.check = True
    
    if args.check:
        checker = DependencyChecker(verbose=args.verbose)
        if checker.run_all_checks():
            sys.exit(0)
        else:
            sys.exit(1)
    
    if args.upgrade_pip:
        if DependencyInstaller.upgrade_pip():
            sys.exit(0)
        else:
            sys.exit(1)
    
    if args.install:
        if DependencyInstaller.install_requirements(args.requirements, args.verbose):
            sys.exit(0)
        else:
            sys.exit(1)
    
    if args.update:
        if DependencyInstaller.update_packages():
            sys.exit(0)
        else:
            sys.exit(1)
    
    if args.freeze:
        if DependencyInstaller.generate_freeze():
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
