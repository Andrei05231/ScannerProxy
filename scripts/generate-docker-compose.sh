#!/bin/bash

# !! Winbind configuration required for fetching AD group users, set "winbind cache time" in /etc/samba/smb.conf to adjust caching time based on how often you want to get group users

AD_GROUP="custom_scan_users"
BASE_COMPOSE_FILE="../docker-compose.yml"
SERVICE_TEMPLATE="scanner-proxy"
OUTPUT_FILE="../docker-compose.generated.yml"
IP_PREFIX="10.0.52."
START_IP=201

# Get user list from AD group via winbind
users=$(wbinfo --group-info="$AD_GROUP" 2>/dev/null | cut -d':' -f4)

# Check if wbinfo succeeded and returned users
if [[ -z "$users" ]]; then
  echo "⚠️ Could not fetch users from AD group '$AD_GROUP'."
  if [[ -f "$OUTPUT_FILE" ]]; then
    echo "ℹ️ Keeping existing $OUTPUT_FILE unchanged."
    exit 0
  else
    echo "ℹ️ No existing $OUTPUT_FILE found. Creating one with only -Shared user."
    users="-Shared"
  fi
fi

IFS=',' read -ra user_array <<< "$users"

# Always add the shared container (unless it's already the only one)
if [[ ! " ${user_array[*]} " =~ " -Shared " ]]; then
  user_array+=("-Shared")
fi

# Empty the output file and start with the 'services:' key
echo "services:" > "$OUTPUT_FILE"

# Loop and append each user-specific service
ip_suffix=$START_IP
for user in "${user_array[@]}"; do
  cat >> "$OUTPUT_FILE" <<EOF
  scanner-proxy-${user}:
    extends:
      file: docker-compose.yml
      service: $SERVICE_TEMPLATE
    container_name: scanner-proxy-${user}
    environment:
      - USERNAME=${user}
    networks:
      ipvlan-net:
        ipv4_address: ${IP_PREFIX}${ip_suffix}

EOF
  ip_suffix=$((ip_suffix + 1))
done

# Append the network definition from the base compose file
echo "" >> "$OUTPUT_FILE"

# Extract the 'networks:' section from the base compose file and append it
awk '/^networks:/ {flag=1; print; next} /^[^[:space:]]/ {flag=0} flag' "$BASE_COMPOSE_FILE" >> "$OUTPUT_FILE"

echo "✅ Generated $OUTPUT_FILE with ${#user_array[@]} services and network definition."

