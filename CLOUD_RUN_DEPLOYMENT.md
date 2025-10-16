# Cloud Run Deployment Guide

How to deploy your Flask/React app to Google Cloud Run for massive scaling.

## Why Cloud Run

Cloud Run is perfect for this app because:

- Auto-scales from 0 to thousands of instances
- Pay only for requests (not idle time)
- Built-in load balancing
- Handles traffic spikes automatically
- No server management needed

## Prerequisites

**1. Install Google Cloud CLI:**

```bash
# Mac
brew install --cask google-cloud-sdk

# Windows
# Download from https://cloud.google.com/sdk/docs/install

# Linux
curl https://sdk.cloud.google.com | bash
```

**2. Login and setup:**

```bash
gcloud auth login
gcloud config set project YOUR-PROJECT-ID
```

**3. Create Google Cloud Project:**

- Go to https://console.cloud.google.com
- Create new project or use existing one
- Enable billing (required for Cloud Run)

## Quick Deployment

**1. Update the deploy script:**

```bash
# Edit deploy-cloud-run.sh
PROJECT_ID="your-actual-project-id"  # Change this!
```

**2. Make script executable and run:**

```bash
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh
```

**3. Wait 5-10 minutes for deployment**

## Manual Deployment Steps

If you prefer to deploy manually:

**Deploy backend services:**

```bash
# READ service
gcloud run deploy flask-read \
  --image=hamid2019/flask-react-backend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="SERVICE_TYPE=read" \
  --max-instances=50

# WRITE service
gcloud run deploy flask-write \
  --image=hamid2019/flask-react-backend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="SERVICE_TYPE=write" \
  --max-instances=20

# OPERATIONS service
gcloud run deploy flask-operations \
  --image=hamid2019/flask-react-backend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="SERVICE_TYPE=operations" \
  --max-instances=30

# TEXT EXTRACTOR service
gcloud run deploy flask-text-extractor \
  --image=hamid2019/flask-react-backend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="SERVICE_TYPE=text_extractor" \
  --max-instances=10
```

**Deploy frontend:**

```bash
gcloud run deploy flask-frontend \
  --image=hamid2019/flask-react-frontend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --max-instances=10
```

## Environment Variables

After deployment, add environment variables to each service:

**For all backend services:**

```bash
gcloud run services update flask-read \
  --region=us-central1 \
  --set-env-vars="DATABASE_URL=your-cockroachdb-url,SECRET_KEY=your-secret,AUTH0_DOMAIN=your-auth0-domain,AUTH0_AUDIENCE=your-audience,GCS_BUCKET_NAME=your-bucket"
```

Repeat for `flask-write`, `flask-operations`, and `flask-text-extractor`.

**Important: Set TEXT_EXTRACTOR_URL for operations service:**

```bash
# After deploying text-extractor, get its URL
TEXT_EXTRACTOR_URL=$(gcloud run services describe flask-text-extractor --region=us-central1 --format='value(status.url)')

# Update operations service to use text-extractor
gcloud run services update flask-operations \
  --region=us-central1 \
  --set-env-vars="TEXT_EXTRACTOR_URL=${TEXT_EXTRACTOR_URL}"
```

**CockroachDB SSL Certificate Options:**

**Option 1: Use sslmode=require (Recommended)**

```bash
# In your DATABASE_URL, add sslmode=require
DATABASE_URL="postgresql://username:password@host:26257/database?sslmode=require"
```

This uses the system certificate store. Works for CockroachDB Cloud.

**Option 2: Embed certificate in Docker image**

```dockerfile
# Add to your backend Dockerfile
COPY root.crt /app/certs/root.crt
```

Then use: `DATABASE_URL="postgresql://username:password@host:26257/database?sslmode=verify-full&sslrootcert=/app/certs/root.crt"`

**Option 3: Mount certificate from Secret Manager**

