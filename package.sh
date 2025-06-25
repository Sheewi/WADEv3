#!/bin/bash
# Package Simple Wade files for distribution

set -e

echo "Packaging Simple Wade files..."

# Create version file
VERSION="1.0.0"
echo $VERSION > /workspace/simple-wade/version.txt

# Create package directory
PACKAGE_DIR="/tmp/simple-wade-package"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Copy files
cp -r /workspace/simple-wade/* $PACKAGE_DIR/

# Create tarball
cd /tmp
tar -czf simple-wade-$VERSION.tar.gz simple-wade-package

echo "Package created: /tmp/simple-wade-$VERSION.tar.gz"
echo "You can distribute this package and use it to create a custom Kali ISO."
