import argparse
import json
from scripts import credman
import os
import sys
import socket
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

scriptName = "manageVMs"
cred_path = "~/.pgvm/"
json_output_file = "./json/vms.json"


def connect_to_vcenter(creds):
    """
    Connects to the vCenter server and returns the service instance.

    :param vcenter_server: vCenter server address
    :param username: Username for vCenter
    :param password: Password for vCenter
    :return: Service Instance connected to vCenter
    """
    vcenter_server = creds["vcenter"]["VCENTER_SERVER"]
    username = creds["vcenter"]["VCENTER_USER"]
    password = creds["vcenter"]["VCENTER_PASSWORD"]

    try:
        # Disable SSL warnings
        context = ssl._create_unverified_context ()

        # Connect to vCenter
        service_instance = SmartConnect (
            host=vcenter_server,
            user=username,
            pwd=password,
            sslContext=context
        )
        print ( "Connected to vCenter." )
        return service_instance
    except vmodl.MethodFault as e:
        print ( f"Error connecting to vCenter: {e}" )
        return None


def disconnect_from_vcenter(service_instance):
    """
    Disconnects from the vCenter server.

    :param service_instance: The service instance to disconnect
    :return: None
    """
    try:
        Disconnect ( service_instance )
        print ( "Disconnected from vCenter." )
    except Exception as e:
        print ( f"Error disconnecting from vCenter: {e}" )


def _get_vms_with_tags(service_instance, json_output_file):
    """
    Retrieves VMs and their tags from vCenter and writes them to a JSON file.

    :param service_instance: The connected vCenter service instance
    :param json_output_file: Name of the JSON output file
    :return: None
    """
    try:
        # Retrieve all VMs from vCenter
        content = service_instance.RetrieveContent ()
        container = content.viewManager.CreateContainerView ( content.rootFolder, [ vim.VirtualMachine ], True )
        vms = container.view

        # Fetch VM tags (requires vSphere 6.5+)
        try:
            tag_manager = content.tagging.Tag
            category_manager = content.tagging.Category
        except Exception:
            print ( "Unable to retrieve tags. Ensure vCenter supports tagging (vSphere 6.5+)." )
            tag_manager = None
            category_manager = None

        # Gather VM details
        vm_list = [ ]
        for vm in vms:
            # VM Name
            vm_info = {
                "name": vm.name,
                "tags": [ ]
            }

            # Get VM Tags
            if tag_manager and category_manager:
                try:
                    tag_ids = tag_manager.ListAttachedTags ( vm )
                    for tag_id in tag_ids:
                        tag = tag_manager.Get ( tag_id )
                        vm_info [ "tags" ].append ( tag.name )
                except Exception as e:
                    print ( f"Error fetching tags for VM '{vm.name}': {e}" )

            vm_list.append ( vm_info )

        # Write to JSON file
        with open ( json_output_file, "w" ) as json_file:
            json.dump ( vm_list, json_file, indent=4 )
        print ( f"VM data saved to {json_output_file}." )

    except vmodl.MethodFault as e:
        print ( f"Error retrieving VMs from vCenter: {e}" )

def get_vms_with_tags(creds, json_file):
    service_instance = connect_to_vcenter ( creds)
    if service_instance:
        try:
            # Fetch VM details and save them to a JSON file
            _get_vms_with_tags ( service_instance, json_file )
        finally:
            # Disconnect from vCenter
            disconnect_from_vcenter ( service_instance )


def main():
    """
    Main function to parse arguments and execute tasks.
    Supports getVMs, shutdownVMs, and combined mode.
    """
    parser = argparse.ArgumentParser ( description="VMWare vSphere VM management script." )
    parser.add_argument ( "--profile", type=str, help="Profile to use for vCenter credentials (defaults to ~/.pgvm/cred.json)." )


    args = parser.parse_args ()
    profile = args.profile or ""
    creds = credman.get_creds ( profile, scriptName )
    get_vms_with_tags(creds, json_output_file)

if __name__ == "__main__":
    main ()