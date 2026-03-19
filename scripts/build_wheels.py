#!/usr/bin/env python3
"""
Build script for BetFlow Engine v0.9.0 wheels and distribution packages.
Creates pre-built wheels for different platforms and Python versions.
"""

import os
import sys
import subprocess
import shutil
import tempfile
import argparse
from pathlib import Path
from typing import List, Dict, Any

def run_command(cmd: List[str], cwd: str = None) -> bool:
    """Run a command and return success status."""
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def build_source_distribution(project_root: Path) -> bool:
    """Build source distribution."""
    print("Building source distribution...")
    
    # Clean previous builds
    dist_dir = project_root / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    build_dir = project_root / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Build source distribution
    return run_command([
        sys.executable, "-m", "build", "--sdist", str(project_root)
    ])

def build_wheel_distribution(project_root: Path, python_versions: List[str] = None) -> bool:
    """Build wheel distributions for specified Python versions."""
    print("Building wheel distributions...")
    
    if python_versions is None:
        python_versions = ["3.11"]
    
    success = True
    
    for py_version in python_versions:
        print(f"Building wheel for Python {py_version}...")
        
        # Use current Python for now (in production, would use multiple Python versions)
        cmd = [sys.executable, "-m", "build", "--wheel", str(project_root)]
        
        if not run_command(cmd):
            success = False
            print(f"Failed to build wheel for Python {py_version}")
    
    return success

def create_requirements_lock(project_root: Path) -> bool:
    """Create locked requirements file."""
    print("Creating locked requirements file...")
    
    # Install pip-tools if not available
    try:
        import pip_tools
    except ImportError:
        print("Installing pip-tools...")
        if not run_command([sys.executable, "-m", "pip", "install", "pip-tools"]):
            return False
    
    # Generate locked requirements
    requirements_in = project_root / "requirements.txt"
    requirements_lock = project_root / "requirements-lock.txt"
    
    if requirements_in.exists():
        return run_command([
            sys.executable, "-m", "piptools", "compile",
            "--generate-hashes",
            "--output-file", str(requirements_lock),
            str(requirements_in)
        ])
    
    return True

def validate_wheel(wheel_path: Path) -> bool:
    """Validate built wheel."""
    print(f"Validating wheel: {wheel_path}")
    
    # Check wheel contents
    if not run_command([sys.executable, "-m", "wheel", "unpack", str(wheel_path)]):
        return False
    
    # Install and test wheel in temporary environment
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = Path(temp_dir) / "test_env"
        
        # Create virtual environment
        if not run_command([sys.executable, "-m", "venv", str(venv_dir)]):
            return False
        
        # Determine python executable in venv
        if sys.platform == "win32":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        
        # Install wheel
        if not run_command([str(python_exe), "-m", "pip", "install", str(wheel_path)]):
            return False
        
        # Test import
        test_script = """
import sys
try:
    from engine import BetFlowEngine
    engine = BetFlowEngine()
    health = engine.health_check()
    print(f"Engine status: {health['status']}")
    print("Wheel validation successful")
    sys.exit(0)
except Exception as e:
    print(f"Wheel validation failed: {e}")
    sys.exit(1)
"""
        
        return run_command([str(python_exe), "-c", test_script])

def create_docker_build_image(project_root: Path) -> bool:
    """Create Docker image for building wheels across platforms."""
    print("Creating Docker build image...")
    
    dockerfile_content = """
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Install Python build tools
RUN pip install --no-cache-dir \\
    build \\
    wheel \\
    setuptools \\
    pip-tools \\
    twine

WORKDIR /workspace

# Copy project files
COPY . .

# Build wheels
RUN python -m build --wheel --sdist

# Validate wheels
RUN python scripts/build_wheels.py --validate-only

CMD ["python", "scripts/build_wheels.py", "--build-all"]
"""
    
    dockerfile_path = project_root / "Dockerfile.build"
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)
    
    # Build Docker image
    return run_command([
        "docker", "build",
        "-f", str(dockerfile_path),
        "-t", "betflow-engine-builder:0.9.0",
        str(project_root)
    ])

