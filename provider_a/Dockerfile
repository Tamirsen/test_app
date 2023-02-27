FROM python:3.9

COPY requirements.txt .
RUN pip install -r requirements.txt

# Install provider_a dependencies
COPY . /app
WORKDIR /app

# Expose port
EXPOSE 8989

# Start the application
CMD ["python", "app.py"]