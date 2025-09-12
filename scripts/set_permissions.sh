#!/bin/bash

# Directory containing the user folders
BASE_DIR="/home/localadmin/ScannerProxy/files"

cd "$BASE_DIR" || exit 1

# Loop through each folder
for dir in *.*; do
    if [ -d "$dir" ]; then
        echo "Setting permissions for: $dir"

        # Set owner and group
        chown root:root "$dir"

        # Set base permissions (drwxrwx---)
        chmod 770 "$dir"

        # Clear existing ACLs
        setfacl -b "$dir"

        # Apply required ACLs
        setfacl -m u:$dir:rwx "$dir"
        setfacl -m g:custom_scan_users:rwx "$dir"

        # Apply default ACLs
        setfacl -d -m u:$dir:rwx "$dir"
        setfacl -d -m g:custom_scan_users:rwx "$dir"

        echo "Done with $dir"
    fi
done

