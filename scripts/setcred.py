import json
import os
import shutil
from colorama import Fore, Style

# Configuration Parameters
BACKUP_LIMIT = 5  # Number of backups to retain
DEFAULT_DIRECTORY = "./"  # Default directory to store backups


def create_backup(base_cred_path, backup_dir):
    # Create the directory if it does not exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    backup_files = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith("backup_")],
        key=lambda x: os.path.getmtime(os.path.join(backup_dir, x))
    )

    # Remove oldest backups if exceeding the limit
    while len(backup_files) >= BACKUP_LIMIT:
        os.remove(os.path.join(backup_dir, backup_files.pop(0)))

    # Create a new backup
    backup_file = os.path.join(backup_dir, f"backup_{len(backup_files) + 1}.json")
    shutil.copy2(base_cred_path, backup_file)
    print(Fore.GREEN + f"[INFO] Backup created at: {backup_file}" + Style.RESET_ALL)


def merge_json(json_template_path, base_cred_path, is_test=False):
    backup_dir = os.path.join(os.path.dirname(base_cred_path), "backup")
    base_data = {}

    # Check if `base-cred` exists; if not, confirm creation
    if not os.path.exists(base_cred_path):
        print(Fore.RED + f"[ERROR] File {base_cred_path} does not exist." + Style.RESET_ALL)
        create_new = input(Fore.GREEN + "[PROMPT] Would you like to create it? (yes/no): " + Style.RESET_ALL).lower()
        if create_new != "yes":
            return
        os.makedirs(os.path.dirname(base_cred_path), exist_ok=True)
        with open(base_cred_path, "w") as new_file:
            new_file.write("{}")  # Create an empty JSON file
        print(Fore.GREEN + f"[INFO] Created file: {base_cred_path}" + Style.RESET_ALL)

    # Load the `base-cred` JSON data
    if os.path.exists(base_cred_path):
        with open(base_cred_path, "r") as base_file:
            try:
                base_data = json.load(base_file)
            except json.JSONDecodeError:
                print(Fore.RED + "[ERROR] Invalid JSON format in base-cred file." + Style.RESET_ALL)
                return

    # Load the `json-template` JSON data
    with open(json_template_path, "r") as template_file:
        try:
            template_data = json.load(template_file)
        except json.JSONDecodeError:
            print(Fore.RED + "[ERROR] Invalid JSON format in json-template file." + Style.RESET_ALL)
            return

    changes = {}

    # Compare and merge JSON structures
    def recursive_merge(template, base, path=""):
        for key, value in template.items():
            full_path = f"{path}.{key}" if path else key

            if key not in base:
                # Handle new keys
                if isinstance(value, dict):
                    # Add empty object for missing dictionary
                    base[key] = {}
                    print(
                        Fore.GREEN + f"[INFO] Added new dictionary key: '{full_path}' with value: {{}} " + Style.RESET_ALL)
                elif isinstance(value, list):
                    # Prompt user to define list values
                    print(
                        Fore.GREEN + f"[PROMPT] Key '{full_path}' is an empty list. Add items now? (yes/no): " + Style.RESET_ALL)
                    add_items = input().lower()
                    if add_items == "yes":
                        base[key] = []
                        item_count = int(input(Fore.GREEN + "How many items? " + Style.RESET_ALL))
                        for i in range(item_count):
                            item_key = input(Fore.GREEN + f"Item {i + 1} key: " + Style.RESET_ALL)
                            item_value = input(Fore.GREEN + f"Item {i + 1} value: " + Style.RESET_ALL)
                            base[key].append({item_key: item_value})
                    else:
                        base[key] = []
                    print(
                        Fore.GREEN + f"[INFO] Added new list key: '{full_path}' with value: {base[key]}" + Style.RESET_ALL)
                elif value in ("", 0, False):
                    # Placeholder value, prompt the user
                    print(
                        Fore.GREEN + f"[PROMPT] Key '{full_path}' has a placeholder value ({value}). Enter a new value or press Enter to keep it: " + Style.RESET_ALL)
                    new_value = input()
                    base[key] = value if new_value == "" else new_value
                    print(Fore.GREEN + f"[INFO] Added new key: '{full_path}' with value: {base[key]}" + Style.RESET_ALL)
                else:
                    # Add scalar values directly
                    base[key] = value
                    print(Fore.GREEN + f"[INFO] Added new key: '{full_path}' with value: {base[key]}" + Style.RESET_ALL)
                changes[full_path] = value
            elif isinstance(value, dict) and isinstance(base[key], dict):
                recursive_merge(value, base[key], full_path)
            elif isinstance(value, list) and isinstance(base[key], list):
                # Merge lists if needed (optional logic for your use case)
                pass
            else:
                # Highlight existing value in yellow
                print(
                    Fore.YELLOW + f"[INFO] Key '{full_path}' already exists in base-cred with value: {base[key]}" + Style.RESET_ALL)

    recursive_merge(template_data, base_data)

    # Print differences in `test` mode
    if is_test:
        print(Fore.GREEN + "[INFO] The following changes would be made to base-cred:" + Style.RESET_ALL)
        print(json.dumps(changes, indent=4))
    else:
        # Create a backup and write the merged data
        create_backup(base_cred_path, backup_dir)
        with open(base_cred_path, "w") as base_file:
            json.dump(base_data, base_file, indent=4)
        print(Fore.GREEN + f"[INFO] Updated base-cred successfully at {base_cred_path}" + Style.RESET_ALL)


# CLI Entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare and merge JSON files.")
    parser.add_argument("--json-template", required=True, help="Path to the JSON template file.")
    parser.add_argument("--base-cred", required=True, help="Path to the base credentials JSON file.")
    parser.add_argument("--test", action="store_true", help="Show the differences without making changes.")
    args = parser.parse_args()

    merge_json(args.json_template, args.base_cred, is_test=args.test)
