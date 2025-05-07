from primebot.clients.marketplace_client import MarketplaceClient
from primebot.clients.db_interface import DatabaseInterface
from primebot.core.logger import Logger
from primebot.config.config import MONGODB_URI 
from primebot.config.config  import PRIVATE_KEY_PATH
from primebot.core.ssh_manager import SSHManager
import random
import time
from primebot.core.rental_session import RentalSession
from primebot.benchmark.gpu_info_collector import *
logger = Logger() # Initiate logger 

# def main():
#     for i in range (100):
#         logger.log(f"[QUOK IT] {i} TIME!")
#         loop()

def main():
    # logger = Logger() # Initiate logger 
    marketplace_client = MarketplaceClient() # Initialize Marketplace Client
    db_interface = DatabaseInterface(db_uri=MONGODB_URI, collection_name="prime-intellect")
    logger.log("Starting QuokBot...")

    # Get available GPUs (array of dictionary)
    available_gpus = marketplace_client.list_available_gpus()
    return 

    if not available_gpus:
        logger.log("No available GPUs found. Exiting.")
        return
    
    logger.log(f"Found {len(available_gpus)} available GPUs.")

    # Select a GPU 
    selected_node = random.choice(available_gpus)
    model = selected_node["gpu_model"]

    logger.log(f"Selected GPU: {selected_node}")
    # Rent GPU 
    logger.log("Attempting to rent GPU instance...")

    # Create session
    session = RentalSession(
        client_id=selected_node["node_id"],
        cluster_name=selected_node["cluster_name"], 
        marketplace="Hyperbolic", 
        model = model
    )
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
        
        # TODO: handle rental failure 
        return

    # Check if Instance is Ready 
    logger.log("Polling for instance to become ready...")
    start_boot_time = time.time()

    try:
        instance_details = marketplace_client.poll_instance_until_ready(instance_name)
        logger.log(f"Instance info: {instance_details}")
    except Exception as e:
        logger.log_error(e, context="poll_instance_until_ready")
        session.add_error("Machine failed to Boot after 4 minutes")
        session.boot_success = False
        db_interface.save_rental_session(session.to_dict())

        return

    end_rent_time = time.time()

    # Measure boot time 
    boot_time_seconds = end_rent_time - start_boot_time
    boot_time_ms = boot_time_seconds * 1000

    logger.log(f"Instance Boot Time: {boot_time_ms:.2f} ms")
    # During flow:
    session.boot_success = True
    session.boot_time_ms = boot_time_ms
    # TODO: Log checkpoint here rq 
    # db_interface.save_gpu_instance(selected_gpu)
    # logger.log("GPU instance info saved to MongoDB.")

    # SSH Connection stuffs 
    instance_id = instance_details["id"]
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

    if ssh_latency == -1:
        logger.log("[WARN] SSH connection failed. Marking instance as 'ssh_unreachable' in database.")
        # Save to database something like:
        # {"instance_name": ..., "ssh_status": "unreachable"}
        session.ssh_success = False
        session.add_error("SSH failed after 3 attempts")
        db_interface.save_rental_session(session.to_dict())
        cleanup(marketplace_client, ssh_manager, instance_id)
        return
    else:
        session.ssh_success = True
        session.ssh_latency_ms=ssh_latency
        logger.log(f"SSH connection successful. Latency: {ssh_latency:.2f} ms")
    
    logger.log("Running health check....")
    try:
        gpu_health_snapshot = collect_gpu_health_snapshot(ssh_manager)
        session.benchmarks["gpu_health_snapshot"] = gpu_health_snapshot
        logger.log("Health check Completed Successfully!")
    except Exception as e:
        logger.log("GPU health snapshot failed")
        session.add_error(f"GPU health snapshot failed: {str(e)}")
        print(str(e))

    db_interface.save_rental_session(session.to_dict())
    cleanup(marketplace_client, ssh_manager, instance_id)


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

def cleanup(marketplace_client: MarketplaceClient, ssh_manager: SSHManager, instance_id: str): 
    logger.log("---------CLEANUP-------")
    SSHManager.disconnect(ssh_manager) # Disconnect
    logger.log("SSH has been disconeected")
    MarketplaceClient.terminate_instance(marketplace_client, instance_id) # Terminate thhe instance
    logger.log("Instance has been terminated")

if __name__ == "__main__":
    main()
