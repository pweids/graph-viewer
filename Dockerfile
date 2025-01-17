FROM python:3.9-slim

# Install system dependencies (Graphviz binaries)
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the app files into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Streamlit will use
EXPOSE 8501

# Command to run your Streamlit app
CMD ["streamlit", "run", "make_node_graph.py", "--server.port=8501", "--server.address=0.0.0.0"]
