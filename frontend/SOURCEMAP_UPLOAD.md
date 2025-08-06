# Sourcemap Upload to Grafana Faro

This project is configured to upload sourcemaps to Grafana Faro for better error tracking and debugging in production.

## Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```
   This will install `@grafana/faro-cli` which is required for sourcemap uploads.

2. **Get your API Key**
   - Go to Grafana Cloud → Frontend Observability → Settings → API Keys
   - Create a new API key with sourcemap upload permissions
   - Keep this key secure and never commit it to version control

3. **Configure Environment Variable**
   
   Option A: Create a local .env file (recommended for development)
   ```bash
   cp .env.example .env
   # Edit .env and add your API key
   ```
   
   Option B: Set environment variable directly
   ```bash
   export FARO_SOURCEMAP_API_KEY="glc_eyJvIjo..."
   ```

## Usage

### Build and Upload in One Step
```bash
# Builds the project and uploads sourcemaps
npm run build:upload-sourcemaps
```

### Upload Existing Build
```bash
# If you've already built the project
npm run upload-sourcemaps
```

The script will automatically load the API key from the `.env` file if present, or use the `FARO_SOURCEMAP_API_KEY` environment variable.

## CI/CD Integration

For automated deployments, set the `FARO_SOURCEMAP_API_KEY` as a secret in your CI/CD environment:

```yaml
# Example GitHub Actions
- name: Build and Upload Sourcemaps
  env:
    FARO_SOURCEMAP_API_KEY: ${{ secrets.FARO_SOURCEMAP_API_KEY }}
  run: npm run build:upload-sourcemaps
```

## Configuration

The upload script is configured with the following settings (in `upload-sourcemaps.sh`):

- **App Name**: rocketlane-assistant
- **App ID**: 193
- **Stack ID**: 1217581
- **Endpoint**: https://faro-api-prod-gb-south-1.grafana.net/faro/api/v1

The script uses the official `@grafana/faro-cli` tool to:
1. Inject a unique bundle ID into the JavaScript files
2. Upload the sourcemaps to Grafana Faro with that bundle ID

## Troubleshooting

- **No sourcemaps found**: Ensure you've run `npm run build` first
- **Authentication error**: Check that your API key is valid and has the correct permissions
- **Upload fails**: Verify network connectivity to Grafana Cloud
- **Permission denied**: Make sure the script is executable (`chmod +x upload-sourcemaps.sh`)

## Security

- **Never commit** the `.env` file or API keys to version control
- The `.gitignore` file is configured to exclude `.env` files
- Use environment variables or secrets management in production
- The API key should only have sourcemap upload permissions, not full account access