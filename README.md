# Windscribe Port Forwarding Manager

Automatically manages Windscribe ephemeral port forwarding, updates qBittorrent listening ports and restarts Docker containers.

## Credits

**Original Credit:** [Mibo5354](https://github.com/Mibo5354) - [Original Gist](https://gist.github.com/Mibo5354/cf265bc2108edb839e3607d9c9359dfa)

**Forked from:** [JNuggets/Windscribe-Ephemeral-Port-Script](https://github.com/JNuggets/Windscribe-Ephemeral-Port-Script)

**This fork adds:**
- SeleniumBase to bypass Cloudflare challenges
- Discord webhook notifications
- Updates Docker network configuration
- Restarts Docker containers
- Better error handling and reporting
- Comprehensive logging

## ⚠️ Disclaimer

**Important:** Using this script too frequently can lead to temporary account suspension. Windscribe support has confirmed that automation scripts are allowed, but **limit usage to once per week** to avoid overloading their servers.

## Features

- ✅ **Automated Port Updates** - Requests new ephemeral ports from Windscribe
- ✅ **qBittorrent Integration** - Automatically updates listening port
- ✅ **Discord Notifications** - Get notified via webhook (optional)
- ✅ **Cloudflare Bypass** - Handles Cloudflare challenges automatically
- ✅ **Detailed Error Reporting** - Know exactly what failed and why
- ✅ **Screenshot Debugging** - Saves screenshots when error occur
- ✅ **Docker Support** - Updates docker network and restart containers (optional)

## Requirements

- **Python 3.12.3** (tested version)
- Chrome or Chromium browser installed

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Windscribe-Port-Forwarding.git
   cd Windscribe-Port-Forwarding
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env_copy .env
   ```
   
   Edit `.env` and fill in your credentials:
   ```env
   # Windscribe Credentials
   ws_username=your_windscribe_username
   ws_password=your_windscribe_password

   # qBittorrent Configuration
   qbt_host=http://localhost
   qbt_port=8080
   qbt_username=admin
   qbt_password=your_qbt_password

   # Discord Webhook
   discord_webhook_url=https://canary.discord.com/api/webhooks/YOUR_WEBHOOK_URL

   # Docker .env path
   docker_path=
   ```

## Configuration Options

### Required Settings
- `ws_username` - Windscribe username
- `ws_password` - Windscribe password
- `qbt_username` - qBittorrent Web UI username
- `qbt_password` - qBittorrent Web UI password
- `qbt_host` - qBittorrent host (e.g., `http://localhost` or `https://qbit.yourdomain.com`)
- `qbt_port` - qBittorrent Web UI port (default: 8080)

### Optional Settings (leave black to disable)
- `discord_webhook_url` - Discord webhook for notifications (leave blank to disable)
- `docker_path` - Path to docker .env and compose.yaml. Updates .env and restarts docker containers (gluetun, qbittorent, prowlarr). Needed if used TechHuts [guide](https://github.com/TechHutTV/homelab/tree/main/media) to set up servarr. 