def upload_to_registry(project_root: Path, registry_url: str = None) -> bool:
    """Upload built packages to package registry."""
    print("Uploading packages to registry...")
    
    dist_dir = project_root / "dist"
    if not dist_dir.exists():
        print("No dist directory found. Run build first.")
        return False
    
    # List built packages
    packages = list(dist_dir.glob("*.whl")) + list(dist_dir.glob("*.tar.gz"))
    if not packages:
        print("No packages found to upload.")
        return False
    
    print(f"Found {len(packages)} packages to upload:")
    for package in packages:
        print(f"  {package.name}")
    
    # Upload using twine (would need credentials configured)
    if registry_url:
        cmd = [
            sys.executable, "-m", "twine", "upload",
            "--repository-url", registry_url,
            *[str(p) for p in packages]
        ]
    else:
        # Upload to PyPI (test or production)
        cmd = [
            sys.executable, "-m", "twine", "upload",
            "--repository", "testpypi",  # Use testpypi for testing
            *[str(p) for p in packages]
        ]
    
    print("Note: Upload requires proper authentication configuration")
    print(f"Command would be: {' '.join(cmd)}")
    
    # Don't actually upload in this example
    return True

def generate_build_info(project_root: Path) -> bool:
    """Generate build information file."""
    print("Generating build information...")
    
    import json
    from datetime import datetime
    
    # Get git information
    try:
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], 
            cwd=project_root, 
            text=True
        ).strip()
        git_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
            cwd=project_root, 
            text=True
        ).strip()
    except:
        git_hash = "unknown"
        git_branch = "unknown"
    
    build_info = {
        "version": "0.9.0",
        "build_date": datetime.utcnow().isoformat(),
        "git_hash": git_hash,
        "git_branch": git_branch,
        "python_version": sys.version,
        "platform": sys.platform,
        "build_system": "setuptools + build",
        "features": {
            "mojo_support": True,
            "opentelemetry": True,
            "prometheus": True,
            "slack_alerts": True,
            "bulk_api": True
        }
    }
    
    build_info_path = project_root / "dist" / "build_info.json"
    build_info_path.parent.mkdir(exist_ok=True)
    
    with open(build_info_path, "w") as f:
        json.dump(build_info, f, indent=2)
    
    print(f"Build info written to {build_info_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Build BetFlow Engine distribution packages")
    parser.add_argument("--build-all", action="store_true", help="Build all distribution types")
    parser.add_argument("--source-only", action="store_true", help="Build source distribution only")
    parser.add_argument("--wheel-only", action="store_true", help="Build wheel distribution only")
    parser.add_argument("--validate-only", action="store_true", help="Validate existing wheels only")
    parser.add_argument("--upload", action="store_true", help="Upload to package registry")
    parser.add_argument("--registry-url", help="Custom registry URL")
    parser.add_argument("--python-versions", nargs="+", default=["3.11"], help="Python versions to build for")
    parser.add_argument("--docker-build", action="store_true", help="Create Docker build image")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    print(f"Building BetFlow Engine v0.9.0 from {project_root}")
    
    success = True
    
    if args.validate_only:
        # Validate existing wheels
        dist_dir = project_root / "dist"
        wheels = list(dist_dir.glob("*.whl"))
        
        if not wheels:
            print("No wheels found to validate")
            return 1
        
        for wheel in wheels:
            if not validate_wheel(wheel):
                success = False
        
        return 0 if success else 1
    
    if args.docker_build:
        success = create_docker_build_image(project_root)
        if not success:
            return 1
    
    if args.build_all or args.source_only:
        success &= build_source_distribution(project_root)
    
    if args.build_all or args.wheel_only:
        success &= build_wheel_distribution(project_root, args.python_versions)
    
    if success:
        success &= generate_build_info(project_root)
    
    if success:
        success &= create_requirements_lock(project_root)
    
    # Validate built wheels
    if success and (args.build_all or args.wheel_only):
        dist_dir = project_root / "dist"
        wheels = list(dist_dir.glob("*.whl"))
        
        for wheel in wheels:
            if not validate_wheel(wheel):
                success = False
                break
    
    if success and args.upload:
        success &= upload_to_registry(project_root, args.registry_url)
    
    if success:
        print("\n✅ Build completed successfully!")
        
        # Show built packages
        dist_dir = project_root / "dist"
        if dist_dir.exists():
            packages = list(dist_dir.glob("*"))
            print(f"\nBuilt packages ({len(packages)}):")
            for package in packages:
                size = package.stat().st_size / 1024  # KB
                print(f"  {package.name} ({size:.1f} KB)")
    else:
        print("\n❌ Build failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
