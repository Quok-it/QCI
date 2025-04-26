from marketplace_client import MarketplaceClient
from db_interface import DatabaseInterface
from logger import Logger
from config import MONGODB_URI
import random
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

    selected_gpu = random.choice(available_gpus)
    logger.log(f"Selected GPU: {selected_gpu}")

    db_interface.save_gpu_instance(selected_gpu)
    logger.log("GPU instance info saved to MongoDB.")

if __name__ == "__main__":
    main()
