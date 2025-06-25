# -*- coding: utf-8 -*-
"""
WADE Version Information
"""

__version__ = "3.0.0"
__version_info__ = (3, 0, 0)
__build__ = "production"
__release_date__ = "2024-06-24"
__codename__ = "Dragon Edition"

# Version components
MAJOR = 3
MINOR = 0
PATCH = 0

# Build information
BUILD_TYPE = "production"
BUILD_DATE = "2024-06-24"
BUILD_COMMIT = "initial"

# Feature flags
FEATURES = {
    "security_enhanced": True,
    "cyber_dashboard": True,
    "advanced_monitoring": True,
    "auto_backup": True,
    "error_recovery": True,
    "docker_support": True,
    "ci_cd_pipeline": True,
}


def get_version():
    """Get the current version string."""
    return __version__


def get_version_info():
    """Get detailed version information."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "build": __build__,
        "release_date": __release_date__,
        "codename": __codename__,
        "features": FEATURES,
    }


def print_version():
    """Print version information."""
    print(f"WADE {__version__} ({__codename__})")
    print(f"Build: {__build__}")
    print(f"Release Date: {__release_date__}")
    print(f"Features: {', '.join([k for k, v in FEATURES.items() if v])}")


if __name__ == "__main__":
    print_version()
