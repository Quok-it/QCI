import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

class RentalSession:
    def __init__(self, client_id: str, cluster_name: str):
        self.session_id = str(uuid.uuid4())
        self.client_id = client_id
        self.cluster_name = cluster_name
        self.start_time = datetime.now(timezone.utc).isoformat()

        # Optional fields that will be populated over time
        self.boot_success: Optional[bool] = None
        self.boot_time_ms: Optional[float] = None
        self.ssh_success: Optional[bool] = None
        self.ssh_latency_ms: Optional[float] = None
        self.gpu_info: Optional[Dict[str, Any]] = None
        self.cpu_info: Optional[Dict[str, Any]] = None
        self.ram_info: Optional[Dict[str, Any]] = None
        self.storage_info: Optional[Dict[str, Any]] = None
        self.benchmarks = {}
        self.errors: List[str] = []
        self.termination_time: Optional[str] = None
        self.termination_status: Optional[str] = None

    def add_error(self, error_message: str):
        self.errors.append(error_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the session to a MongoDB-insertable dictionary."""
        return {
            "session_id": self.session_id,
            "client_id": self.client_id,
            "cluster_name": self.cluster_name,
            "start_time": self.start_time,
            "boot_success": self.boot_success,
            "boot_time_ms": self.boot_time_ms,
            "ssh_success": self.ssh_success,
            "ssh_latency_ms": self.ssh_latency_ms,
            "gpu_info": self.gpu_info,
            "cpu_info": self.cpu_info,
            "ram_info": self.ram_info,
            "storage_info": self.storage_info,
            "benchmarks": self.benchmarks,
            "errors": self.errors,
            "termination_time": self.termination_time,
            "termination_status": self.termination_status,
        }
