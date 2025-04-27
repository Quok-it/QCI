from marketplace_client import MarketplaceClient
from db_interface import DatabaseInterface
from logger import Logger
from config import MONGODB_URI 
from config import PRIVATE_KEY_PATH
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

    # Rent GPU 
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

    # Check if Instance is Ready 
    logger.log("Polling for instance to become ready...")
    start_boot_time = time.time()

    try:
        instance_details = marketplace_client.poll_instance_until_ready(instance_name)
        logger.log(f"Instance info: {instance_details}")
    except Exception as e:
        logger.log_error(e, context="poll_instance_until_ready")
        return

    end_rent_time = time.time()

    # Measure boot time 
    boot_time_seconds = end_rent_time - start_boot_time
    boot_time_ms = boot_time_seconds * 1000

    logger.log(f"Instance Boot Time: {boot_time_ms:.2f} ms")

    # TODO: Log checkpoint here rq 
    # db_interface.save_gpu_instance(selected_gpu)
    # logger.log("GPU instance info saved to MongoDB.")

    # SSH Connection stuffs 
    ssh_command = instance_details["sshCommand"]
    username, host, port = parse_ssh_command(ssh_command) # Extract parameters for ssh manager 
    # initialize ssh manager 
    ssh_manager = SSHManager(
        ip=host,             
        username=username,         
        private_key_path=PRIVATE_KEY_PATH,
        port=port                 
    )

    ssh_latency = SSHManager.connect_and_measure_latency(ssh_manager) # Connect and measure 
    logger.log(f"Instance ssh connection time: {ssh_latency:.2f} ms")


# TODO: Move into utils probably 
def parse_ssh_command(ssh_command: str) -> tuple[str, str, int]:
    """
    Parses the sshCommand string to extract username, hostname, and port.

    Example sshCommand:
      'ssh ubuntu@pertinent-mushroom-panther.1.cricket.hyperbolic.xyz -p 31564'
    
    Returns:
      (username, hostname, port)
    """
    parts = ssh_command.split()

    # parts[1] = ubuntu@hostname
    user_at_host = parts[1]
    username, hostname = user_at_host.split('@')

    # parts[3] = port number
    port = int(parts[3])

    return username, hostname, port

if __name__ == "__main__":
    main()
