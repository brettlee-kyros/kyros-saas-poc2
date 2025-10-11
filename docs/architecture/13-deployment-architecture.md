# 13. Deployment Architecture

## 13.1 Deployment Strategy

**Frontend Deployment:**
- **Platform:** Docker Compose (local PoC only)
- **Build Command:** `npm run build` (Next.js production build)
- **Output Directory:** `apps/shell-ui/.next`
- **CDN/Edge:** None (PoC runs on localhost)
- **MVP Path:** Deploy to Vercel or Azure App Service with CDN

**Backend Deployment:**
- **Platform:** Docker Compose (local PoC only)
- **Build Command:** N/A (Python interpreted)
- **Deployment Method:** Docker containers with volume mounts
- **MVP Path:** Azure App Service, AKS, or Azure Container Apps

---
