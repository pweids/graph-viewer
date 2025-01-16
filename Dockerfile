FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the app code into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir streamlit graphviz

# Expose the port Streamlit will run on
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "make_node_graph.py", "--server.port=8501", "--server.address=0.0.0.0"]
