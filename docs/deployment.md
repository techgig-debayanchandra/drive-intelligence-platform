# Deployment Guide

The platform is container-ready and can run in a single Linux container or on a workstation with a local SQLite database.

## Local Docker

```bash
docker compose up --build
```

## Production Notes

- Store SQLite data on persistent storage.
- Mount archive volumes read-only when possible.
- Keep approved execution disabled until the user reviews a plan.
- Rotate application logs and archive manifests regularly.