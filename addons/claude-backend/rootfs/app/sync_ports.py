#!/usr/bin/env python3
"""
Sync api_port with ingress_port and ports in config.yaml
Run before the main server starts to ensure ports are synchronized.
"""
import os
import yaml

CONFIG_PATH = "/app/config.yaml"
DEFAULT_PORT = 5000

try:
    # Get the configured API port from environment
    api_port = os.getenv("API_PORT", str(DEFAULT_PORT))
    api_port_str = str(api_port)
    
    # Read current config.yaml
    if not os.path.exists(CONFIG_PATH):
        print(f"Config file not found at {CONFIG_PATH}, skipping port sync")
        exit(0)
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check if port needs updating
    current_ingress_port = config.get('ingress_port')
    current_port_keys = list(config.get('ports', {}).keys()) if config.get('ports') else []
    target_port_key = f"{api_port_str}/tcp"
    
    # Debug logging
    print(f"Current ingress_port: {current_ingress_port}, API_PORT: {api_port_str}")
    print(f"Current port keys: {current_port_keys}, Target: {target_port_key}")
    
    if current_ingress_port != int(api_port_str) or target_port_key not in current_port_keys:
        print(f"Syncing ports: API_PORT={api_port_str}, updating ingress_port and ports...")
        
        # Update ingress_port
        config['ingress_port'] = int(api_port_str)
        
        # Update ports section
        if 'ports' in config:
            # Remove old port entries
            for old_key in current_port_keys:
                if old_key != target_port_key:
                    print(f"Removing old port: {old_key}")
                    del config['ports'][old_key]
            # Add new port entry
            config['ports'][target_port_key] = None
        
        # Update ports_description section
        if 'ports_description' in config:
            # Remove old port descriptions
            old_desc_keys = list(config['ports_description'].keys())
            for old_key in old_desc_keys:
                if old_key != target_port_key:
                    print(f"Removing old port description: {old_key}")
                    del config['ports_description'][old_key]
            # Add new port description
            is_dev = os.getenv("PANEL_TITLE", "").endswith("DEV")
            desc = f"AI Assistant API (DEV)" if is_dev else f"AI Assistant API"
            config['ports_description'][target_port_key] = desc
        
        # Write updated config.yaml
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"Port sync complete: ingress_port={api_port_str}")
    else:
        print(f"Ports already synchronized: ingress_port={current_ingress_port}, api_port={api_port_str}")

except Exception as e:
    print(f"Warning: Failed to sync ports: {e}")
    print("Continuing with current configuration...")
    exit(0)
