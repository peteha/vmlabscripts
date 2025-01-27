# HCL Update

As documented by William Lam @ [link](https://williamlam.com/2023/12/dynamically-generate-custom-vsan-esa-hcl-json-for-vmware-cloud-foundation-vcf-5-1.html)
you can create custom HCLs use un-approved hardware for vSAN in non production environments.  The process to create the customhcl is located within the
linked page.  The script here keeps the customhcl up to date with the date from the online version and updates vCenter
with the latest version.

I run this in a daily cron job on a host to keep my lab up to date.

The process uses a credential file stored in ~/.pgvm/.  You can create this file using `credbuilder.py` in the 
root of this script directory.


The `hclupdate.py` script provides several command-line arguments to control how it processes and updates the `customhcl.json` file and applies it to `vCenter`. Below is a detailed description of each argument:
### **Arguments**
- `--hcl-path` **
    - **Type**: `string`
    - **Description**: Specifies the path to the source `customhcl.json` file.
        - If not provided, the script defaults to a predefined path (`customhcl`) as the source.

    - **Example**:
``` bash
     python hclupdate.py --hcl-path /path/to/my/customhcl.json
```
- **`--test` **
    - **Type**: `flag` (does not require a value)
    - **Description**: Runs the script in **test mode**, meaning it will simulate changes without actually modifying files.
    - **Example**:
``` bash
     python hclupdate.py --test
```
- **`--update-vcenter` **
    - **Type**: `flag` (does not require a value)
    - **Description**: Triggers the script to apply the updated `customhcl.json` file to a vCenter server using the **REST API**.
        - Requires a valid `--profile` argument (or defaults to the general `~/.pgvm/cred.json` if no profile is supplied).

    - **Effect**:
        - Invokes a PowerShell script (`hclvcenter.ps1`) that interacts with a vCenter server for updates.
        - Requires credentials stored in `cred.json` for authentication.

    - **Example**:
``` bash
     python hclupdate.py --update-vcenter --profile myprofile
```
- **`--profile` **
    - **Type**: `string` (optional)
    - **Description**: Specifies the profile to use for retrieving vCenter credentials.
        - Profiles are expected to be stored in `~/.pgvm/<profile>/cred.json`.
        - If not provided, defaults to `~/.pgvm/cred.json`.
    - **Behavior**:
        - For example:
            - If `--profile` is not provided, credentials are fetched from:
        ``` 
         ~/.pgvm/cred.json
        ```
      - If `--profile myprofile` is provided, credentials are fetched from:

    ``` 
         ~/.pgvm/cred.json
    ```
    - If `--profile myprofile` is provided, credentials are fetched from:
    ``` 
         ~/.pgvm/myprofile/cred.json
    ```
   - **Example**:
    ``` bash
     python hclupdate.py --update-vcenter --profile production
    ```



