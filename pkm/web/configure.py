#!/usr/bin/env python3
import json
import os
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import argparse

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'web_enabled': False,
            'username': 'admin',
            'password_hash': None,
            'host': '0.0.0.0',
            'port': 5000,
            'secret_key': secrets.token_hex(32),
            'ssl': {
                'enabled': False,
                'cert_path': '',
                'key_path': ''
            },
            'session': {
                'lifetime': 1440,
                'permanent': True
            },
            'security': {
                'max_attempts': 5,
                'lockout_time': 300
            }
        }

def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    print("Configuration saved successfully!")

def enable_web():
    config = load_config()
    config['web_enabled'] = True
    save_config(config)
    print("Web interface enabled!")

def disable_web():
    config = load_config()
    config['web_enabled'] = False
    save_config(config)
    print("Web interface disabled!")

def set_credentials(username, password):
    config = load_config()
    config['username'] = username
    # Use a stronger method for password hashing
    config['password_hash'] = generate_password_hash(password, method='pbkdf2:sha256:600000')
    save_config(config)
    print(f"Credentials updated for user: {username}")
    
    # Verify the password hash works
    if check_password_hash(config['password_hash'], password):
        print("Password hash verification successful!")
    else:
        print("Warning: Password hash verification failed!")

def configure_ssl(cert_path, key_path):
    config = load_config()
    config['ssl']['enabled'] = True
    config['ssl']['cert_path'] = cert_path
    config['ssl']['key_path'] = key_path
    save_config(config)
    print("SSL configuration updated!")

def main():
    parser = argparse.ArgumentParser(description='Configure PKM Web Interface')
    parser.add_argument('--enable', action='store_true', help='Enable web interface')
    parser.add_argument('--disable', action='store_true', help='Disable web interface')
    parser.add_argument('--username', help='Set username')
    parser.add_argument('--password', help='Set password')
    parser.add_argument('--ssl-cert', help='Path to SSL certificate')
    parser.add_argument('--ssl-key', help='Path to SSL private key')
    parser.add_argument('--port', type=int, help='Set web server port')
    parser.add_argument('--status', action='store_true', help='Show current configuration')

    args = parser.parse_args()

    if args.status:
        config = load_config()
        print("\nCurrent Configuration:")
        print(f"Web Interface: {'Enabled' if config['web_enabled'] else 'Disabled'}")
        print(f"Username: {config['username']}")
        print(f"Port: {config['port']}")
        print(f"SSL: {'Enabled' if config['ssl']['enabled'] else 'Disabled'}")
        return

    if args.enable:
        enable_web()

    if args.disable:
        disable_web()

    if args.username and args.password:
        set_credentials(args.username, args.password)

    if args.ssl_cert and args.ssl_key:
        configure_ssl(args.ssl_cert, args.ssl_key)

    if args.port:
        config = load_config()
        config['port'] = args.port
        save_config(config)
        print(f"Port updated to: {args.port}")

    if not any([args.enable, args.disable, args.username, args.ssl_cert, args.port, args.status]):
        parser.print_help()

if __name__ == '__main__':
    main()
