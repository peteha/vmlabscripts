import os
import json
import shutil
import argparse
import requests
import subprocess
from colorama import Fore, Style

## Parameters for Script
customhcl_path = None
customhcl_default_path = "json/customhcl.json"
remote_json_url = "https://partnerweb.vmware.com/service/vsan/all.json"
backup_path = "json/backup/customhcl_backup.json"
cred_path = "~/.pgvm/"


def info_msg(message):
    return f"{Fore.GREEN}[INFO] {message}{Style.RESET_ALL}"

def error_msg(message):
    return f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}"

def prompt_msg(message, txt: bool = True):
    if txt:
        return f"{Fore.YELLOW}[PROMPT] {message}{Style.RESET_ALL}"
    else:
        return f"{Fore.YELLOW}{message}{Style.RESET_ALL}"

def fetch_remote_data(url):
    """
    Fetch JSON data from the provided URL.

    :param url: URL of the JSON data.
    :return: Parsed JSON data.
    """
    try:
        print ( prompt_msg( f"Fetching data from {url}..." ) )
        response = requests.get ( url )
        response.raise_for_status ()
        return response.json ()
    except requests.exceptions.RequestException as e:
        print ( error_msg( f"Error fetching data: {e}") )
        return None


def backup_file(filepath, int_backup_path):
    """
    Create a backup of the provided JSON file.

    :param filepath: Path to the original JSON file.
    :param int_backup_path: Path to save the backup file.
    """
    # Ensure the backup directory exists
    backup_dir = os.path.dirname (int_backup_path)
    if not os.path.exists ( backup_dir ):
        print ( prompt_msg( f"Backup directory '{backup_dir}' does not exist. Creating it..." ) )
        os.makedirs ( backup_dir )

    if os.path.exists ( filepath ):
        print (prompt_msg( f"Backing up {filepath} to {int_backup_path}..."))
        shutil.copy (filepath, int_backup_path)
    else:
        print ( prompt_msg( f"File {filepath} does not exist. Cannot create backup." ) )


def update_json_file(filepath, timestamp, json_updated_time, test_mode=False):
    """
    Update the `timestamp` and `jsonUpdatedTime` values in a JSON file.

    In test mode, the changes are printed but not saved.

    :param filepath: Path to the JSON file to update.
    :param timestamp: New timestamp to replace in the file.
    :param json_updated_time: New jsonUpdatedTime to replace in the file.
    :param test_mode: If True, outputs changes without modifying the file.
    """
    if not os.path.exists ( filepath ):
        print ( error_msg( "File {filepath} not found. Aborting..." ) )
        return

    try:
        # Load the existing data
        with open ( filepath, 'r' ) as outfile:
            data = json.load ( outfile )

        # Prepare the updated data
        updated_data = data.copy ()
        updated_data [ "timestamp" ] = timestamp
        updated_data [ "jsonUpdatedTime" ] = json_updated_time

        if test_mode:
            print ( prompt_msg( "\n[TEST MODE] The file will not be updated. Changes are:" ) )
            print ( prompt_msg( f"  - Old 'timestamp': {data.get ( 'timestamp' )}" ) )
            print ( prompt_msg( f"  - New 'timestamp': {timestamp}" ) )
            print ( prompt_msg( f"  - Old 'jsonUpdatedTime': {data.get ( 'jsonUpdatedTime' )}" ) )
            print ( prompt_msg( f"  - New 'jsonUpdatedTime': {json_updated_time}" ) )
        else:
            # Save the updated JSON data
            with open ( filepath, 'w' ) as outfile:
                json.dump ( updated_data, outfile, indent=4 )
            print ( info_msg( f"File {filepath} successfully updated." ) )
    except Exception as e:
        print ( error_msg( f"Error updating JSON file: {e}" ) )


