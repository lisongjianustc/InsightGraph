import yaml

def remove_unused_depends():
    with open('docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)
        
    valid_services = set(compose.get('services', {}).keys())
    
    for svc_name, svc in compose.get('services', {}).items():
        if 'depends_on' in svc:
            depends = svc['depends_on']
            if isinstance(depends, list):
                svc['depends_on'] = [d for d in depends if d in valid_services]
            elif isinstance(depends, dict):
                keys_to_remove = [k for k in depends.keys() if k not in valid_services]
                for k in keys_to_remove:
                    del depends[k]
                    
    with open('docker-compose.yml', 'w') as f:
        yaml.dump(compose, f, sort_keys=False, default_flow_style=False)

if __name__ == "__main__":
    remove_unused_depends()