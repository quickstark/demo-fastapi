#!/usr/bin/env python3

"""
GitHub Secrets Setup Script (Python Version)
============================================
This script automatically uploads environment variables to GitHub Secrets
Usage: python scripts/setup_secrets.py .env.production
"""

import os
import sys
import re
import requests
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def get_github_token():
    """Get GitHub token from environment or prompt user"""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        token = input("Enter your GitHub Personal Access Token: ").strip()
    return token

def get_repo_info():
    """Get repository owner and name from git remote or prompt user"""
    try:
        import subprocess
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip()
            # Parse GitHub URL
            match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', url)
            if match:
                return match.group(1), match.group(2)
    except:
        pass
    
    # Fallback to manual input
    owner = input("Enter GitHub repository owner: ").strip()
    repo = input("Enter GitHub repository name: ").strip()
    return owner, repo

def get_public_key(owner, repo, token):
    """Get repository's public key for encryption"""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get public key: {response.text}")
    
    return response.json()

def encrypt_secret(public_key_data, secret_value):
    """Encrypt secret value using repository's public key"""
    public_key_bytes = base64.b64decode(public_key_data)
    public_key = serialization.load_der_public_key(public_key_bytes)
    
    encrypted = public_key.encrypt(
        secret_value.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return base64.b64encode(encrypted).decode('utf-8')

def set_secret(owner, repo, token, secret_name, secret_value, key_id, public_key):
    """Set a secret in the GitHub repository"""
    encrypted_value = encrypt_secret(public_key, secret_value)
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    data = {
        'encrypted_value': encrypted_value,
        'key_id': key_id
    }
    
    response = requests.put(url, headers=headers, json=data)
    return response.status_code in [201, 204]

def parse_env_file(file_path):
    """Parse environment file and return key-value pairs"""
    env_vars = {}
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                env_vars[key] = value
            else:
                print(f"⚠️  Warning: Invalid line {line_num}: {line}")
    
    return env_vars

def is_placeholder_value(value):
    """Check if value is a placeholder that should be skipped"""
    if not value:
        return True
    
    placeholder_patterns = [
        r'^your-',
        r'^sk-your-',
        r'^secret_your-',
        r'^SG\.your-',
        r'your-.*-here$',
        r'your-.*-key$',
        r'your-.*-id$',
        r'your-.*-secret$',
        r'your-.*-name$',
        r'your-.*-string$'
    ]
    
    for pattern in placeholder_patterns:
        if re.match(pattern, value, re.IGNORECASE):
            return True
    
    return False

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python setup_secrets.py <env-file>")
        print("Example: python setup_secrets.py .env.production")
        sys.exit(1)
    
    env_file = sys.argv[1]
    
    if not os.path.exists(env_file):
        print(f"❌ Environment file '{env_file}' not found")
        sys.exit(1)
    
    print("🚀 Setting up GitHub Secrets from", env_file)
    print()
    
    # Get GitHub credentials and repo info
    token = get_github_token()
    owner, repo = get_repo_info()
    
    print(f"📦 Repository: {owner}/{repo}")
    print()
    
    try:
        # Get repository's public key
        public_key_info = get_public_key(owner, repo, token)
        key_id = public_key_info['key_id']
        public_key = public_key_info['key']
        
        # Parse environment file
        env_vars = parse_env_file(env_file)
        
        secret_count = 0
        skipped_count = 0
        
        for key, value in env_vars.items():
            if is_placeholder_value(value):
                print(f"⏭️  Skipping {key} (placeholder value)")
                skipped_count += 1
                continue
            
            print(f"✅ Setting secret: {key}")
            if set_secret(owner, repo, token, key, value, key_id, public_key):
                secret_count += 1
            else:
                print(f"❌ Failed to set secret: {key}")
        
        print()
        print("🎉 Setup complete!")
        print(f"✅ Set {secret_count} secrets")
        print(f"⏭️  Skipped {skipped_count} placeholder values")
        print()
        print("💡 Next steps:")
        print(f"1. Verify secrets in GitHub: https://github.com/{owner}/{repo}/settings/secrets/actions")
        print("2. Push to main branch to trigger deployment")
        print("3. Monitor the GitHub Actions workflow")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 