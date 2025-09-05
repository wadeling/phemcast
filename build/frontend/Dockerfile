# Frontend Dockerfile for Industry News Agent
# Based on nginx for serving static files

FROM nginx:alpine

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy nginx configuration
COPY html/nginx.conf /etc/nginx/nginx.conf

# Copy static files from the html directory
COPY html/ .

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
