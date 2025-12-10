# Base Python image
FROM python:3.12.10-slim

# Set working directory
WORKDIR /app

# Copy and install Python dependencies from the backend directory
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the project files (assuming app.py is in root)
COPY . .

# Expose default port (Render will inject $PORT at runtime)
EXPOSE 8000

# Start the app with gunicorn, binding to the port Render provides
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:${PORT:-8000}", "--forwarded-allow-ips", "*"]
