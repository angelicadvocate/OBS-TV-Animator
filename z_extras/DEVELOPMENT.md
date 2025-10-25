# 🛠️ Development Setup Guide

This project offers **three different development approaches** depending on your needs:

## 🚀 Quick Start Options

### 1. **LOCAL Development** (⚡ Fastest - Recommended for Frontend)
**Perfect for:** HTML, CSS, JS changes with instant hot reload

```bash
# All platforms (run from project root)
python z_extras/dev_local.py
```

**Benefits:**
- ✅ Instant hot reload (no rebuilds)
- ✅ Native Flask debug mode
- ✅ Direct file system access
- ✅ Fastest development cycle

**Access:** http://localhost:5000

---

### 2. **Docker Development** (🐳 Containerized with Hot Reload)
**Perfect for:** Testing Docker setup while developing

```bash
# First move dev compose file to root (only needed once)
mv z_extras/docker-compose.dev.yml ./docker-compose.dev.yml

# Then run development container
docker-compose -f docker-compose.dev.yml up --build
```

**Benefits:**
- ✅ Matches production environment
- ✅ Volume mounts for live changes
- ✅ Flask debug mode in container
- ✅ Network isolation testing

**Access:** http://localhost:8081

---

### 3. **Production** (🚀 Full Production Setup)
**Perfect for:** Final testing and deployment

```bash
# All platforms
docker-compose up -d --build
```

**Benefits:**
- ✅ Production-ready configuration
- ✅ Optimized for performance
- ✅ Health checks enabled
- ✅ Proper logging

**Access:** http://localhost:8080

---

## 🔄 Development Workflow

### Frontend Development (HTML/CSS/JS)
1. **Use LOCAL development** for fastest feedback
2. Run `python z_extras/dev_local.py` from project root
3. Edit files in `templates/`, `static/css/`, `static/js/`
4. Refresh browser to see changes instantly

### Backend Development (Python)
1. **Use LOCAL development** for debugging
2. Edit `app.py` - Flask auto-reloads on changes
3. Check terminal for error messages
4. Use Python debugger if needed

### Full Stack Testing
1. **Use Docker development** to test integration
2. Move `z_extras/docker-compose.dev.yml` to root if not already done
3. Run `docker-compose -f docker-compose.dev.yml up --build` to start containerized version
4. Test both frontend and backend changes
5. Verify everything works in containerized environment

### Production Validation
1. **Use Production setup** for final testing
2. Run `docker-compose up -d --build` to test production config
3. Verify performance and stability
4. Test with actual Smart TV devices

---

## 📁 File Change Detection

### What triggers hot reload:

#### LOCAL Development:
- ✅ `app.py` - Flask auto-reloads
- ✅ `templates/*.html` - Immediate on refresh  
- ✅ `static/css/*.css` - Immediate on refresh
- ✅ `static/js/*.js` - Immediate on refresh

#### Docker Development:
- ✅ `app.py` - Flask reloads in container
- ✅ `templates/*.html` - Volume mounted, immediate
- ✅ `static/css/*.css` - Volume mounted, immediate  
- ✅ `static/js/*.js` - Volume mounted, immediate
- ❌ `requirements.txt` - Requires rebuild
- ❌ `Dockerfile` changes - Requires rebuild

#### Production:
- ❌ All changes require `docker-compose up --build`

---

## 🎯 Which Setup to Use When

| Task | Recommended Setup | Why |
|------|------------------|-----|
| **HTML/CSS tweaks** | LOCAL | Instant refresh, no containers |
| **JavaScript changes** | LOCAL | Debug tools, instant feedback |
| **Python/Flask changes** | LOCAL | Best debugging experience |
| **Testing integrations** | Docker Dev | Realistic environment |
| **Smart TV testing** | Docker Dev/Prod | Network accessibility |
| **Final validation** | Production | Real deployment conditions |

---

## 🔧 Troubleshooting

### Port Conflicts
- **LOCAL:** Uses port 5000 (Flask default) + 5001 (Raw WebSocket)
- **Docker Dev:** Uses port 8081 (external) → 8080 (internal) + 8081 (Raw WebSocket) 
- **Production:** Uses port 8080 (main) + 8081 (Raw WebSocket)

**Note:** Each setup uses 2 ports - main port and main port + 1 for raw WebSocket connections

### Volume Mount Issues (Docker)
```bash
# If changes aren't reflected, rebuild:
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up --build
```

### Python Dependencies
```bash
# Install/update requirements for local development:
pip install -r requirements.txt
```

### File Permissions (macOS/Linux)
```bash
# Make dev_local.py executable if needed:
chmod +x z_extras/dev_local.py
```

---

## 💡 Pro Tips

1. **Use LOCAL for 90% of development** - it's the fastest
2. **Keep Docker Dev running** in a separate terminal for testing
3. **Use browser dev tools** - they work great with LOCAL setup
4. **Test on real Smart TV** regularly with Docker setups
5. **Check both setups** before committing changes

---

This setup gives you the **best of both worlds**: blazing-fast local development with the safety of containerized testing! 🎉