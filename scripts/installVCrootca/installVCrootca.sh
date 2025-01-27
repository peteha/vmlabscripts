#!/bin/bash

# Function to display the help message
show_help() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "A script to install vCenter root certificates."
    echo ""
    echo "Options:"
    echo "  -p, --profile PROFILE  Specify the profile name for credentials (default: 'default')."
    echo "  -y, --yes              Automatically install missing dependencies without prompting."
    echo "  -h, --help             Show this help message and exit."
    exit 0
}

# Check if a command exists
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        return 1 # Dependency is missing
    else
        return 0 # Dependency is present
    fi
}

# Special check for certutil, since it behaves differently across platforms
check_certutil() {
    if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* ]]; then
        # Certutil is typically available on Windows systems; check for its presence
        if ! command -v certutil &> /dev/null; then
            return 1
        fi
    else
        # Certutil might not apply on non-Windows systems like macOS or Linux
        if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
            echo "Note: 'certutil' is not required on Linux or macOS. Skipping its check."
            return 0 # Consider it as available
        fi
    fi
    return 0
}

# Install a missing dependency
install_dependency() {
    case "$OSTYPE" in
        linux-gnu*)
            if command -v apt-get &> /dev/null; then
                echo "Attempting to install '$1' using apt-get..."
                sudo apt-get update && sudo apt-get install -y "$1"
            elif command -v yum &> /dev/null; then
                echo "Attempting to install '$1' using yum..."
                sudo yum install -y "$1"
            else
                echo "Error: Package manager not supported for this OS. Please install '$1' manually."
                exit 1
            fi
            ;;
        darwin*)
            if command -v brew &> /dev/null; then
                echo "Attempting to install '$1' using Homebrew..."
                brew install "$1"
            else
                echo "Error: Homebrew is not installed. Please install '$1' manually or install Homebrew first."
                exit 1
            fi
            ;;
        msys*|cygwin*)
            echo "Error: Automated installation of '$1' not supported on Windows. Please install it manually."
            exit 1
            ;;
        *)
            echo "Error: Unsupported OS. Please install '$1' manually."
            exit 1
            ;;
    esac
}

# Check and prompt to install missing dependencies
ensure_dependencies() {
    dependencies=("jq" "curl" "unzip" "find")
    missing_dependencies=()

    # Check all standard dependencies first
    for dep in "${dependencies[@]}"; do
        if ! check_dependency "$dep"; then
            missing_dependencies+=("$dep")
        fi
    done

    # Check certutil separately
    if ! check_certutil; then
        missing_dependencies+=("certutil")
    fi

    if [ ${#missing_dependencies[@]} -gt 0 ]; then
        echo "The following dependencies are missing: ${missing_dependencies[*]}"
        if [ "$auto_confirm" = true ]; then
            confirm="y"
        else
            read -p "Would you like to attempt to install them now? (y/n): " confirm
        fi

        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            for dep in "${missing_dependencies[@]}"; do
                install_dependency "$dep"
            done
        else
            echo "Error: Missing dependencies. Please install them manually and re-run the script."
            exit 1
        fi
    fi
}

# Default values for arguments
profile="default"
auto_confirm=false

# Parse arguments with getopts
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -p|--profile)
            profile="$2"
            shift 2
            ;;
        -y|--yes)
            auto_confirm=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Error: Invalid argument '$1'"
            show_help
            ;;
    esac
done

# Ensure the script is run with sudo/root privileges
check_sudo

# Default profile location
default_profile="$HOME/.pgvm/cred.json"
cred_file=${default_profile}

# Custom profile file location (if given)
if [ "$profile" != "default" ]; then
    cred_file="$HOME/.pgvm/$profile/cred.json"
fi

# Ensure necessary dependencies are installed
ensure_dependencies

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