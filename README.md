# 1Panel WAF & Logs Viewer

A lightweight, interactive Python Flask-based viewer application to read WAF attack logs and website traffic logs directly from the built-in SQLite database of **1Panel OpenResty WAF**.

This application reads data directly from the 1Panel WAF production directory in *real-time* without the need to copy or duplicate the database. It features a Bootstrap 5 and DataTables-based interface for fast searching, sorting, and pagination, even for tens of thousands of log rows.

## Features

*   **Summary Dashboard:** Displays total requests, attacks, and blocked logs.
*   **WAF Attack Logs Viewer:** View details of attacks blocked by the WAF, complete with IP, *Rule Match*, and the action taken.
*   **Site Traffic Logs Viewer:** View specific *traffic* logs per website (HTTP Status, URI, Response Time, etc.) available in 1Panel.
*   **Real-time Database Access:** Reads the built-in `/opt/1panel/apps/openresty/openresty/1pwaf/data/db` database directly if run on a production server.
*   **HTTP Basic Authentication:** Built-in protection to secure your logs viewer from unauthorized access.

## System Requirements

*   Python 3.8+
*   *Root* access (or read permission to the 1Panel WAF directory) if run on a production server.

## Installation (Local / Development)

1. Clone this repository or copy all files into a single folder.
2. Create a Virtual Environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies (including Flask and Gunicorn):
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment template and configure (see Security section below):
   ```bash
   cp .env.example .env
   ```
5. Run the Flask application:
   ```bash
   python3 app.py
   ```
6. Open in browser: `http://127.0.0.1:5000`

> **Note:** If run locally, the application will look for database files in the `db` folder located in the same directory as `app.py`.

## Security & Authentication

To protect your logs from unauthorized access, it is highly recommended to enable HTTP Basic Authentication.

1. Edit the `.env` file in your application directory.
2. Set your desired username and password:
   ```env
   BASIC_AUTH_USERNAME=admin
   BASIC_AUTH_PASSWORD=your_secure_password
   ```
If you leave these variables blank or commented out, the application will be accessible without a password.

## Deployment & Production Security (1Panel UI)

**⚠️ IMPORTANT:** Do not expose the application port (e.g., `5000`) directly to the public internet, even with Basic Authentication enabled. It is much safer to keep the application internal and access it via a Reverse Proxy (with HTTPS) or a secure VPN like Tailscale.

### Method 1: Website Runtime via 1Panel (Recommended)

1Panel allows you to create a website that connects directly to your Python application container. This automatically sets up the proxy and SSL.

1. **Step 1: Create Python Runtime**
   - Go to **Websites > Runtimes > Python** and click **Create Python App**.
   - **Name:** `1pwaf-viewer`
   - **Application Directory:** `/home/ubuntu/1pwaf-viewer` (adjust to your actual path)
   - **Run script:** `pip install -r requirements.txt && gunicorn -w 4 -b 0.0.0.0:5000 app:app`
   - **App port:** `5000`
   - **External port:** Leave it empty (to keep it private from the public internet).
   - **External access:** Disable.
2. **Step 2: Create the Website**
   - Go to **Websites > Websites** and click **Create Website**.
   - Select the **Runtime** tab.
   - **Type:** Choose `Python`.
   - **Runtime:** Select the `1pwaf-viewer` runtime you created in Step 1.
   - **Primary domain:** Enter your domain (e.g., `waf.yourdomain.com`).
3. **Step 3: Enable HTTPS**
   - After the website is created, go to the website settings and enable **HTTPS/SSL** to ensure your Basic Auth credentials are encrypted.

> **Important:** Since the app runs inside a container, ensure that the container has volume mappings or permissions to read the OpenResty WAF database directory (`/opt/1panel/apps/openresty/openresty/1pwaf/data/db`). You may need to add this path to the **Volume** configuration when creating the Python Runtime.

> **Important:** Since the app runs inside a container, ensure that the container has volume mappings or permissions to read the OpenResty WAF database directory, or configure `WAF_DATA_DIR` in your `.env` file appropriately.

### Method 2: Access via Tailscale (VPN)

If you do not want to expose the viewer to the public internet at all (no public domain required):

1. Install Tailscale on your server and your local machine.
2. When deploying the app (or running Gunicorn), bind it exclusively to your Tailscale IP address (e.g., `100.x.y.z:5000`) or keep it on `127.0.0.1` and use a local web server (like Nginx) to proxy requests from the Tailscale interface.
3. Access the viewer securely through your browser using your server's Tailscale IP address. This completely hides the application from public network scans.
