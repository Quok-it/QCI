from marketplace_client import MarketplaceClient
from logger import Logger

def main():
    logger = Logger() # Initiate logger 
    marketplace_client = MarketplaceClient() # Initialize Marketplace Client

    logger.log("Starting QuokBot...")

    # Get available GPUs (array)
    available_gpus = marketplace_client.list_available_gpus(gpu_name_filter="H100")

    for gpu in available_gpus:
        print(f"Available GPU: {gpu['gpu_model']} for ${gpu['price_per_hour']}/hr at {gpu['region']}")

    logger.log(f"Found {len(available_gpus)} GPUs available.")

if __name__ == "__main__":
    main()
