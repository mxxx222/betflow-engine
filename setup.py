"""
Setup script for BetFlow Engine Python package.
Creates distributable wheel for the engine.
"""

from setuptools import setup, find_packages
import os

# Read version from engine/__init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'engine', '__init__.py')
    with open(version_file, 'r') as f:
        for line in f:
            if line.startswith('Version:'):
                return line.split(':')[1].strip()
    return "0.9.0"

# Read README
def get_long_description():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "BetFlow Engine - High-performance sports analytics calculations"

setup(
    name="betflow-engine",
    version="0.9.0",
    author="BetFlow Team",
    author_email="team@betflow-engine.com",
    description="High-performance sports analytics calculation engine with Mojo acceleration",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/betflow/betflow-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.24.0",
        "dataclasses-json>=0.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "mojo": [
            # Mojo dependencies when available
        ],
    },
    include_package_data=True,
    package_data={
        "engine": ["*.mojo", "*.so", "*.dylib", "*.dll"],
    },
    entry_points={
        "console_scripts": [
            "betflow-benchmark=engine.benchmarks:run_ci_benchmarks",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/betflow/betflow-engine/issues",
        "Source": "https://github.com/betflow/betflow-engine",
        "Documentation": "https://docs.betflow-engine.com",
    },
)
