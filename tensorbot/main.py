from tensorbot.clients.marketplace_client import MarketplaceClient
from tensorbot.clients.db_interface import DatabaseInterface
from tensorbot.core.logger import Logger
from tensorbot.config.config import MONGODB_URI 
from tensorbot.config.config  import PRIVATE_KEY_PATH
from tensorbot.config.config import SSH_PUBLIC_KEY
from tensorbot.core.ssh_manager import SSHManager
import random
import time
from tensorbot.core.rental_session import RentalSession
from tensorbot.benchmark.gpu_info_collector import *
logger = Logger() # Initiate logger 

def main():
    for i in range (100):
        logger.log(f"[QUOK IT] {i} TIME!")
        loop()

def loop():
    marketplace_client = MarketplaceClient()
    db_interface = DatabaseInterface(db_uri=MONGODB_URI, collection_name="tensordock")
    logger.log("Starting QuokBot...")

    # Get available GPUs from hostnodes
    available_gpus = []
    try:
        hostnodes = marketplace_client.list_available_gpus()
        
        # Process each hostnode to extract GPU information
        for node in hostnodes:
            node_gpus = node.get("available_resources", {}).get("gpus", [])
            for gpu in node_gpus:
                if gpu["availableCount"] > 0:
                    available_gpus.append({
                        "node_id": node["id"],
                        "gpu_model": gpu["v0Name"],
                        "available_count": gpu["availableCount"],
                        "price_per_hour": gpu["price_per_hr"],
                        "location": {
                            "city": node["location"]["city"],
                            "country": node["location"]["country"]
                        },
                        "max_vcpus": node["available_resources"].get("max_vcpus_per_gpu", 8),
                        "max_ram": node["available_resources"].get("max_ram_per_gpu", 32)
                    })

    except Exception as e:
        logger.log_error(e, context="Failed to fetch available GPUs")
        return

    if not available_gpus:
        logger.log("No available GPUs found. Exiting.")
        return
    
    logger.log(f"Found {len(available_gpus)} available GPUs.")

    # Select a GPU 
    selected_gpu = random.choice(available_gpus)
    logger.log(f"Selected GPU: {selected_gpu}")
    
    # Create session with TensorDock specific information
    session = RentalSession(
        client_id=selected_gpu["node_id"],
        marketplace="TensorDock", 
        model=selected_gpu["gpu_model"]
    )

    # Calculate resources based on GPU limits
    vcpu_count = min(selected_gpu["max_vcpus"], 8)  # Use 8 vCPUs or max available
    ram_gb = min(selected_gpu["max_ram"], 32)      # Use 32GB RAM or max available

    # Rent GPU with TensorDock configuration
    try:
        rental_info = marketplace_client.rent_gpu(
            hostnode_id=selected_gpu["node_id"],
            gpu_model=selected_gpu["gpu_model"],
            gpu_count=1,
            vcpus=vcpu_count,
            ram_gb=ram_gb,
            storage_gb=100,  # Minimum required by TensorDock
            ssh_key=SSH_PUBLIC_KEY,
            instance_name=f"quokbot-{int(time.time())}"
        )
        
        # Extract instance ID from TensorDock response
        instance_id = rental_info["data"]["id"]
        logger.log(f"Created instance: {instance_id}")
        
    except Exception as e:
        logger.log_error(e, context="rent_gpu() failed")
        session.add_error(f"Failed to rent GPU: {str(e)}")
        db_interface.save_rental_session(session.to_dict())
        return

    # Poll for instance readiness
    logger.log("Polling for instance to become ready...")
    start_boot_time = time.time()

    try:
        instance_details = marketplace_client.poll_instance_until_ready(instance_id)
        
        # Verify instance is running
        if instance_details.get("status") != "running":
            raise Exception(f"Instance status is {instance_details.get('status')}")
            
        logger.log(f"Instance info: {instance_details}")
        
    except Exception as e:
        logger.log_error(e, context="poll_instance_until_ready")
        session.add_error("Machine failed to Boot after timeout")
        session.boot_success = False
        db_interface.save_rental_session(session.to_dict())
        return

    end_rent_time = time.time()
    boot_time_ms = (end_rent_time - start_boot_time) * 1000
    logger.log(f"Instance Boot Time: {boot_time_ms:.2f} ms")
    session.boot_success = True
    session.boot_time_ms = boot_time_ms

    # Get SSH connection details from instance
    try:
        # Find SSH port from port forwards
        port_forwards = instance_details.get("attributes", {}).get("port_forwards", [])
        ssh_port = next(
            (pf["external_port"] for pf in port_forwards if pf["internal_port"] == 22),
            None
        )
        
        if not ssh_port:
            raise ValueError("No SSH port forwarding found")

        # Get instance IP
        host = instance_details.get("attributes", {}).get("ip_address")
        if not host:
            raise ValueError("No IP address found for instance")

        # Initialize SSH manager with TensorDock's Ubuntu username
        ssh_manager = SSHManager(
            ip=host,
            username="ubuntu",  # TensorDock uses 'ubuntu' for Ubuntu images
            private_key_path=PRIVATE_KEY_PATH,
            port=ssh_port
        )

        # Rest of the SSH connection logic remains the same
        ssh_latency = SSHManager.connect_and_measure_latency(ssh_manager)
        if ssh_latency == -1:
            logger.log("[WARN] SSH connection failed")
            session.ssh_success = False
            session.add_error("SSH failed after 3 attempts")
            db_interface.save_rental_session(session.to_dict())
            cleanup(marketplace_client, ssh_manager, instance_id)
            return
            
        session.ssh_success = True
        session.ssh_latency_ms = ssh_latency
        logger.log(f"SSH connection successful. Latency: {ssh_latency:.2f} ms")
        logger.log("Running health check....")


    except Exception as e:
        logger.log_error(e, context="ssh_setup")
        session.add_error(f"SSH setup failed: {str(e)}")
        cleanup(marketplace_client, None, instance_id)
        return
    try:
        gpu_health_snapshot = collect_gpu_health_snapshot(ssh_manager)
        session.benchmarks["gpu_health_snapshot"] = gpu_health_snapshot
        logger.log("Health check Completed Successfully!")
    except Exception as e:
        logger.log("GPU health snapshot failed")
        session.add_error(f"GPU health snapshot failed: {str(e)}")
        print(str(e))
    
    # Run benchmarking commands
    logger.log("Starting benchmarking process...")
    try:
        # Setup benchmarking environment
        setup_commands = """
        rm -rf benchmarking && \
        git clone https://github.com/Quok-it/benchmarking && \
        cd benchmarking && \
        chmod +x benchmarks.sh
        """
        
        stdout, stderr = ssh_manager.run_command(setup_commands)
        if stderr:
            logger.log(f"Warning during benchmark setup: {stderr}")
        
        # Run benchmark with output redirection and explicit shell
        logger.log("Running benchmarks (this will take approximately 30 minutes)...")
        benchmark_cmd = """
        cd benchmarking && \
        ./benchmarks.sh 2>&1 | tee benchmark_output.log && \
        echo "=== BENCHMARK COMPLETE ===" && \
        cat benchmark_output.log && \
        python3 parse.py | tee parse_output.json && \
        cat parse_output.json
        """
        
        stdout, stderr = ssh_manager.run_command(benchmark_cmd)
        logger.log("Benchmark command completed")
        
        # Log everything for debugging
        logger.log("Benchmark stdout:")
        logger.log(stdout)
        if stderr:
            logger.log("Benchmark stderr:")
            logger.log(stderr)
        
        # Try to parse the JSON output
        try:
            import json
            # Look for the last JSON object in the output
            json_lines = [line for line in stdout.split('\n') if line.strip().startswith('{')]
            if json_lines:
                benchmark_results = json.loads(json_lines[-1])
                session.benchmarks["gpu_benchmarks"] = benchmark_results
                logger.log("Successfully stored benchmark results in session!")
            else:
                # Check if the output file exists and try to read it directly
                stdout, stderr = ssh_manager.run_command("cd benchmarking && cat parse_output.json")
                if stdout and stdout.strip().startswith('{'):
                    benchmark_results = json.loads(stdout)
                    session.benchmarks["gpu_benchmarks"] = benchmark_results
                    logger.log("Successfully stored benchmark results from file!")
                else:
                    raise ValueError("No JSON output found in benchmark results or output file")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.log(f"Error parsing benchmark results: {e}")
            logger.log(f"Raw output was: {stdout}")
            session.add_error("Failed to parse benchmark results")
            
    except Exception as e:
        logger.log("Benchmarking process failed")
        session.add_error(f"Benchmarking failed: {str(e)}")
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
    if ssh_manager:
        SSHManager.disconnect(ssh_manager)
        logger.log("SSH has been disconnected")
    
    try:
        marketplace_client.terminate_instance(instance_id)
        logger.log("Instance has been terminated")
    except Exception as e:
        logger.log(f"Error during instance termination: {str(e)}")

if __name__ == "__main__":
    main()
