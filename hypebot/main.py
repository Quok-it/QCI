from marketplace_client import MarketplaceClient
from db_interface import DatabaseInterface
from logger import Logger
from config import MONGODB_URI
from ssh_manager import SSHManager
import random
import time
def main():
    logger = Logger() # Initiate logger 
    marketplace_client = MarketplaceClient() # Initialize Marketplace Client
    db_interface = DatabaseInterface(db_uri=MONGODB_URI, collection_name="hyperbolic")

    logger.log("Starting QuokBot...")

    # Get available GPUs (array of dictionary)
    available_gpus = marketplace_client.list_available_gpus(gpu_name_filter="H100")

    if not available_gpus:
        logger.log("No available GPUs found. Exiting.")
        return
    
    logger.log(f"Found {len(available_gpus)} available GPUs.")

    # Select a GPU 
    selected_node = random.choice(available_gpus)
    logger.log(f"Selected GPU: {selected_node}")

    # --------------- RENT GPU ---------------
    logger.log("Attempting to rent GPU instance...")


    try:
        rental_info = marketplace_client.rent_gpu(
            cluster_name=selected_node["cluster_name"],
            node_name=selected_node["node_id"],
            gpu_count=1
        )
        instance_name = rental_info.get("instance_name")
        logger.log(f"Created instance: {instance_name}")
    except Exception as e:
        logger.log_error(e, context="rent_gpu() failed")
        return

    # --------------- POLL FOR INSTANCE READY ---------------
    logger.log("Polling for instance to become ready...")
    start_boot_time = time.time()

    try:
        instance_details = marketplace_client.poll_instance_until_ready(instance_name)
    except Exception as e:
        logger.log_error(e, context="poll_instance_until_ready")
        return

    end_rent_time = time.time()

    # --------------- MEASURE BOOT TIME ---------------
    boot_time_seconds = end_rent_time - start_boot_time
    boot_time_ms = boot_time_seconds * 1000

    logger.log(f"Instance Boot Time: {boot_time_ms:.2f} ms")
    # db_interface.save_gpu_instance(selected_gpu)
    # logger.log("GPU instance info saved to MongoDB.")

if __name__ == "__main__":
    main()