```bash
# Upload cert to Secret Manager
gcloud secrets create cockroachdb-cert --data-file=root.crt

# Mount in Cloud Run service
gcloud run services update flask-read \
  --region=us-central1 \
  --set-env-vars="DATABASE_URL=postgresql://username:password@host:26257/database?sslmode=verify-full&sslrootcert=/secrets/cockroachdb-cert" \
  --add-volume=name=secrets,type=secret,secret=cockroachdb-cert \
  --add-volume-mount=volume=secrets,mount-path=/secrets
```

**For frontend service:**

```bash
gcloud run services update flask-frontend \
  --region=us-central1 \
  --set-env-vars="VITE_API_URL=https://your-load-balancer-url/api,VITE_AUTH0_DOMAIN=your-auth0-domain,VITE_AUTH0_CLIENT_ID=your-client-id,VITE_AUTH0_AUDIENCE=your-audience"
```

## Load Balancer Setup

Cloud Run gives you separate URLs for each service, but you need one URL that routes requests like nginx does.

**Important**: The text-extractor service is called internally by the operations service, so it doesn't need to be exposed through the load balancer. Only the read, write, and operations services need public routing.

**Create Load Balancer:**

1. Go to Google Cloud Console > Network Services > Load Balancing
2. Create HTTP(S) Load Balancer
3. Configure backend services:
   - GET requests → flask-read service
   - POST requests → flask-write service
   - PUT/DELETE requests → flask-operations service
   - Frontend → flask-frontend service
   - **Note**: flask-text-extractor is internal (called by operations service)

**Or use this script:**

```bash
# Create load balancer (simplified)
gcloud compute url-maps create flask-app-map \
  --default-service=flask-read-backend

# Add path matchers for different HTTP methods
# (Full configuration is complex, use Console UI)
```

## Cloudflare Integration

Since you're already using Cloudflare, here's how to connect it to Cloud Run:

**Option 1: Direct to Cloud Run (Simplest)**

1. Deploy services to Cloud Run (get the URLs)
2. In Cloudflare DNS, create CNAME records:
   ```
   api.yourdomain.com → CNAME → your-load-balancer-url
   app.yourdomain.com → CNAME → flask-frontend-xyz.run.app
   ```
3. Enable Cloudflare proxy (orange cloud)
4. Set up Page Rules for caching

**Option 2: Keep Load Balancer + Cloudflare**

1. Create Google Load Balancer (as documented above)
2. Get Load Balancer IP address
3. In Cloudflare DNS:
   ```
   yourdomain.com → A → load-balancer-ip
   api.yourdomain.com → A → load-balancer-ip
   ```
4. Enable Cloudflare proxy for CDN and security

**Cloudflare Page Rules for API:**

```
api.yourdomain.com/api/filesystem/*/download
- Cache Level: Cache Everything
- Edge Cache TTL: 1 hour

api.yourdomain.com/api/*
- Cache Level: Bypass
- Disable Apps, Performance features
```

**Cloudflare Settings to configure:**

- SSL/TLS: Full (strict)
- Security Level: Medium
- Browser Cache TTL: 4 hours (for frontend)
- Always Use HTTPS: On

## Custom Domain (Alternative without Cloudflare)

**Add your domain directly to Google:**

```bash
# Map custom domain to load balancer
gcloud compute url-maps create flask-app-map \
  --default-service=your-backend-service

# Add SSL certificate
gcloud compute ssl-certificates create flask-app-ssl \
  --domains=yourdomain.com
```

## Scaling Configuration

**Service limits:**

- READ service: Up to 50 instances (handles most traffic)
- WRITE service: Up to 20 instances (file uploads)
- OPERATIONS service: Up to 30 instances (file operations)
- TEXT EXTRACTOR service: Up to 10 instances (PDF text extraction)
- Frontend: Up to 10 instances (static files)

**Cost estimate for 1000 concurrent users:**

- Cloud Run services: $50-100/month
- Load Balancer: $18-25/month (see breakdown below)
- Total: $70-125/month
- Still much cheaper than VMs running 24/7

**Google Load Balancer pricing:**

- Forwarding rules: $18/month (flat rate)
- Data processing: $0.008 per GB
- Example: 100GB/month = $18 + $0.80 = $18.80/month

