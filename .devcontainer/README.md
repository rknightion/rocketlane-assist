# DevContainer Setup

This project includes DevContainer configuration for VS Code development.

## Quick Start

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Install [VS Code](https://code.visualstudio.com/)
3. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

## Development Setup

The devcontainer provides a complete Python development environment with the backend running in Docker. The frontend can be run either:

1. **On your host machine** (recommended for better performance):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **In the devcontainer** (if you prefer everything containerized):
   - Open a terminal in VS Code
   - Navigate to `/workspace/frontend`
   - Run `npm install && npm run dev`

### What's Included

- **Python 3.13** with uv package manager
- **Backend auto-reload** on code changes
- **Full VS Code integration** with Python and JS/TS extensions
- **Zsh shell** with Oh My Zsh for better terminal experience
- **Pre-configured linting and formatting** for both Python and TypeScript

### Using the DevContainer

1. Open VS Code
2. Run "Dev Containers: Reopen in Container" from Command Palette
3. Wait for the container to build and start
4. Backend will automatically be available at http://localhost:8000
5. Start the frontend using your preferred method (host or container)

## Troubleshooting

### Shell errors during setup
If you see "source: not found" errors, the container uses sh instead of bash. This has been fixed in the current configuration.

### Node.js version
The project uses Node.js 22 LTS. If you need a different version, update:
- `frontend/package.json` engines field
- `frontend/Dockerfile` FROM statements
- `.devcontainer/devcontainer-fullstack.json` features section

### Port conflicts
If ports 8000 or 3000 are already in use:
1. Stop conflicting services
2. Or modify port mappings in `docker-compose.dev.yml`

### VS Code Port Forwarding Messages
You may see port forwarding messages in the VS Code terminal like:
```
Port forwarding connection from 55878 > 39641 > 39641 in the container.
```

These are normal and can be ignored. They're VS Code internal connections for:
- Language servers
- Extension communication
- Debugging tools

The devcontainer is configured to only forward ports 8000 and 3000 for your application. To reduce these messages:
1. The configuration already sets `remote.autoForwardPorts: false`
2. Other ports are set to be ignored with `otherPortsAttributes`

Your application ports (8000 and 3000) work independently of these internal connections.