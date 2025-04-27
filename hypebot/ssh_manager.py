import paramiko
import time
import os 
import socket
class SSHManager:
    def __init__(self, ip: str, username: str, private_key_path: str, port: int = 22):
        self.ip = ip
        self.username = username
        self.private_key_path = private_key_path
        self.port = port
        self.client = None

    def _load_private_key(self):
        """Loads a private key file and logs the key type."""
        if not os.path.exists(self.private_key_path):
            raise FileNotFoundError(f"Private key file not found at: {self.private_key_path}")

        try:
            key = paramiko.Ed25519Key.from_private_key_file(self.private_key_path)
            print(f"[INFO] Private key loaded successfully from {self.private_key_path} (Ed25519)")
            return key
        except paramiko.ssh_exception.PasswordRequiredException:
            raise Exception("Private key is password protected. Cannot load without password.")
        except paramiko.ssh_exception.SSHException:
            # fallback to ECDSA if needed
            raise Exception(f"Failed to load Ed25519 key from {self.private_key_path}. Ensure it is a valid key.")

    def connect_and_measure_latency(self, timeout: int = 30) -> float:
        """Connects over SSH and measures connection time in milliseconds. Returns -1 if failed."""
        key = self._load_private_key()

        start_time = time.time()
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(
                hostname=self.ip,
                username=self.username,
                pkey=key,
                port=self.port,
                timeout=timeout
            )
        except (paramiko.ssh_exception.SSHException, socket.error, TimeoutError) as e:
            print(f"[ERROR] SSH connection failed: {e}")
            return -1  # Special value indicating SSH failure

        end_time = time.time()

        latency_ms = (end_time - start_time) * 1000
        return latency_ms
    def disconnect(self):
        if self.client:
            self.client.close()

    