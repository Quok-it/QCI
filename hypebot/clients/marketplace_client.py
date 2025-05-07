import requests
import time
from hypebot.config.config  import HYPERBOLIC_API_KEY
import json
class MarketplaceClient:
    def __init__(self):
        self.marketplace_url = "https://api.hyperbolic.xyz/v1/marketplace"


    # Lists available GPUs with optional API filters and optional name 
    def list_available_gpus(self, filters: dict = None, gpu_name_filter: str = None) -> list:
        payload = {"filters": filters or {}}
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(self.marketplace_url, json=payload, headers=headers)
        response.raise_for_status()

        # get instances
        instances = response.json().get("instances", [])

        available_instances = []
        for instance in instances:
            if (instance["status"] == "node_ready" and
                not instance["reserved"] and
                instance["gpus_reserved"] < instance["gpus_total"]):
                
                # get the GPU model 
                gpu_model = instance["hardware"]["gpus"][0]["model"]if instance["hardware"]["gpus"] else None

                # Only return specified GPU
                if gpu_model: 
                    # checks if we have no filter or if we match a given filter 
                    if gpu_name_filter is None or gpu_name_filter in gpu_model:
                        available_instances.append({
                            "node_id": instance["id"],
                            "cluster_name": instance["cluster_name"],
                            "gpu_model": gpu_model,
                            "gpu_ram": instance["hardware"]["gpus"][0]["ram"] if instance["hardware"]["gpus"] else None,
                            "price_per_hour": instance["pricing"]["price"]["amount"]/100,
                            "region": instance["location"]["region"]
                        })


        return available_instances
    
    def rent_gpu(self, cluster_name: str, node_name: str, gpu_count: int = 1) -> dict:
            url = "https://api.hyperbolic.xyz/v1/marketplace/instances/create"
            headers = {
                "Authorization": f"Bearer {HYPERBOLIC_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "cluster_name": cluster_name,
                    "node_name": node_name,
                "gpu_count": gpu_count,
                "image": {
                    "name": "nvidia/cuda",
                    "tag": "12.3.1-devel-ubuntu22.04",
                    "port": 22
                }
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            return response.json()  # Should contain instance ID, credentials (or ID to fetch them)
    
    def list_user_instances(self) -> list:
        url = "https://api.hyperbolic.xyz/v1/marketplace/instances"
        headers = {
            "Authorization": f"Bearer {HYPERBOLIC_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        full_response = response.json()

        # DEBUG PRINT HERE
        # print("\n[DEBUG] Full Response from /instances API:")
        # import json
        # print(json.dumps(full_response, indent=2))  # Pretty print with indentation

        return full_response.get("instances", [])

    
    def poll_instance_until_ready(self, instance_name: str, max_attempts: int = 25, wait_seconds: int = 5) -> dict:
        attempts = 0
        print("Starting polling...")

        while attempts < max_attempts:
            instances = self.list_user_instances()

            # Print instance names and statuses
            print(f"\n[Poll Attempt {attempts+1}] Available Instances:")
            for inst in instances:
                instance_info = inst.get("instance", {})
                print(f"  - Name: {instance_info.get('id')} | Status: {instance_info.get('status')}")

            found_instance = None
            for instance in instances:
                if instance.get("instance", {}).get("id") == instance_name:
                    found_instance = instance
                    break

            if found_instance:
                status = found_instance.get("instance", {}).get("status", "").lower()
                if status == "online" or status == "ready":
                    return found_instance  # Instance is ready
                else:
                    print(f"[Poll] Attempt {attempts+1}: Instance {instance_name} status = {status}")
            else:
                print(f"[Poll] Attempt {attempts+1}: Instance {instance_name} not found yet.")

            attempts += 1
            time.sleep(wait_seconds)

        raise Exception(f"Instance {instance_name} not ready after {max_attempts} attempts.")
    
    def terminate_instance(self, instance_id: str): 
        url = "https://api.hyperbolic.xyz/v1/marketplace/instances/terminate"
        headers = {
            "Authorization": f"Bearer {HYPERBOLIC_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "id": instance_id
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        full_response = response.json()

        # print("\n[DEBUG] Full Response from /instances API:")
        # print(json.dumps(full_response, indent=2))  # Pretty print with indentation

        return full_response
