#!/usr/bin/env python3
"""Simple CORS proxy for Jira Cloud API.

This proxy allows the demo UI to access Jira Cloud API from the browser
without CORS issues.

Usage:
    python scripts/jira_proxy.py
    
Then in demo UI, use: http://localhost:8080/proxy
"""

import base64
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests


class JiraProxyHandler(BaseHTTPRequestHandler):
    """HTTP handler that proxies requests to Jira Cloud."""
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Jira-Email')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        # Parse URL
        parsed = urlparse(self.path)
        
        if parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return
        
        if not parsed.path.startswith('/proxy'):
            self.send_error(404, "Not found")
            return
        
        # Get auth headers
        auth_header = self.headers.get('Authorization')
        email = self.headers.get('X-Jira-Email')
        
        if not auth_header or not email:
            self.send_error(401, "Missing Authorization or X-Jira-Email header")
            return
        
        # Extract API token from Authorization header
        if auth_header.startswith('Bearer '):
            api_token = auth_header[7:]
        else:
            self.send_error(401, "Invalid Authorization header format")
            return
        
        # Get Jira URL and path from query params
        query_params = parse_qs(parsed.query)
        jira_url = query_params.get('jira_url', ['https://insight-bridge.atlassian.net'])[0]
        jira_path = query_params.get('path', ['/rest/api/3/search'])[0]
        
        # Build full Jira URL
        full_url = f"{jira_url}{jira_path}"
        
        # Add any additional query params
        extra_params = {k: v[0] for k, v in query_params.items() if k not in ['jira_url', 'path']}
        
        try:
            # Create Basic Auth header
            auth_string = f"{email}:{api_token}"
            auth_b64 = base64.b64encode(auth_string.encode()).decode()
            
            # Make request to Jira
            response = requests.get(
                full_url,
                params=extra_params,
                headers={
                    'Authorization': f'Basic {auth_b64}',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            # Send response back to client
            self.send_response(response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.content)
            
        except Exception as e:
            self.send_error(500, f"Proxy error: {str(e)}")
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_proxy(port=8080):
    """Run the proxy server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, JiraProxyHandler)
    print(f"🚀 Jira CORS Proxy running on http://localhost:{port}")
    print(f"   Health check: http://localhost:{port}/health")
    print(f"   Proxy endpoint: http://localhost:{port}/proxy")
    print(f"\n   Usage in demo UI:")
    print(f"   - Set proxy URL: http://localhost:{port}/proxy")
    print(f"   - Add X-Jira-Email header with your email")
    print(f"   - Add Authorization: Bearer YOUR_API_TOKEN")
    print(f"\n   Press Ctrl+C to stop\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down proxy server...")
        httpd.shutdown()


if __name__ == '__main__':
    run_proxy()

