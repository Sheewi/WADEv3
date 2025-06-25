#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WADE Setup Configuration
"""

from setuptools import setup, find_packages
import os
import sys


# Read version from version file
def get_version():
    version_file = os.path.join("WADE_CORE", "version.py")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            content = f.read()
            for line in content.split("\n"):
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "3.0.0"


# Read long description from README
def get_long_description():
    readme_path = os.path.join("..", "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    elif os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    return "WADE - Weaponized Autonomous Deployment Engine"


# Read requirements
def get_requirements():
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        with open(req_file, "r") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


setup(
    name="wade",
    version=get_version(),
    author="WADE Team",
    author_email="wade@wade.systems",
    description="Weaponized Autonomous Deployment Engine - Advanced AI-driven system management",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Sheewi/WADEv3",
    project_urls={
        "Bug Tracker": "https://github.com/Sheewi/WADEv3/issues",
        "Documentation": "https://wade.readthedocs.io/",
        "Source Code": "https://github.com/Sheewi/WADEv3",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.1.0",
            "pytest-mock>=3.10.0",
            "black>=22.12.0",
            "isort>=5.11.0",
            "flake8>=6.0.0",
            "mypy>=0.991",
            "pylint>=2.15.0",
        ],
        "security": [
            "bandit>=1.7.0",
            "safety>=2.3.0",
        ],
        "docs": [
            "sphinx>=5.3.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=0.18.0",
        ],
        "monitoring": [
            "prometheus-client>=0.15.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wade=WADE_CORE.main:main",
            "wade-bootloader=interface.bootloader:main",
            "wade-dashboard=interface.cyber_dashboard:main",
            "wade-monitor=system.monitor:main",
            "wade-backup=system.backup_manager:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.conf", "*.cfg"],
        "WADE_CORE": ["config/*.json"],
        "security": ["certs/*.pem", "certs/*.crt"],
        "interface": ["assets/*", "themes/*"],
    },
    zip_safe=False,
    keywords="automation deployment security monitoring ai system-administration",
    platforms=["any"],
)
