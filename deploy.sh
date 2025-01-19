#!/bin/bash

# Variables
EC2_USER="ec2-user"
EC2_HOST="ec2-35-94-43-61.us-west-2.compute.amazonaws.com"
PEM_KEY_PATH="/Users/paulweidinger/dev/node_graph/paul-node-graph.pem"
LOCAL_DIR_PATH="/Users/paulweidinger/dev/node_graph"
REMOTE_APP_DIR="/home/ec2-user/node_graph"
SERVICE_NAME="streamlit"

# Sync excluding venv and .git
rsync -av \
  --exclude '.git' \
  --exclude '.gitignore' \
  --exclude 'venv' \
  --exclude '__pycache__' \
  -e "ssh -i $PEM_KEY_PATH" \
  "$LOCAL_DIR_PATH/" \
  "$EC2_USER@$EC2_HOST:$REMOTE_APP_DIR/"

# SSH and restart service
ssh -i "$PEM_KEY_PATH" "$EC2_USER@$EC2_HOST" << EOF
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
EOF

echo "Deployment complete. The Streamlit service has been restarted."
