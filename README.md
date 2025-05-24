# QCI

A comprehensive Python-based automation suite for managing, testing, and benchmarking GPU instances across multiple cloud marketplaces.

## Overview

This repository contains two main automation bots:

- **Hypebot**: Automation for the Hyperbolic marketplace
- **Primebot**: Automation for the Prime Intellect marketplace

Both bots are designed to automate the process of:

- Discovering available GPU instances
- Renting and managing GPU instances
- Running health checks and benchmarks
- Collecting and storing performance metrics
- Managing instance lifecycles

## Features

### Core Features

- Multi-marketplace support
- Automated GPU instance management
- SSH-based remote command execution
- Comprehensive GPU health monitoring
- Automated benchmarking
- MongoDB integration for data storage
- Robust logging and error handling

### Supported Marketplaces

- Hyperbolic (via hypebot)
- Prime Intellect (via primebot-- NOT DONE YET)

## Prerequisites

- Python 3.x
- MongoDB database
- SSH key pair for remote access
- API keys for supported marketplaces

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Quok-it/QCI
cd QCI
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
MONGODB_URI=your_mongodb_connection_string
HYPERBOLIC_API_KEY=your_hyperbolic_api_key
PRIVATE_KEY_PATH=path_to_your_ssh_private_key
```

## Project Structure

├── hypebot/ # Hyperbolic marketplace automation
│ ├── benchmark/ # Benchmarking tools
│ ├── clients/ # API clients
│ ├── config/ # Configuration
│ ├── core/ # Core functionality
│ └── main.py
├── primebot/ # Prime Intellect marketplace automation
│ ├── benchmark/
│ ├── clients/
│ ├── config/
│ ├── core/
│ └── main.py
├── requirements.txt # Python dependencies
├── LICENSE # License information
└── .gitignore # Git ignore rules

## Usage

### Running Hypebot

```bash
python -m hypebot.main
```

### Running Primebot

```bash
python -m primebot.main
```

Each bot will:

1. Connect to its respective marketplace
2. Search for available GPU instances
3. Rent and configure instances
4. Run health checks and benchmarks
5. Store results in MongoDB
6. Clean up resources

## Configuration

### Environment Variables

Required environment variables:

- `MONGODB_URI`: MongoDB connection string
- `HYPERBOLIC_API_KEY`: API key for Hyperbolic marketplace
- `PRIVATE_KEY_PATH`: Path to SSH private key

### MongoDB Structure

The system uses the following collections:

- `hyperbolic`: Data from Hyperbolic marketplace
- `prime-intellect`: Data from Prime Intellect marketplace


## Authors

QCI Development Team
