import requests

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
