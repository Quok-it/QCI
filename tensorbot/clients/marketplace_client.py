import requests
import time
from tensorbot.config.config import TENSORDOCK_API_KEY

class MarketplaceClient:
    def __init__(self):
        self.base_url = "https://api.tensordock.com/api/v2"
        self.headers = {
            "Authorization": f"Bearer {TENSORDOCK_API_KEY}",
            "Content-Type": "application/json"
        }

    def list_available_gpus(self, filters: dict = None, gpu_name_filter: str = None) -> list:
        """Lists available GPUs from TensorDock hostnodes"""
        response = requests.get(f"{self.base_url}/hostnodes", headers=self.headers)
        response.raise_for_status()
        
        hostnodes = response.json().get("data", {}).get("hostnodes", [])
        available_instances = []
        
        for node in hostnodes:
            for gpu in node.get("available_resources", {}).get("gpus", []):
                if gpu["availableCount"] > 0:
                    if gpu_name_filter is None or gpu_name_filter in gpu["v0Name"]:
                        available_instances.append({
                            "node_id": node["id"],
                            "gpu_model": gpu["v0Name"],
                            "price_per_hour": gpu["price_per_hr"],
                            "region": f"{node['location']['city']}, {node['location']['country']}",
                            "available_count": gpu["availableCount"],
                            "max_vcpus_per_gpu": node["available_resources"].get("max_vcpus_per_gpu"),
                            "max_ram_per_gpu": node["available_resources"].get("max_ram_per_gpu")
                        })
        
        return available_instances

    def rent_gpu(self, hostnode_id: str, gpu_model: str, gpu_count: int = 1, 
                 vcpus: int = 8, ram_gb: int = 32, storage_gb: int = 100,
                 ssh_key_id: str = None, ssh_key: str = None) -> dict:
        """
        Rent a GPU on TensorDock
        Either ssh_key_id or ssh_key must be provided
        """
        if not (ssh_key_id or ssh_key) or (ssh_key_id and ssh_key):
            raise ValueError("Either ssh_key_id or ssh_key must be provided (but not both)")

        payload = {
            "data": {
                "type": "virtualmachine",
                "attributes": {
                    "name": f"tensorbot-instance-{int(time.time())}",
                    "type": "virtualmachine",
                    "image": "ubuntu2404",
                    "hostnode_id": hostnode_id,
                    "resources": {
                        "vcpu_count": vcpus,
                        "ram_gb": ram_gb,
                        "storage_gb": storage_gb,
                        "gpus": {
                            gpu_model: {
                                "count": gpu_count
                            }
                        }
                    },
                    "port_forwards": [
                        {
                            "internal_port": 22,
                            "external_port": 20000  # This will be automatically assigned if unavailable
                        }
                    ],
                    "cloud_init": {
                        "package_update": True,
                        "packages": ["nvidia-driver-535", "nvidia-utils-535"]
                    }
                }
            }
        }

        # Add either ssh_key_id or ssh_key
        if ssh_key_id:
            payload["data"]["attributes"]["ssh_key_id"] = ssh_key_id
        else:
            payload["data"]["attributes"]["ssh_key"] = ssh_key

        response = requests.post(f"{self.base_url}/instances", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_user_instances(self) -> list:
        """List all instances for the current user"""
        response = requests.get(f"{self.base_url}/instances", headers=self.headers)
        response.raise_for_status()
        return response.json().get("data", [])

    def poll_instance_until_ready(self, instance_id: str, max_attempts: int = 25, wait_seconds: int = 5) -> dict:
        attempts = 0
        print("Starting polling...")

        while attempts < max_attempts:
            response = requests.get(f"{self.base_url}/instances/{instance_id}", headers=self.headers)
            response.raise_for_status()
            instance_data = response.json().get("data", {})
            
            status = instance_data.get("status", "").lower()
            print(f"[Poll] Attempt {attempts+1}: Instance {instance_id} status = {status}")
            
            if status == "running":
                return instance_data
            
            attempts += 1
            time.sleep(wait_seconds)

        raise Exception(f"Instance {instance_id} not ready after {max_attempts} attempts.")

    def terminate_instance(self, instance_id: str):
        """Terminate a specific instance"""
        response = requests.delete(f"{self.base_url}/instances/{instance_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_hostnode_details(self, hostnode_id: str) -> dict:
        """Get detailed information about a specific hostnode"""
        response = requests.get(f"{self.base_url}/hostnodes/{hostnode_id}", headers=self.headers)
        response.raise_for_status()
        return response.json().get("data", {})