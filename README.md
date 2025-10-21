# OBS-TV-Animator

> ⚠️ **This project is still in development and not production-ready.**

A lightweight **Flask-SocketIO** server that displays HTML/CSS/JS animations or videos on a Smart TV — with real-time updates triggered via **OBS WebSocket**, **StreamerBot**, or **REST API**.  
Upload and manage media entirely through the web-based admin panel, no manual file edits required.

---

## ✨ Features

- 🎨 Serve HTML/CSS/JS or video animations to Smart TVs
- ⚡ Real-time switching via WebSocket or REST
- 🖥️ Web-based Admin UI for managing media, users, and triggers
- 🎮 OBS & StreamerBot integration for event-driven control
- 🔇 Videos are muted by default (Chrome autoplay compliant)
- 🐳 Simple one-command Docker deployment

---

## 🚀 Installation (Docker)

### Prerequisites

You only need **one** of the following installed on your system:

- [Docker Desktop](https://docs.docker.com/get-started/get-docker/) *(recommended for Windows/macOS)*
- [Docker Engine](https://docs.docker.com/engine/install/) *(for Linux servers)*
- [Docker Compose](https://docs.docker.com/compose/install/) *(included with most Docker Desktop installs)*

> 🧩 **Note:** See the included [`docker-compose.yml`](./docker-compose.yml) for bind mounts and configuration details.

---

### Build & Run

> 🧱 **Docker Hub:** Prebuilt images are coming soon!  
> For now, during testing, please build manually.

1. **Clone this repository:**
   ```bash
   git clone https://github.com/angelicadvocate/OBS-TV-Animator.git
   cd obs-tv-animator
   ```

2. **Build and start the container:**
   ```bash
   docker compose up -d --build
   ```

3. **Access the web interfaces:**
   - **Admin Panel:** http://[DOCKER_HOST_IP]:8080/admin
   - **TV Display:** http://[DOCKER_HOST_IP]:8080
   - **WebSocket API:** ws://[DOCKER_HOST_IP]:8080/socket.io/

### Default Login

- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ **Change this immediately in the Admin → Users page after first login.**

---

## 🧭 Using the Admin Interface

All configuration and media management are now handled in the web UI:

- Upload or remove HTML and video animations
- Switch currently active media in real time
- Manage user accounts and credentials
- Trigger animations manually or link to OBS/StreamerBot events

> **No manual code edits required** — manage media directly from the Admin Interface.

---

## 🔗 Integrations

OBS-TV-Animator integrates seamlessly with event-based tools like OBS and StreamerBot:

- **OBS WebSocket:** Trigger media changes on scene transitions
- **StreamerBot:** Automate event-based triggers
- **REST API:** For simple or legacy integrations

### Example WebSocket Event

```json
{
  "event": "trigger_animation",
  "data": {
    "animation": "intro.html"
  }
}
```

---

## 📺 Smart TV Setup

1. **Find your Docker host IP** (e.g., `192.168.1.100`)

2. **Start the container:**
   ```bash
   docker compose up -d
   ```

3. **On your Smart TV browser, open:**
   ```
   http://192.168.1.100:8080
   ```

The current animation or video will auto-play fullscreen. Changes appear instantly when triggered via the admin UI, OBS, or StreamerBot.

---

## 🧠 Tips

- **Responsive Design:** Use `vw`, `vh`, and flexbox for Smart TV-friendly layouts
- **Performance:** Keep animations lightweight for older TV browsers
- **Testing:** Preview animations in a desktop browser before deploying
- **Muted Autoplay:** All videos are auto-muted to comply with Chrome autoplay restrictions

---

## 🧩 Developer Notes

- Built with **Flask-SocketIO + Docker** for lightweight, real-time media control
- Default server port: **8080**

---

## 📄 License

See [LICENSE](LICENSE) for details.
