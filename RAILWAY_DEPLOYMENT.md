# Railway Deployment Guide

This guide explains how to deploy MathFlow to Railway.app.

## 📋 Prerequisites

1. A Railway.app account
2. Git repository with your code pushed
3. API keys for OpenRouter and LlamaCloud

## 🚀 Deployment Steps

### 1. Prepare Your Repository

Make sure all changes are committed, including:
- `railway.json` (Railway configuration)
- `Procfile` (process definition)
- `build.sh` (frontend build script)
- Updated `backend/app/main.py` (static file serving)
- Updated `.gitignore` (excludes `backend/static/`)

### 2. Create a New Project on Railway

1. Go to [Railway.app](https://railway.app) and log in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect the `railway.json` configuration

### 3. Configure Environment Variables

In Railway dashboard, go to your project → Variables, and add:

**Required:**
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `LLAMA_CLOUD_API_KEY` - Your LlamaCloud API key

**Optional:**
- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins (e.g., `https://yourdomain.com,https://www.yourdomain.com`). If not set, the app will allow all origins (`*`).

### 4. Deploy

Railway will automatically:
1. Install dependencies (Python and Node.js via nixpacks)
2. Build the frontend (`npm run build` in frontend directory)
3. Copy built assets to `backend/static/`
4. Start the server using the Procfile command

### 5. Verify Deployment

After deployment completes:
1. Check the health endpoint: `https://your-app.railway.app/health`
2. Visit the root URL to see the frontend
3. Test the chat functionality
4. Try uploading a PDF

## 🔧 How It Works

### Architecture

- **Single Process**: Railway runs one process (FastAPI backend) that serves both the API and the static frontend files.
- **Build Process**: During the build phase, Railway:
  1. Installs Node.js dependencies in `frontend/`
  2. Builds the React app with Vite (`npm run build`)
  3. Copies the built files from `frontend/dist/` to `backend/static/`
- **Runtime**: The FastAPI server:
  - Serves static files from `/static` and `/` (with SPA fallback)
  - Handles API requests under `/api/v1/`
  - WebSocket endpoint at `/ws/logs`

### Static File Serving

The backend is configured to:
- Mount static assets at `/static` for direct access (CSS, JS, fonts, images)
- Serve `index.html` for all non-API routes (client-side routing)
- Return 404 for unmatched API routes

### CORS Configuration

- Development: Allows `localhost:3000` and `localhost:5173`
- Production: Uses `ALLOWED_ORIGINS` env var if set, otherwise allows all origins (`*`)

## 🐛 Troubleshooting

### Issue: "Website not showing" or blank page

**Check:**
1. Build logs: Ensure frontend build completed successfully
2. Static files exist: Verify `backend/static/index.html` was created
3. Health endpoint: `/health` should return `{"status": "healthy"}`
4. Browser console: Look for 404 errors on static assets

**Common causes:**
- Build failed due to missing Node.js dependencies
- Static files not copied to `backend/static/`
- FastAPI not serving static files correctly

### Issue: API requests failing with CORS errors

**Solution:** Set `ALLOWED_ORIGINS` environment variable with your Railway domain.

### Issue: WebSocket connection fails

**Check:**
- Railway uses HTTPS/WSS, ensure frontend uses `wss://` protocol
- The WebSocket URL is constructed from `API_URL` in the frontend

### Issue: PDF uploads failing

**Check:**
- API keys are correctly set
- Backend logs in Railway for errors
- File size limits (Railway has a 100MB request limit)

### Issue: Build taking too long

The frontend build can take 2-5 minutes on Railway's free tier. This is normal.

## 📊 Monitoring

- **Logs**: View logs in Railway dashboard → your project → Logs
- **Metrics**: Check CPU, memory, and bandwidth usage
- **Domains**: Add a custom domain in Railway settings if needed

## 🔄 Updates

To update your deployment:
1. Push changes to your GitHub repository
2. Railway will automatically trigger a new deployment
3. Monitor the deployment logs for any errors

## 📝 Notes

- The `backend/static/` directory is git-ignored and will be created during build
- ChromaDB data is stored in `chroma_db/` (persisted by Railway volumes if configured)
- Chat history is stored in `data/chats/` (persisted by Railway volumes if configured)
- Uploaded PDFs are stored in `data/` (persisted by Railway volumes if configured)

## 🆘 Need Help?

- Check Railway logs in the dashboard
- Review the main README.md for project details
- Open an issue in the GitHub repository
