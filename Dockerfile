# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install system dependencies and Python packages in one layer for faster build
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --only-binary=all -r requirements.txt \
    && python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy only necessary application files
COPY app.py chatbot.py nlp_utils.py models.py user_management.py init_db.py extensions.py ./
COPY database/ ./database/
COPY htdocs/ ./htdocs/
COPY static/css/ ./static/css/
COPY static/js/ ./static/js/
COPY static/media/ ./static/media/
# Copy uploads directory if it exists (for existing uploaded content)
RUN mkdir -p static/uploads/locations static/uploads/visuals && \
    if [ -d static/uploads ]; then cp -r static/uploads/* ./static/uploads/ 2>/dev/null || true; fi

# Initialize the database
RUN python init_db.py

# Expose port (Railway will override if needed)
EXPOSE 8000

# Default command (Railway will use startCommand from railway.json)
CMD ["gunicorn", "app:app"]
