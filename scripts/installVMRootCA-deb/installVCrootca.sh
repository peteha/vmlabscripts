#!/bin/bash

# Default profile location
default_profile="$HOME/.pgvm/cred.json"

# Get the profile argument or use the default
profile=${1:-"default"}
if [ "$profile" != "default" ]; then
    cred_file="$HOME/.pgvm/$profile/cred.json"
else
    cred_file="$default_profile"
fi

# Ensure the credentials file exists
if [ ! -f "$cred_file" ]; then
    echo "Error: Credentials file not found at $cred_file"
    exit 1
fi

# Read the vCenter server address from the JSON file
vcenter_server=$(jq -r '.vcenter.VCENTER_SERVER' "$cred_file")
if [ -z "$vcenter_server" ] || [ "$vcenter_server" == "null" ]; then
    echo "Error: 'VCENTER_SERVER' not found in $cred_file"
    exit 1
fi

# Prepare the download URL
download_url="https://$vcenter_server/certs/download.zip"

# Temporary directory for the downloaded and unzipped files
temp_dir=$(mktemp -d)

# Setup the download destination
download_file="$temp_dir/download.zip"

# Download the ZIP file, ignoring certificate warnings
echo "Downloading $download_url..."
curl -k -o "$download_file" "$download_url"
if [ $? -ne 0 ]; then
    echo "Error: Failed to download $download_url"
    rm -rf "$temp_dir"
    exit 1
fi

# Unzip the download file
echo "Unzipping $download_file..."
unzip -q "$download_file" -d "$temp_dir"
if [ $? -ne 0 ]; then
    echo "Error: Failed to unzip $download_file"
    rm -rf "$temp_dir"
    exit 1
fi

# Path to the certificates
certs_dir="$temp_dir/certs/win"

# Ensure certificates directory exists
if [ ! -d "$certs_dir" ]; then
    echo "Error: Certificates directory not found in extracted files"
    rm -rf "$temp_dir"
    exit 1
fi

# Add the .crt files to the trusted CA store
crt_files=($(find "$certs_dir" -name '*.crt'))

if [ ${#crt_files[@]} -eq 0 ]; then
    echo "Error: No .crt files found in $certs_dir"
    rm -rf "$temp_dir"
    exit 1
fi

echo "Adding certificates to the trusted CA store..."
for crt_file in "${crt_files[@]}"; do
    echo "Adding $crt_file to the trusted store..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # For Linux
        sudo cp "$crt_file" /usr/local/share/ca-certificates/
        sudo update-ca-certificates
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # For macOS
        sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$crt_file"
    elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* ]]; then
        # For Windows with OpenSSL (example)
        certutil -addstore -f "Root" "$crt_file"
    else
        echo "Unsupported OS. Please add $crt_file manually to your trusted CA store."
    fi
done

# Cleanup
rm -rf "$temp_dir"

echo "Certificates added successfully!"