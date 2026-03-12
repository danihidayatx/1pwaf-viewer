FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set default port via ENV
ENV APP_PORT=5000

# Expose the application port
EXPOSE $APP_PORT

# Use shell form of CMD to interpolate the environment variable
CMD gunicorn -w 4 -b 0.0.0.0:$APP_PORT app:app