def apply_to_vcenter(profile, path_customhcl):
    """
    Apply the customhcl.json to the vCenter via REST API.

    :param profile: Name of the profile to use for vCenter credentials.

    :param path_customhcl: Path to the customhcl.json file to apply.
    """
    # Path to credentials
    if profile:
        credentials_path = os.path.expanduser ( f"{cred_path}{profile}/cred.json" )
    else:
        credentials_path = os.path.expanduser ( f"{cred_path}cred.json" )

    # Verify that the credentials file exists
    if not os.path.exists ( credentials_path ):
        print ( prompt_msg( f"Credentials file does not exist for the profile '{profile}'. Expected at: {credentials_path}" ) )
        exit ( 1 )

    # Load credentials
    try:
        with open ( credentials_path, 'r' ) as file:
            creds = json.load ( file )
        vcenter_host = creds["lab"]["vcenter"]["vcenter_server"]
        vcenter_user = creds["lab"]["vcenter"]["vcenter_user"]
        vcenter_password = creds["lab"]["vcenter"]["vcenter_password"]
        print ( prompt_msg( f"Connecting to {vcenter_host}..." ) )
    except Exception as e:
        print ( error_msg ( f"Error loading credentials: {e}" ) )
        exit ( 1 )

    # Ensure all required credentials are available
    if not (vcenter_host and vcenter_user and vcenter_password):
        print ( error_msg ( "Incomplete credentials. Ensure the 'vcenter_host', 'username', and 'password' fields are defined." ) )
        exit ( 1 )

    # Path to the customhcl.json file
    if not os.path.exists ( path_customhcl ):
        print ( error_msg ( f"The HCL file '{path_customhcl}' does not exist." ) )
        exit ( 1 )

    powershell_script_path = "hclvcenter.ps1"  # Replace with the path to your PowerShell script
    try:
        # Build the PowerShell command
        command = [
            "pwsh",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            powershell_script_path,
            vcenter_host,
            vcenter_user,
            vcenter_password,
            path_customhcl
        ]
        # Run the command and capture output
        result = subprocess.run ( command, capture_output=True, text=True )

        # Check the result
        if result.returncode == 0:
            print ( info_msg( "PowerShell script executed successfully." ) )
            print ( info_msg(result.stdout) )
        else:
            print ( error_msg ( "PowerShell script execution failed." ) )
            print ( error_msg ( "Error Output:" ) )
            print ( error_msg ( result.stderr ) )

    except Exception as e:
        print ( error_msg ( f"An error occurred while running the PowerShell script: {e}" ) )
        exit ( 1 )


def prepare_file(source_path, destination_path):
    """
    Copy the customhcl file to the specified destination directory.
    :param source_path: Path to the source customhcl file.
    :param destination_path: Path to the destination customhcl.json file.
    """
    # Ensure the destination directory exists
    destination_dir = os.path.dirname ( destination_path )
    if not os.path.exists ( destination_dir ):
        print ( prompt_msg( "Creating destination directory at {destination_dir}..." ) )
        os.makedirs ( destination_dir )

    if not os.path.exists ( source_path ):
        print ( error_msg ( f"Source file {source_path} does not exist. Exiting..." ) )
        exit ( 1 )

    print ( prompt_msg( f"Copying {source_path} to {destination_path}..." ) )
    shutil.copy ( source_path, destination_path )


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser ( description="Update customhcl.json with remote timestamp and jsonUpdatedTime." )
    parser.add_argument ( "--hcl-path", type=str, default=None, help="Path to the customhcl file." )
    parser.add_argument ( "--test", action="store_true", help="Run the script in test mode (no changes will be made)." )
    parser.add_argument ( "--update-vcenter", action="store_true", help="Apply the custom.hcl to the vCenter." )
    parser.add_argument ( "--profile", type=str, help="Profile to use for vCenter credentials (defaults to ~/.pgvm/cred.json)." )

    args = parser.parse_args ()
    source_hcl_path = args.hcl_path or "customhcl"
    destination_hcl_path = "json/customhcl.json"
    test_mode = args.test
    update_vcenter = args.update_vcenter
    profile = args.profile or ""

    # Ensure profile is provided if --update-vcenter is used

    # Copy customhcl to destination path
    prepare_file ( source_hcl_path, destination_hcl_path )

    # Continue using the destination path for updates
    path_customhcl = destination_hcl_path

    # Fetch data from remote URL
    remote_data = fetch_remote_data ( remote_json_url )
    if not remote_data:
        print ( error_msg( "Failed to fetch remote data. Exiting..." ) )
        return

    # Extract timestamp and jsonUpdatedTime
    timestamp = remote_data.get ( "timestamp" )
    json_updated_time = remote_data.get ( "jsonUpdatedTime" )
    if timestamp is None or json_updated_time is None:
        print ( error_msg ( "Invalid data retrieved from remote JSON. Missing `timestamp` or `jsonUpdatedTime`. Exiting..." ) )
        return
    print ( info_msg( f"Retrieved jsonUpdatedTime: {json_updated_time}" ) )

    # If not in test mode, back up the existing customhcl.json
    if not test_mode:
        backup_file ( path_customhcl, backup_path )

    # Update customhcl.json with new values
    update_json_file ( path_customhcl, timestamp, json_updated_time, test_mode )

    # If the --update-vcenter flag is set, apply the JSON to vCenter
    if update_vcenter:
        apply_to_vcenter ( profile, path_customhcl )


if __name__ == "__main__":
    main ()
