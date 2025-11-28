# Use lightweight Python image
FROM python:3.10-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget ffmpeg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxkbcommon0 libxdamage1 libxrandr2 libasound2 libpangocairo-1.0-0 \
    libxcomposite1 libxshmfence1 libgbm1 libpango-1.0-0 libgtk-3-0 \
    && apt-get clean

# Install Playwright + Browsers
RUN pip install playwright
RUN playwright install --with-deps

# Copy requirement file
COPY requirements.txt /app/requirements.txt

# Install requirements
RUN pip install -r /app/requirements.txt

# Copy project files
COPY . /app
WORKDIR /app

# Expose HuggingFace default port
EXPOSE 7860

# Start FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
