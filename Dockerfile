FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/FPBP

# Install system dependencies
RUN apt-get update && \
    apt-get install -y netcat-traditional gcc postgresql-client libpq-dev dos2unix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install pip requirements
COPY requirements.txt /usr/src/FPBP/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . /usr/src/FPBP/

# Copy entrypoint script, set permissions, and convert line endings
COPY entrypoint.sh /usr/src/FPBP/
RUN chmod +x /usr/src/FPBP/entrypoint.sh
RUN dos2unix /usr/src/FPBP/entrypoint.sh

# Verify permissions
RUN ls -l /usr/src/FPBP/entrypoint.sh

# Specify the entrypoint script
ENTRYPOINT ["sh", "/usr/src/FPBP/entrypoint.sh"]
