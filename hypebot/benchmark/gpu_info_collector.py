import re

def collect_gpu_health_snapshot(ssh_manager) -> dict:
    """Collects a full GPU health snapshot by parsing nvidia-smi -q output."""

    # Step 1: Run nvidia-smi -q remotely
    out, err = ssh_manager.run_command("sudo nvidia-smi -q")

    if err.strip():
        raise Exception(f"[ERROR] Failed to run nvidia-smi -q: {err}")
    # print("\n[DEBUG] Raw nvidia-smi -q Output:")
    # print(out)

    snapshot = {"snapshot_version": 1}  # Always version your snapshots

    lines = out.splitlines()
    current_section = None


    for line in lines:
        line = line.strip()
        # print(f"DEBUG: Raw line: {line}")
        if not line:
            continue  # skip empty lines

        # Section detection
        if (":" not in line) and not (line.startswith("-")):
            current_section = line
            # print(f"[DEBUG] Entered section: {current_section}")
            continue

        # Data line inside section
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # print(f"[DEBUG] Parsing {key} = {value} inside {current_section}")
        # -------------------- #
        # Basic flat key parsing
        # -------------------- #
        if line.startswith("GPU UUID"):
            snapshot["gpu_uuid"] = extract_after_colon(line)


        if line.startswith("Product Name"):
            snapshot["product_name"] = extract_after_colon(line)

        if line.startswith("Performance State"):
            snapshot["performance_state"] = extract_after_colon(line)

        if line.startswith("Persistence Mode"):
            snapshot["persistence_mode"] = extract_after_colon(line)

        # Power related
        if line.startswith("Power Draw") and current_section=="GPU Power Readings":
            field_name = "power_draw_watts"
            field_value = extract_number(line)
            snapshot[field_name] = field_value
            # print(f"[Parse] Found {field_name}: {field_value}")
        if line.startswith("Current Power Limit") and current_section=="GPU Power Readings":
            snapshot["current_power_limit_watts"] = extract_number(line)
        if line.startswith("Default Power Limit") and current_section=="GPU Power Readings":
            snapshot["default_power_limit_watts"] = extract_number(line)
        if line.startswith("Max Power Limit") and current_section=="GPU Power Readings":
            snapshot["max_power_limit_watts"] = extract_number(line)
        if line.startswith("Min Power Limit") and current_section=="GPU Power Readings":
            snapshot["min_power_limit_watts"] = extract_number(line)

        # Temperature thresholds
        if line.startswith("GPU Current Temp") and current_section=="Temperature":
            snapshot["temperature_gpu_celsius"] = extract_number(line)
        if line.startswith("GPU Shutdown")and current_section=="Temperature":
            snapshot["gpu_shutdown_temp_celsius"] = extract_number(line)
        if line.startswith("GPU Slowdown")and current_section=="Temperature":
            snapshot["gpu_slowdown_temp_celsius"] = extract_number(line)
        if line.startswith("GPU Max Operating")and current_section=="Temperature":
            snapshot["gpu_max_operating_temp_celsius"] = extract_number(line)
        if line.startswith("GPU Target Temperature")and current_section=="Temperature":
            snapshot["gpu_target_temp_celsius"] = extract_number(line)

        # ECC mode and errors
        if line.startswith("Current") and current_section=="ECC Mode":
            snapshot["ecc_mode"] = extract_after_colon(line)
        if line.startswith("DRAM Correctable") and current_section == "ECC Errors":
            snapshot["ecc_errors_correctable_dram"] = extract_number(line)
        if line.startswith("DRAM Uncorrectable") and current_section == "ECC Errors":
            snapshot["ecc_errors_uncorrectable_dram"] = extract_number(line)

        # Clocks
        if line.startswith("Graphics") and "MHz" in line and current_section == "Clocks":
            snapshot["graphics_clock_mhz"] = extract_number(line)
        if line.startswith("SM") and "MHz" in line and current_section == "Clocks":
            snapshot["sm_clock_mhz"] = extract_number(line)
        if line.startswith("Memory") and "MHz" in line and current_section == "Clocks":
            snapshot["memory_clock_mhz"] = extract_number(line)

        # Max Clocks
        if line.startswith("Graphics") and "MHz" in line and current_section == "Max Clocks":
            snapshot["max_graphics_clock_mhz"] = extract_number(line)
        if line.startswith("SM") and "MHz" in line and current_section == "Max Clocks":
            snapshot["max_sm_clock_mhz"] = extract_number(line)
        if line.startswith("Memory") and "MHz" in line and current_section == "Max Clocks":
            snapshot["max_memory_clock_mhz"] = extract_number(line)
        # Fan speed
        if line.startswith("Fan Speed"):
            snapshot["fan_speed_percent"] = extract_number(line)

        # Memory Usage
        if current_section == "FB Memory Usage":
            if line.startswith("Total"):
                snapshot["memory_total_mb"] = extract_number(line)
            if line.startswith("Used"):
                snapshot["memory_used_mb"] = extract_number(line)
            if line.startswith("Free"):
                snapshot["memory_free_mb"] = extract_number(line)
            if line.startswith("Reserved"):
                snapshot["memory_reserved_mb"] = extract_number(line)

        if current_section == "BAR1 Memory Usage":
            if line.startswith("Total"):
                snapshot["bar1_memory_total_mb"] = extract_number(line)
            if line.startswith("Used"):
                snapshot["bar1_memory_used_mb"] = extract_number(line)
            if line.startswith("Free"):
                snapshot["bar1_memory_free_mb"] = extract_number(line)

        # PCIe Throughput
        if current_section == "PCI":
            if line.startswith("Tx Throughput"):
                snapshot["pci_tx_throughput_kbps"] = extract_number(line)
            if line.startswith("Rx Throughput"):
                snapshot["pci_rx_throughput_kbps"] = extract_number(line)

        # Utilization (from 'Utilization' section)
        if current_section == "Utilization":
            if line.startswith("Gpu"):
                snapshot["gpu_utilization_percent"] = extract_number(line)
            if line.startswith("Memory"):
                snapshot["memory_utilization_percent"] = extract_number(line)
            if line.startswith("Encoder"):
                snapshot["encoder_utilization_percent"] = extract_number(line)
            if line.startswith("Decoder"):
                snapshot["decoder_utilization_percent"] = extract_number(line)

        # XID Errors (will show up if any)
        if "XID" in line:
            snapshot.setdefault("xid_errors", []).append(line)

    return snapshot

# ---------------------- #
# Helper Functions
# ---------------------- #
def extract_number(line: str) -> float:
    """Extracts a number (float or int) from a 'Key : Value' line."""
    match = re.search(r"[-+]?\d*\.\d+|\d+", line)
    return float(match.group()) if match else None

def extract_after_colon(line: str) -> str:
    """Extracts everything after the colon and trims it."""
    return line.split(":", 1)[-1].strip()
