# OpenShorts AWS Native Deployment

This directory contains the scripts and configurations for deploying OpenShorts natively to an AWS EC2 instance without Docker.

## Scripts
- `bootstrap-host.sh`: Sets up the EC2 instance dependencies.
- `deploy-release.sh`: Deploys a specific release of the code.
- `healthcheck.sh`: Verifies the health of the services.

## Configurations
- `nginx-openshorts.conf`: Nginx reverse proxy configuration.
- `openshorts-backend.service`: Systemd service for the FastAPI backend.
- `openshorts-renderer.service`: Systemd service for the Remotion renderer.
- `openshorts.env.example`: Example environment variables for the systemd services.
