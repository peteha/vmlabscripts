# VM Lab Scripts 

A collection of my lab scripts used for VMware labs including VCF.

Included with the scripts is a process to create the credentials required for each of them. 

## credbuilder

The **`credbuilder.py` **script is designed to **manage credentials** for various profiles, providing users with the ability to create, update, and maintain credential files (`cred.json`). These credentials are often used by other scripts, such as those interacting with APIs or systems like vCenter. The script features robust handling for multiple profiles, backup management, and user input to customize the stored credentials.
### Key Features
1. **Profile Management**:
    - Credentials are organized in profiles stored under the `~/.pgvm/` directory.
    - Users can choose existing profiles or create new ones.
    - Each profile contains a `cred.json` file that holds the credentials.

2. **Interactive Credential Input**:
    - Users are prompted to review or modify values in `cred.json` during updates.
    - Parameters are loaded from a base structure file (specific to the script being used, like `script-cred.json`).
    - Fields can be edited, and defaults are retained if left unchanged.

3. **Backup Management**:
    - Before updating `cred.json`, the script automatically takes backups.
    - Old backups are stored in the `backup` directory inside the profile folder.
    - The script retains a maximum of 10 backups, deleting older ones when necessary.

4. **Dynamic Credential Structure**:
    - The script dynamically loads the expected credential fields (`base_structure`) from a JSON template file (`script-cred.json`). This template is customizable for different use cases.
    - E.g., If used with vCenter, the base structure may have fields like `VCENTER_SERVER`, `VCENTER_USER`, and `VCENTER_PASSWORD`.

5. **User-Friendly Interaction**:
    - Displays available profiles for selection.
    - Guides users through credential updates interactively using clear inputs and prompts.

6. **Command-Line Support**:
    - Users can specify a `--script` parameter to load credentials for a specific script (looks for `scripts/<script>/<script>-cred.json`).
    - Provides flexibility for integrating with different tools and workflows.

7. **Error Handling**:
    - Gracefully handles missing directories, files, and invalid inputs.
    - Ensures the process exits cleanly with helpful error messages.

### How It Works
#### 1. **Base Workflow**:
- When executed, `credbuilder.py` performs the following steps:
    1. **Load Base Directory**:
        - Ensures `~/.pgvm/` exists as the directory for storing profiles and credentials.

    2. **Load Base Structure**:
        - Loads the base template for credentials from a file (`script-cred.json`) in the corresponding script directory.
        - If the base template is missing, it exits with a message.

    3. **List Profiles**:
        - Enumerates and displays all available profiles stored in `~/.pgvm/`.

    4. **Profile Selection**:
        - Prompts the user to select an existing profile or create a new one.

    5. **Credential Handling**:
        - For an existing profile:
            - Loads the current `cred.json` file.
            - Prompts the user to review and edit parameters.
            - Takes a backup before saving updates.

        - For a new profile:
            - Creates a new folder for the profile.
            - Asks the user for values for each parameter and saves them in `cred.json`.

#### 2. **Backup Management**:
- Before modifying `cred.json`, a backup is saved in `backup/` within the profile folder.
- Backup filenames contain a timestamp (e.g., `cred_20231018120000.json`).
- If the backup count exceeds 10, the oldest backups are deleted.

#### 3. **Interactive Credential Updates**:
- The script prompts users to modify or confirm credential fields interactively.
- Fields are pre-filled with existing values, and users can leave them unchanged by pressing `Enter`.

#### 4. **Dynamic Credential Templates**:
- Loads a `script-cred.json` file dynamically for specific scripts, allowing flexibility for managing different types of credentials.
- For example:
    - A template for vCenter might include: