# Security Scanning App

A web-based security scanner that analyzes code, Docker images, and infrastructure configs (Kubernetes, Docker Compose, Terraform, Ansible) to detect security, cost, and performance vulnerabilities.

## Features

- **Code scanning** – Source code, dependencies, Dockerfiles
- **Docker images** – Container image vulnerability scanning
- **Docker Compose** – `docker-compose.yml` misconfigurations
- **Kubernetes** – Manifests, Helm charts
- **Terraform** – IaC security and cost estimation
- **Ansible** – Playbooks and roles

## Prerequisites

Install the following scanners on your system:

### Trivy (required)
```bash
# macOS
brew install trivy

# Linux
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
```

### Checkov (required)
```bash
pip install checkov
```

### Infracost (optional – for Terraform cost estimation)
```bash
# macOS
brew install infracost

# Register for a free API key at https://dashboard.infracost.io
export INFRACOST_API_KEY=your-key-here
```

## Quick Start

### Local development

1. **Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open http://localhost:5173

The frontend proxies `/api` requests to the backend.

### Docker (single image)

Build and run the full app (backend + frontend):

```bash
docker build -t security-scan-app .
docker run -p 8000:8000 -e PORT=8000 security-scan-app
```

Open http://localhost:8000

### Docker Compose (dev – backend + frontend separate)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173  
- Backend: http://localhost:8000  

**Note:** Scanners (Trivy, Checkov, Infracost) are not included in the image. For full scanning, run locally with scanners installed, or extend the Dockerfile.

## Deploy to Render

1. **Push to GitHub** (or GitLab/Bitbucket):
   ```bash
   git add .
   git commit -m "Add Render deployment"
   git push origin main
   ```

2. **Open the Blueprint** (replace with your repo URL):
   ```
   https://dashboard.render.com/blueprint/new?repo=https://github.com/YOUR_USERNAME/YOUR_REPO
   ```

3. **Connect your repo** and complete Git OAuth if prompted.

4. **Optional:** Add `INFRACOST_API_KEY` in the Render Dashboard (Environment) for Terraform cost scanning.

5. **Apply** and wait for the deploy. Your app will be live at `https://security-scan-app.onrender.com` (or your chosen name).

The `render.yaml` Blueprint uses a single Docker service that builds both frontend and backend.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Basic health check |
| `/api/health/scanners` | GET | Scanner availability (Trivy, Checkov, Infracost) |
| `/api/scans` | POST | Create and run a scan (multipart: file, target_type, docker_image_ref) |
| `/api/scans/{id}` | GET | Get scan status and results |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `INFRACOST_API_KEY` | Infracost API key for Terraform cost scans |
| `SCAN_UPLOAD_DIR` | Upload directory (default: `/tmp/security-scan-uploads`) |
| `SCAN_MAX_UPLOAD_SIZE_MB` | Max upload size in MB (default: 100) |
| `SCAN_TRIVY_PATH` | Path to Trivy binary |
| `SCAN_CHECKOV_PATH` | Path to Checkov binary |
| `SCAN_INFRACOST_PATH` | Path to Infracost binary |

## License

MIT
