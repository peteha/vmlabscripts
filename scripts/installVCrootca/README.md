# InstallVCRootCA

This shell script installs the Root CAs found on the vCenter server.

It uses credbuilder.py to build the credentials needed for the script.
To setup the script run `python ./credbuilder.py -script installVCrootca` from the root of this repo.

## Usage

`installVCrootca.sh -p <profile> -y`

**Options:**
- The options include:
  - `-p, --profile` to specify the credential profile name (defaults to `default`).
  - `-y, --yes` for automatic confirmation to install dependencies without a prompt.
  - `-h, --help` to display a help message.

Example script using full paths and 'pggblab' profile.

```
> pwd
/home/peteha/GitHub/vmlabscripts
> /bin/bash /home/peteha/GitHub/vmlabscripts/scripts/installVCRootca/installVCrootca.sh -p pggblab -y
/home/peteha/GitHub/vmlabscripts/scripts/installVCRootca/installVCrootca.sh: line 139: check_sudo: command not found
Note: 'certutil' is not required on Linux or macOS. Skipping its check.
Downloading https://vc.pggb.local/certs/download.zip...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 11860  100 11860    0     0  24901      0 --:--:-- --:--:-- --:--:-- 24863
Unzipping /tmp/tmp.H1BXak9uDz/download.zip...
Adding certificates to the trusted CA store...
Adding /tmp/tmp.H1BXak9uDz/certs/win/81b33078.0.crt to the trusted store...
[sudo] password for peteha:
Updating certificates in /etc/ssl/certs...
0 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
Adding /tmp/tmp.H1BXak9uDz/certs/win/bef264ea.0.crt to the trusted store...
Updating certificates in /etc/ssl/certs...
0 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
Certificates added successfully!
```
