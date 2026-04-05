import yaml
import sys

def merge_compose():
    # Load ig compose
    with open('docker-compose.yml', 'r') as f:
        ig_compose = yaml.safe_load(f)
        
    # Load dify compose
    with open('dify-source/docker/docker-compose.yaml', 'r') as f:
        dify_compose = yaml.safe_load(f)
        
    # Rename ig services to avoid conflict
    ig_services = ig_compose['services']
    if 'postgres' in ig_services:
        ig_services['ig_postgres'] = ig_services.pop('postgres')
        ig_services['ig_postgres']['container_name'] = 'insight_postgres'
        ig_services['ig_postgres']['ports'] = ['5433:5432'] # Change port
    if 'redis' in ig_services:
        ig_services['ig_redis'] = ig_services.pop('redis')
        ig_services['ig_redis']['container_name'] = 'insight_redis'
        ig_services['ig_redis']['ports'] = ['6380:6379'] # Change port
        
    # Update depends_on and environment for ig services
    if 'n8n' in ig_services:
        n8n_env = ig_services['n8n']['environment']
        for i, e in enumerate(n8n_env):
            if e.startswith('DB_POSTGRESDB_HOST='):
                n8n_env[i] = 'DB_POSTGRESDB_HOST=ig_postgres'
        if 'depends_on' in ig_services['n8n'] and 'postgres' in ig_services['n8n']['depends_on']:
            ig_services['n8n']['depends_on']['ig_postgres'] = ig_services['n8n']['depends_on'].pop('postgres')
            
    if 'backend' in ig_services:
        backend_env = ig_services['backend']['environment']
        for i, e in enumerate(backend_env):
            if e.startswith('DB_HOST='):
                backend_env[i] = 'DB_HOST=ig_postgres'
            elif e.startswith('REDIS_URL='):
                backend_env[i] = 'REDIS_URL=redis://:${REDIS_PASSWORD}@ig_redis:6379/0'
        if 'depends_on' in ig_services['backend']:
            if 'postgres' in ig_services['backend']['depends_on']:
                ig_services['backend']['depends_on']['ig_postgres'] = ig_services['backend']['depends_on'].pop('postgres')
            if 'redis' in ig_services['backend']['depends_on']:
                ig_services['backend']['depends_on']['ig_redis'] = ig_services['backend']['depends_on'].pop('redis')
                
    # Essential Dify services
    dify_essential = [
        'api', 'worker', 'worker_beat', 'web', 'db_postgres', 'redis', 
        'sandbox', 'plugin_daemon', 'ssrf_proxy', 'nginx', 'weaviate', 'init_permissions'
    ]
    
    # Merge dify services into ig_services
    for svc_name in dify_essential:
        if svc_name in dify_compose.get('services', {}):
            svc = dify_compose['services'][svc_name]
            
            # Add env_file to all dify services to point to dify's .env
            if 'env_file' in svc:
                if isinstance(svc['env_file'], list):
                    svc['env_file'] = ['./dify-source/docker/.env'] + svc['env_file']
                else:
                    svc['env_file'] = ['./dify-source/docker/.env', svc['env_file']]
            else:
                svc['env_file'] = ['./dify-source/docker/.env']
                
            # Update volume paths
            if 'volumes' in svc:
                new_volumes = []
                for v in svc['volumes']:
                    if isinstance(v, str) and v.startswith('./volumes/'):
                        new_volumes.append(v.replace('./volumes/', './dify-source/docker/volumes/'))
                    elif isinstance(v, str) and v.startswith('./nginx/'):
                        new_volumes.append(v.replace('./nginx/', './dify-source/docker/nginx/'))
                    elif isinstance(v, str) and v.startswith('./ssrf_proxy/'):
                        new_volumes.append(v.replace('./ssrf_proxy/', './dify-source/docker/ssrf_proxy/'))
                    elif isinstance(v, str) and v.startswith('./'):
                        # e.g., ./dify-source/docker/xxx
                        new_volumes.append(v.replace('./', './dify-source/docker/'))
                    else:
                        new_volumes.append(v)
                svc['volumes'] = new_volumes
                
            ig_services[svc_name] = svc

    # Handle global networks and volumes
    if 'networks' not in ig_compose:
        ig_compose['networks'] = {}
        
    ig_compose['networks']['ssrf_proxy_network'] = {'driver': 'bridge', 'internal': True}
    
    # Optional: handle global volumes if any are used by the imported services
    if 'volumes' in dify_compose:
        if 'volumes' not in ig_compose:
            ig_compose['volumes'] = {}
        for vol in ['db_postgres', 'redis', 'weaviate']:
            if vol in dify_compose['volumes']:
                ig_compose['volumes'][vol] = dify_compose['volumes'][vol]

    # Write merged compose
    with open('docker-compose.yml', 'w') as f:
        yaml.dump(ig_compose, f, sort_keys=False, default_flow_style=False)
        
    print("Merged successfully!")

if __name__ == "__main__":
    merge_compose()