#!/bin/bash
# Package Wade with Crew AI files for distribution

set -e

echo "Packaging Wade with Crew AI files..."

# Create version file
VERSION="1.0.0"
echo $VERSION > /workspace/simple-wade/version.txt

# Create package directory
PACKAGE_DIR="/tmp/wade-crew-package"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Copy files
cp -r /workspace/simple-wade/* $PACKAGE_DIR/

# Create tarball
cd /tmp
tar -czf wade-crew-$VERSION.tar.gz wade-crew-package

echo "Package created: /tmp/wade-crew-$VERSION.tar.gz"
echo "You can distribute this package and use it to create a custom Kali ISO."
