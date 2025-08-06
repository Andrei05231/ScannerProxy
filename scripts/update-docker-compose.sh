#!/bin/bash

# Path to the generated file
FILE="../docker-compose.generated.yml"

# Temporary backup file
TMP_FILE="${FILE}.bak"

# Command to generate the docker-compose file
GENERATE_COMMAND="./generate-docker-compose.sh"  

# Directory where docker commands should run
DOCKER_DIR="../"

# Make a backup of the current file if it exists
if [ -f "$FILE" ]; then
    cp "$FILE" "$TMP_FILE"
else
    touch "$TMP_FILE"
fi

# Run the generation script
$GENERATE_COMMAND

# Compare the new file with the backup
if ! cmp -s "$FILE" "$TMP_FILE"; then
    echo "Changes detected in $FILE"
    (cd "$DOCKER_DIR" && make docker-stop && make docker-run-ad)
else
    echo "No changes in $FILE"
fi

# Clean up
rm "$TMP_FILE"
