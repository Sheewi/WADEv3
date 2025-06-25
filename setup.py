#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WADE v3.0 Setup Configuration
Production-ready setup for Weaponized Autonomous Digital Entity
"""

from setuptools import setup, find_packages
import os

# Read version from version.txt
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'version.txt')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            return f.read().strip()
    return '3.0.0'

# Read long description from README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return 'WADE - Weaponized Autonomous Digital Entity v3.0'

# Read requirements from requirements.txt
def get_requirements():
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="wade",
    version=get_version(),
    author="WADE Development Team",
    author_email="dev@wade-ai.org",
    description="Weaponized Autonomous Digital Entity - Advanced AI Agent Framework",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Sheewi/WADEv3",
    project_urls={
        "Bug Tracker": "https://github.com/Sheewi/WADEv3/issues",
        "Documentation": "https://github.com/Sheewi/WADEv3/docs",
        "Source Code": "https://github.com/Sheewi/WADEv3",
    },
    packages=find_packages(exclude=['tests*', 'docs*', 'backup*']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=get_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.2.0',
            'pytest-cov>=4.0.0',
            'pytest-xdist>=3.1.0',
            'pytest-mock>=3.10.0',
            'pytest-asyncio>=0.20.0',
            'pytest-benchmark>=4.0.0',
            'black>=22.12.0',
            'isort>=5.11.0',
            'flake8>=6.0.0',
            'mypy>=0.991',
            'pylint>=2.15.0',
            'bandit>=1.7.0',
            'safety>=2.3.0',
        ],
        'docs': [
            'sphinx>=5.3.0',
            'sphinx-rtd-theme>=1.2.0',
            'myst-parser>=0.18.0',
        ],
        'security': [
            'cryptography>=38.0.0',
            'pycryptodome>=3.19.0',
            'bcrypt>=4.0.0',
            'pyjwt>=2.6.0',
            'paramiko>=3.3.0',
        ],
        'monitoring': [
            'psutil>=5.9.0',
            'prometheus-client>=0.15.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'wade=wade.main:main',
            'wade-cli=wade.interface.cli_handler:main',
            'wade-server=wade.WADE_CORE.main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'wade': [
            'resources/*',
            'resources/configs/*',
            'resources/templates/*',
        ],
    },
    zip_safe=False,
)