**For low traffic (1 user/month):**

- Load Balancer: $18/month (minimum cost)
- Cloud Run: ~$0-2/month
- Total: ~$18-20/month

**Cost-saving alternatives:**

- Skip Load Balancer, use Cloudflare routing directly to services
- Use single Cloud Run service with internal routing
- For very low traffic, the $18 Load Balancer minimum might not be worth it

## Monitoring

**Check service health:**

```bash
# Get service status
gcloud run services list --region=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Monitor metrics in Cloud Console
```

**Set up alerts:**

- Error rate > 5%
- Response time > 2 seconds
- Memory usage > 80%

## Database Setup

**Use CockroachDB Cloud:**

1. Create cluster at https://cockroachlabs.cloud
2. Get connection string
3. Add to all backend services as DATABASE_URL

**Connection string format:**

```
postgresql://username:password@host:26257/database?sslmode=require
```

## File Storage

**Use Google Cloud Storage:**

1. Create bucket: `gsutil mb gs://your-app-files`
2. Set up service account with Storage Admin role
3. Add GCS_BUCKET_NAME to backend services

## Troubleshooting

**Service won't start:**

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=flask-read" --limit=10

# Check service configuration
gcloud run services describe flask-read --region=us-central1
```

**High costs:**

- Check if services are scaling down to zero
- Reduce max-instances if needed
- Use `--no-cpu-throttling=false` to save money

**Slow responses:**

- Increase memory: `--memory=1Gi`
- Increase CPU: `--cpu=2`
- Check database connection pooling

## CI/CD Integration

Add Cloud Run deployment to your GitHub Actions:

```yaml
# Add to .github/workflows/ci.yml
- name: Deploy to Cloud Run
  if: github.ref == 'refs/heads/main'
  run: |
    gcloud auth configure-docker
    ./deploy-cloud-run.sh
  env:
    GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
```

## Cost Optimization

**Tips to reduce costs:**

- Set appropriate max-instances
- Use `--concurrency=1000` for frontend
- Enable CPU throttling: `--no-cpu-throttling=false`
- Use Cloud CDN for static files
- Set up proper caching headers

**Monthly costs for different scales:**

- 100 users: ~$10-20
- 1,000 users: ~$50-100
- 10,000 users: ~$200-500

Much cheaper than running VMs 24/7 and scales automatically.

## Migration from VM + Docker Compose

Since you're currently using Cloudflare → VM → nginx → docker-compose, here's the migration path:

**Current setup:**

```
Cloudflare → VM (nginx) → Docker containers
```

**New setup:**

```
Cloudflare → Google Load Balancer → Cloud Run services
```

**Migration steps:**

1. Deploy to Cloud Run (keep VM running)
2. Set up Load Balancer with same routing rules as your nginx
3. Test Cloud Run setup with temporary subdomain
4. Update Cloudflare DNS to point to Load Balancer IP
5. Monitor for 24 hours, then shutdown VM

**Nginx to Load Balancer mapping:**

```nginx
# Your current nginx config
location /api/filesystem {
    if ($request_method = GET) { proxy_pass http://read_service; }
    if ($request_method = POST) { proxy_pass http://write_service; }
    if ($request_method ~ ^(PUT|DELETE)$) { proxy_pass http://operations_service; }
}
```

Becomes Load Balancer rules:

```
GET /api/* → flask-read service
POST /api/* → flask-write service
PUT|DELETE /api/* → flask-operations service
/* → flask-frontend service
```

**Benefits after migration:**

- Auto-scaling (no more VM management)
- Pay per request (not 24/7 VM costs)
- Better performance under load
- Automatic SSL and health checks
- Global load balancing

## Next Steps

1. Deploy using the script
2. Set up Load Balancer in Console
3. Configure environment variables
4. Set up Cloudflare DNS (keep VM as backup)
5. Test thoroughly, then migrate DNS
6. Add to CI/CD pipeline

Cloud Run will handle thousands of concurrent users automatically. Your app architecture is already perfect for this kind of deployment.
