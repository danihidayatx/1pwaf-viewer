# 1Panel WAF & Logs Viewer

A lightweight, interactive Python Flask-based viewer application to read WAF attack logs and website traffic logs directly from the built-in SQLite database of **1Panel OpenResty WAF**.

This application reads data directly from the 1Panel WAF production directory in *real-time* without the need to copy or duplicate the database. It features a Bootstrap 5 and DataTables-based interface for fast searching, sorting, and pagination, even for tens of thousands of log rows.

## Features

*   **Summary Dashboard:** Displays total requests, attacks, and blocked logs.
*   **WAF Attack Logs Viewer:** View details of attacks blocked by the WAF, complete with IP, *Rule Match*, and the action taken.
*   **Site Traffic Logs Viewer:** View specific *traffic* logs per website (HTTP Status, URI, Response Time, etc.) available in 1Panel.
*   **Real-time Database Access:** Reads the built-in `/opt/1panel/apps/openresty/openresty/1pwaf/data/db` database directly if run on a production server.

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
4. Run the Flask application:
   ```bash
   python3 app.py
   ```
5. Open in browser: `http://127.0.0.1:5000`

> **Note:** If run locally, the application will look for database files in the `db` folder located in the same directory as `app.py`.

## Deployment (1Panel UI)

Since this application is intended to work alongside your 1Panel setup, you can easily deploy it directly through the 1Panel dashboard using the Python runtime environment.

1. Ensure you have copied/cloned the application to your server (e.g., `/home/ubuntu/1pwaf-viewer`).
2. In the 1Panel Dashboard, navigate to the Python App creation section (e.g., **Websites > Runtimes > Python**) and add a new application.
3. Fill out the application form with the following details:
   - **Name:** `1pwaf-viewer`
   - **Application Directory:** `/home/ubuntu/1pwaf-viewer` (adjust to your actual path)
   - **Run script:** `pip install -r requirements.txt && gunicorn -w 4 -b 0.0.0.0:5000 app:app`
   - **App port:** `5000`
   - **External port:** `5000` (or any other available port)
   - **External access:** Enable / Add
   - **Container name:** `1pwaf-viewer`
4. Confirm and let 1Panel deploy the application. 

> **Important:** Since the app runs inside a container, ensure that the container has volume mappings or permissions to read the OpenResty WAF database directory, or configure `WAF_DATA_DIR` in your `.env` file appropriately.

### Reverse Proxy Configuration (Optional but Recommended)

If you want to access the application using a domain (e.g., `waf.yourdomain.com`) with HTTPS:

1. Open 1Panel Dashboard -> **Websites**.
2. Click **Create Website** -> Select the **Reverse Proxy** tab.
3. Enter your domain (example: `waf.yourdomain.com`).
4. In the **Proxy Target** section, enter `http://127.0.0.1:5000` (or the corresponding container IP and port).
5. Save and configure SSL as usual through the 1Panel menu.

Now you can safely access the 1Panel WAF Viewer through your domain!