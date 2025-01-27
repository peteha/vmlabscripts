import os
import json
import shutil
from datetime import datetime
import argparse

# Base directory
BASE_DIR = os.path.expanduser ( "~/.pgvm/" )
BACKUP_DIRNAME = "backup"
MAX_BACKUPS = 10
# Get the directory of the current script
SCRIPT_DIR = os.path.dirname ( os.path.abspath ( __file__ ) )
# ANSI escape codes for better visual appearance
BOLD_YELLOW = "\033[1;33m"  # Bold Yellow
RESET_COLOR = "\033[0m"  # Reset to default terminal color


def get_directories(base_dir):
    """Fetch list of profile directories."""
    return [ d for d in os.listdir ( base_dir ) if os.path.isdir ( os.path.join ( base_dir, d ) ) ]


def create_profile(base_dir, profile_name):
    """Create a new profile directory."""
    profile_path = os.path.join ( base_dir, profile_name )
    os.makedirs ( profile_path, exist_ok=True )
    return profile_path


def load_json(file_path):
    """Load JSON file from the given path."""
    try:
        with open ( file_path, "r" ) as f:
            return json.load ( f )
    except FileNotFoundError:
        print ( f"Error: JSON file not found at {file_path}. Exiting." )
        exit ( 1 )


def save_json(file_path, data):
    """Save data as JSON to the given path."""
    with open ( file_path, "w" ) as f:
        json.dump ( data, f, indent=4 )


def take_backup(profile_path):
    """Take a backup of the existing cred.json and manage backups."""
    cred_file = os.path.join ( profile_path, "cred.json" )
    if not os.path.exists ( cred_file ):
        return  # No file to back up

    backup_dir = os.path.join ( profile_path, BACKUP_DIRNAME )
    os.makedirs ( backup_dir, exist_ok=True )

    # Old backups
    backups = sorted ( os.listdir ( backup_dir ) )
    if len ( backups ) >= MAX_BACKUPS:
        oldest_backup = os.path.join ( backup_dir, backups [ 0 ] )
        os.remove ( oldest_backup )

    # Save new backup
    timestamp = datetime.now ().strftime ( "%Y%m%d%H%M%S" )
    backup_name = f"cred_{timestamp}.json"
    shutil.copy ( cred_file, os.path.join ( backup_dir, backup_name ) )


def display_in_bold_yellow(text):
    """Display the given text in bold yellow."""
    return f"{BOLD_YELLOW}{text}{RESET_COLOR}"


def verify_parameters(existing, base):
    """Verify and update parameters with the user."""
    updated = existing.copy ()
    for key, value in base.items ():
        # If it's a dictionary, handle deep verification
        if isinstance ( value, dict ):
            updated [ key ] = verify_parameters ( existing.get ( key, {} ), value )
        elif isinstance ( value, list ):  # Handle list values
            existing_value = existing.get ( key, value )
            print ( f"Existing value for {key}: {display_in_bold_yellow ( existing_value )}" )
            print ( f"Enter values for {key} (comma-separated). Leave empty to keep the existing list:" )
            new_values = input ( f"> " ).strip ()
            if new_values:  # Only update if user provides input
                updated [ key ] = [ item.strip () for item in new_values.split ( "," ) ]
            else:
                updated [ key ] = existing_value
        else:
            # Ask for basic reassignment
            existing_value = existing.get ( key, value )
            print ( f"Existing value for {key}: {display_in_bold_yellow ( existing_value )}" )
            new_value = input ( f"Provide updated value for {key} (leave empty to keep existing): " ).strip ()
            updated [ key ] = new_value if new_value else existing_value

    return updated


def load_base_structure(base_structure_file):
    """Load the BASE_STRUCTURE from the specified file."""
    # print(base_structure_file)
    if not os.path.exists ( base_structure_file ):
        print ( "Script does not require credentials" )
        return None
    return load_json ( base_structure_file )





def main():
    parser = argparse.ArgumentParser ( description="Manage script credentials" )
    parser.add_argument (
        "--script",
        type=str,
        default="",
        help="Prefix for the base credential JSON file (default: '')"
    )
    args = parser.parse_args ()

    # Dynamic base structure file path based on the argument
    base_structure_file = os.path.join ( SCRIPT_DIR, f"scripts/{args.script}", f"{args.script}-cred.json" )

    # Load the base structure
    base_structure = load_base_structure ( base_structure_file )
    if not base_structure:
        return  # Exit if the base file doesn't exist

    if not os.path.exists ( BASE_DIR ):
        os.makedirs ( BASE_DIR )

    profiles = get_directories ( BASE_DIR )
    print ( "Available profiles:" )
    for i, profile in enumerate ( profiles ):
        print ( f"{i + 1}. {profile}" )

    print ( "\nOptions:" )
    print ( "n. Create a new profile" )
    choice = input ( "Choose an existing profile by number or type 'n' to create a new one: " ).strip ()

    if choice.lower () == 'n':
        profile_name = input ( "Enter name for the new profile: " ).strip ()
        profile_path = create_profile ( BASE_DIR, profile_name )
        print ( f"Created new profile: {profile_name}" )

        # Get values for the new cred.json file
        print ( "Provide values for the following parameters:" )
        new_values = verify_parameters ( {}, base_structure )

        # Save the file
        cred_file = os.path.join ( profile_path, "cred.json" )
        save_json ( cred_file, new_values )

        print ( f"Saved credentials to {cred_file}" )
    else:
        try:
            profile_index = int ( choice ) - 1
            if profile_index < 0 or profile_index >= len ( profiles ):
                raise ValueError

            profile_name = profiles [ profile_index ]
            profile_path = os.path.join ( BASE_DIR, profile_name )
            cred_file = os.path.join ( profile_path, "cred.json" )

            # Load existing file and process
            existing_data = load_json ( cred_file )
            if existing_data:
                print ( f"Loaded existing cred.json for {profile_name}" )
                updated_data = verify_parameters ( existing_data, base_structure )

                # Take a backup
                take_backup ( profile_path )

                # Save updated data
                save_json ( cred_file, updated_data )
                print ( f"Updated credentials saved to {cred_file}" )
            else:
                print ( "No existing cred.json found. Creating a new one." )
                new_values = verify_parameters ( {}, base_structure )
                save_json ( cred_file, new_values )

        except (ValueError, IndexError):
            print ( "Invalid choice. Exiting." )


if __name__ == "__main__":
    main ()

