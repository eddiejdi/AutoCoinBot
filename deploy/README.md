# Deployment helpers

This folder contains templates and instructions to run the app as a systemd
service or inside Docker.

Systemd (recommended for single-machine deployments)

1. Copy and edit the template:

   sudo cp deploy/streamlit.service.template /etc/systemd/system/streamlit.service
   sudo editor /etc/systemd/system/streamlit.service

   Replace `{PROJECT_DIR}` with the absolute path to the project
   (for example `/home/edenilson/Downloads/kucoin_app`) and `{USER}` with the
   user that should run the service.

2. Reload systemd and start:

   sudo systemctl daemon-reload
   sudo systemctl enable --now streamlit.service

Docker / docker-compose (good for containers)

1. Build and run from the `deploy/` folder:

   cd deploy
   docker compose build
   docker compose up -d

Notes
- `start_streamlit.sh` supports `--foreground` that runs the app in foreground
  (suitable for systemd) and the default background mode (backward compatible).
- When using Docker, the project directory is mounted into the container by the
  compose file; adjust volumes for production use (persistent DB storage, etc.).
