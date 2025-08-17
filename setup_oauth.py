#!/usr/bin/env python3
"""
OAuth Setup Helper for Atlassian MCP Server.
This script helps you complete the OAuth 2.0 flow to get access tokens.
"""

import os
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Atlassian."""

    def do_GET(self):
        """Handle GET request with authorization code."""
        try:
            # Parse the authorization code from the callback URL
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)

            if "code" in query_params:
                auth_code = query_params["code"][0]
                print(f"\n✅ Received authorization code: {auth_code[:20]}...")

                # Exchange code for tokens
                tokens = exchange_code_for_tokens(auth_code)

                if tokens:
                    # Send success response
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    success_html = """
                    <html>
                    <body>
                    <h2>✅ OAuth Setup Complete!</h2>
                    <p>You can close this window and return to the terminal.</p>
                    <p>Your tokens have been saved to the .env file.</p>
                    </body>
                    </html>
                    """
                    self.wfile.write(success_html.encode("utf-8"))

                    # Update .env file
                    update_env_file(tokens)
                    print("✅ Tokens saved to .env file!")

                else:
                    self.send_error(400, "Failed to exchange code for tokens")
            else:
                self.send_error(400, "No authorization code received")

        except Exception as e:
            print(f"❌ Error handling callback: {e}")
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        """Suppress HTTP server logging."""
        pass


def exchange_code_for_tokens(auth_code):
    """Exchange authorization code for access and refresh tokens."""
    try:
        client_id = os.getenv("ATLASSIAN_CLIENT_ID")
        client_secret = os.getenv("ATLASSIAN_CLIENT_SECRET")
        redirect_uri = os.getenv("ATLASSIAN_REDIRECT_URI")

        token_url = "https://auth.atlassian.com/oauth/token"

        data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": auth_code,
            "redirect_uri": redirect_uri,
        }

        print(f"🔄 Exchanging authorization code for tokens...")
        response = requests.post(
            token_url, json=data, headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            tokens = response.json()
            print(f"✅ Successfully obtained tokens!")
            print(f"   Access token: {tokens['access_token'][:20]}...")
            if "refresh_token" in tokens:
                print(f"   Refresh token: {tokens['refresh_token'][:20]}...")
            return tokens
        else:
            print(f"❌ Token exchange failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error exchanging code for tokens: {e}")
        return None


def update_env_file(tokens):
    """Update .env file with new tokens."""
    try:
        with open(".env", "r") as f:
            content = f.read()

        # Update or add access token
        if "ATLASSIAN_ACCESS_TOKEN=" in content:
            # Replace existing
            import re

            content = re.sub(
                r"ATLASSIAN_ACCESS_TOKEN=.*",
                f"ATLASSIAN_ACCESS_TOKEN={tokens['access_token']}",
                content,
            )
        else:
            # Add new
            content += f"\nATLASSIAN_ACCESS_TOKEN={tokens['access_token']}"

        # Update or add refresh token if present
        if "refresh_token" in tokens:
            if "ATLASSIAN_REFRESH_TOKEN=" in content:
                import re

                content = re.sub(
                    r"ATLASSIAN_REFRESH_TOKEN=.*",
                    f"ATLASSIAN_REFRESH_TOKEN={tokens['refresh_token']}",
                    content,
                )
            else:
                content += f"\nATLASSIAN_REFRESH_TOKEN={tokens['refresh_token']}"

        with open(".env", "w") as f:
            f.write(content)

    except Exception as e:
        print(f"❌ Error updating .env file: {e}")


def start_oauth_flow():
    """Start the OAuth 2.0 authorization flow."""
    print("🚀 Starting Atlassian OAuth 2.0 Setup")
    print("=" * 50)

    # Check required environment variables
    client_id = os.getenv("ATLASSIAN_CLIENT_ID")
    client_secret = os.getenv("ATLASSIAN_CLIENT_SECRET")
    redirect_uri = os.getenv("ATLASSIAN_REDIRECT_URI", "http://localhost:8080/callback")

    if not client_id or not client_secret:
        print("❌ Missing ATLASSIAN_CLIENT_ID or ATLASSIAN_CLIENT_SECRET in .env file")
        print(
            "💡 Make sure you've created an OAuth app at https://developer.atlassian.com/console/myapps/"
        )
        return False

    print(f"✅ Client ID: {client_id}")
    print(f"✅ Redirect URI: {redirect_uri}")

    # Required scopes for Jira and Confluence access
    scopes = [
        "read:jira-work",
        "write:jira-work",
        "read:jira-user",
        "read:confluence-content.summary",
        "read:confluence-space.summary",
        "offline_access",  # For refresh token
    ]

    # Build authorization URL
    auth_url = "https://auth.atlassian.com/authorize"
    params = {
        "audience": "api.atlassian.com",
        "client_id": client_id,
        "scope": " ".join(scopes),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "prompt": "consent",
    }

    auth_url_with_params = f"{auth_url}?{urllib.parse.urlencode(params)}"

    print(f"\n🌐 Starting local callback server on port 8080...")

    # Start callback server
    server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print(f"🔗 Opening authorization URL in browser...")
    print(f"📋 If browser doesn't open automatically, visit:")
    print(f"   {auth_url_with_params}")

    # Open browser
    webbrowser.open(auth_url_with_params)

    print(f"\n⏳ Waiting for authorization...")
    print(f"💡 Complete the authorization in your browser")
    print(f"🛑 Press Ctrl+C to cancel")

    try:
        # Keep server running until interrupted
        while True:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n🛑 OAuth setup cancelled")
        server.shutdown()
        return False


def check_existing_tokens():
    """Check if we already have valid tokens."""
    access_token = os.getenv("ATLASSIAN_ACCESS_TOKEN")
    if access_token:
        print(f"✅ Found existing access token: {access_token[:20]}...")

        # Test the token by calling the accessible resources endpoint
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }
            response = requests.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers=headers,
            )

            if response.status_code == 200:
                resources = response.json()
                print(
                    f"✅ Token is valid! Found {len(resources)} accessible resources:"
                )
                for resource in resources:
                    print(f"   - {resource['name']} ({resource['url']})")
                    print(f"     Cloud ID: {resource['id']}")
                return True
            else:
                print(f"❌ Token validation failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error validating token: {e}")
            return False

    return False


if __name__ == "__main__":
    print("🔐 Atlassian OAuth 2.0 Setup Helper")
    print("=" * 40)

    # Check if we already have valid tokens
    if check_existing_tokens():
        print("\n✅ You already have valid OAuth tokens!")
        print("🎯 You can now use the Atlassian MCP server with real data.")
    else:
        print("\n🔄 Setting up OAuth tokens...")

        print("\n📋 PREREQUISITES:")
        print(
            "1. Create an OAuth app at https://developer.atlassian.com/console/myapps/"
        )
        print("2. Set redirect URI to: http://localhost:8080/callback")
        print("3. Add required scopes (Jira and Confluence APIs)")
        print("4. Update .env with CLIENT_ID and CLIENT_SECRET")
        print("\n🚀 Ready to start OAuth flow? (y/n): ", end="")

        if input().lower().startswith("y"):
            start_oauth_flow()
        else:
            print("👋 Setup cancelled. Run this script again when ready!")
