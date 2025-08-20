FROM ostris/aitoolkit:sha256:e150f201456c2f6ee9eb3737a8077fadb2faa694f3b8f304a9424b9fa22837f5

# Install runpod and any additional dependencies
RUN pip install runpod

# Copy handler file
COPY rp_handler.py /app/rp_handler.py

# Set working directory
WORKDIR /app

# Ensure proper permissions
RUN chmod +x /app/rp_handler.py

# Start the container with our handler
CMD ["python", "-u", "/app/rp_handler.py"]
