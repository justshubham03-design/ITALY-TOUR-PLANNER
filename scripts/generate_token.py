#!/usr/bin/env python3
"""
Generate token.json from Google OAuth2 credentials.json (Zero dependencies).
Auto-resolves credentials file from project directory or current working directory.
"""

import os
import sys
import json
import urllib.parse
import urllib.request

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cloud-platform"
]

def find_file(filename):
    if os.path.exists(filename):
        return os.path.abspath(filename)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, filename)
    if os.path.exists(candidate):
        return candidate
    
    parent_dir = os.path.dirname(script_dir)
    candidate = os.path.join(parent_dir, filename)
    if os.path.exists(candidate):
        return candidate
    
    workspace_root = "/Users/shubham73/Desktop/italy travel planner"
    candidate = os.path.join(workspace_root, filename)
    if os.path.exists(candidate):
        return candidate
    
    return None

def load_credentials():
    creds_path = find_file("credentials.json") or find_file("credential.json")
    if not creds_path:
        print(f"Error: Neither 'credentials.json' nor 'credential.json' found.")
        print(f"Looked in:\n - {os.getcwd()}\n - /Users/shubham73/Desktop/italy travel planner")
        sys.exit(1)
    
    print(f"Using credentials from: {creds_path}")
    with open(creds_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    creds = data.get('installed') or data.get('web')
    if not creds:
        print("Error: Invalid credentials format. Expected 'installed' or 'web' key.")
        sys.exit(1)
    
    target_dir = os.path.dirname(creds_path)
    token_save_path = os.path.join(target_dir, "token.json")
    return creds, token_save_path

def exchange_code_for_token(client_id, client_secret, code, redirect_uri, token_save_path, token_uri="https://oauth2.googleapis.com/token"):
    print("\nExchanging authorization code for OAuth tokens...")
    payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    data = urllib.parse.urlencode(payload).encode('utf-8')
    req = urllib.request.Request(
        token_uri,
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            token_data = json.loads(response.read().decode('utf-8'))
            
            with open(token_save_path, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, indent=2)
            
            print(f"\n========================================================")
            print(f" [SUCCESS] token.json generated successfully!")
            print(f" Saved to: {token_save_path}")
            print(f"========================================================")
            print(f"Access Token: {token_data.get('access_token', '')[:25]}...")
            if 'refresh_token' in token_data:
                print(f"Refresh Token: {token_data.get('refresh_token', '')[:25]}...")
            print(f"Expires In: {token_data.get('expires_in')} seconds\n")
            return token_data
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"\n[ERROR] Failed to exchange code for token: {e}")
        print(f"Details: {err_body}")
        sys.exit(1)

def generate_auth_url(client_id, redirect_uri, scopes=None, auth_uri="https://accounts.google.com/o/oauth2/auth"):
    scopes = scopes or DEFAULT_SCOPES
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(scopes),
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return f"{auth_uri}?{urllib.parse.urlencode(params)}"

def main():
    creds, token_save_path = load_credentials()
    client_id = creds['client_id']
    client_secret = creds['client_secret']
    auth_uri = creds.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth')
    token_uri = creds.get('token_uri', 'https://oauth2.googleapis.com/token')
    
    redirect_uris = creds.get('redirect_uris', ['http://localhost'])
    redirect_uri = redirect_uris[0] if redirect_uris else 'http://localhost'
    
    auth_url = generate_auth_url(client_id, redirect_uri, scopes=DEFAULT_SCOPES, auth_uri=auth_uri)
    
    print("=" * 70)
    print(" Google OAuth 2.0 Token Generator")
    print("=" * 70)
    print("\n1. Open this authorization URL in your web browser:\n")
    print(auth_url)
    print("\n" + "=" * 70)
    print("2. Sign in and grant permissions.")
    print("3. Google will redirect you to: http://localhost/?code=4/0A...&scope=...")
    print("4. Copy the full redirect URL (or just the 'code' parameter value) and paste it below:\n")
    
    try:
        user_input = input("Paste the code or redirect URL here: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)
    
    if not user_input:
        print("No code provided. Exiting.")
        sys.exit(1)
    
    if 'code=' in user_input:
        parsed = urllib.parse.urlparse(user_input)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get('code', [None])[0]
        if not code:
            qs = user_input.split('code=')[-1].split('&')[0]
            code = urllib.parse.unquote(qs)
    else:
        code = user_input
    
    if not code:
        print("Could not extract authorization code.")
        sys.exit(1)
    
    exchange_code_for_token(client_id, client_secret, code, redirect_uri, token_save_path, token_uri)

if __name__ == '__main__':
    main()
