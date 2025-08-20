FROM ostris/aitoolkit:latest

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
