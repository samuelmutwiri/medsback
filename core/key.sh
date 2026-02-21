#!/bin/bash
# ============================================================================
# generate_secret.sh
# Django SECRET_KEY generator and rotator
# Safely regenerates and updates the SECRET_KEY entry in your .env file.
# Author: Samuel Mutwiri
# ============================================================================

# Project directory (edit if needed)
PROJECT_DIR="."
ENV_FILE="$PROJECT_DIR/.env"
BACKUP_FILE="$PROJECT_DIR/.env.backup_$(date +%Y%m%d_%H%M%S)"

# Move to project directory
cd "$PROJECT_DIR" || { echo "Error: Project directory not found."; exit 1; }

# Check if .env exists
if [ -f "$ENV_FILE" ]; then
    echo "Backing up existing .env file to: $BACKUP_FILE"
    cp "$ENV_FILE" "$BACKUP_FILE"
else
    echo "No .env file found. A new one will be created."
    touch "$ENV_FILE"
fi

# Generate a new secure secret key
NEW_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# Remove any existing SECRET_KEY line
grep -v '^SECRET_KEY=' "$ENV_FILE" > "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"

# Append the new key at the top for visibility
echo "SECRET_KEY=$NEW_KEY" | cat - "$ENV_FILE" > "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"

# Ensure DEBUG and other defaults are set if missing
grep -q '^DEBUG=' "$ENV_FILE" || echo "DEBUG=False" >> "$ENV_FILE"

# Set secure file permissions
chmod 600 "$ENV_FILE"

echo "✅ SECRET_KEY has been rotated successfully."
echo "📦 Backup of old environment: $BACKUP_FILE"
echo "🔑 New SECRET_KEY: ${NEW_KEY:0:8}********${NEW_KEY: -8}"
echo "Done."
