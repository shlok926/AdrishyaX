# StegoForge v4 Live Deployment Guide

This document outlines how to deploy the application in a live environment, based on the MVP backend and Tailwind UI.

## Local Docker Deployment
If you have Docker Desktop installed, run the following:

```bash
docker build -t stegoforge-app .
docker run -d -p 8000:8000 --name stegoforge-container stegoforge-app
```

Then visit `http://localhost:8000/`.

## Cloud Deployment (Heroku, Render, AWS, etc.)
The `Dockerfile` provided is ready for nearly any container-based PaaS (Platform as a Service).

1. Push your code to a GitHub repository.
2. Link the repository to your chosen platform (e.g., Render, Railway, Heroku).
3. The platform will automatically detect the Dockerfile, build the image, and expose it on the assigned URL.
4. Ensure you set environment variables like `FLASK_ENV=production` as needed.

## Security Considerations for Live
- **TLS/HTTPS:** In production, this application *must* run behind an HTTPS load balancer or reverse proxy (like Nginx) to protect passwords and payload transit.
- **Deniability:** The Decoy Protocol is active in the V1 format.
