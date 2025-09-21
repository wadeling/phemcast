# Backend Dockerfile for Industry News Agent
FROM ccr.ccs.tencentyun.com/phemcast/backend-base:latest

# Copy application code
COPY ./src/ ./src/
COPY ./build/backend/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY ./requirements.txt ./app_requirements.txt
COPY ./init_invite_codes.py .
   
# Install application dependencies
RUN pip install --no-cache-dir -r app_requirements.txt 

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application using the independent Docker startup script
ENTRYPOINT [ "entrypoint.sh" ]
