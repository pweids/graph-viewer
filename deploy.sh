#!/bin/bash

# Variables
EC2_USER="ec2-user"
EC2_HOST="ec2-35-94-43-61.us-west-2.compute.amazonaws.com"
PEM_KEY_PATH="/Users/paulweidinger/dev/node_graph/paul-node-graph.pem"
LOCAL_FILE_PATH="/Users/paulweidinger/dev/node_graph/make_node_graph.py"
REMOTE_APP_DIR="/home/ec2-user/node_graph"
SERVICE_NAME="streamlit"

# Transfer the updated file to the EC2 instance
scp -i "$PEM_KEY_PATH" "$LOCAL_FILE_PATH" "$EC2_USER@$EC2_HOST:$REMOTE_APP_DIR/"

# SSH into the EC2 instance and restart the Streamlit service
ssh -i "$PEM_KEY_PATH" "$EC2_USER@$EC2_HOST" << EOF
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
EOF

echo "Deployment complete. The Streamlit service has been restarted."
