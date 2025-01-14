FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Set environment variable for port
ENV PORT=8080

# Command to run the application
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
