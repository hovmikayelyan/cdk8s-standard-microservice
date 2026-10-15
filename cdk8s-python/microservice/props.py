"""Input contract of the Standard Microservice ("Golden Path") library."""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class Resources:
    cpu_request_m: int = 100
    cpu_limit_m: int = 500
    memory_request_mi: int = 128
    memory_limit_mi: int = 256


@dataclass(frozen=True)
class MicroserviceProps:
    # Metadata
    app_name: str
    image: str
    namespace: str = "default"
    replicas: int = 2

    # Scaling
    resources: Resources = field(default_factory=Resources)
    hpa_enabled: bool = True
    hpa_max_replicas: int = 5
    hpa_cpu_target_percent: int = 70

    # Connectivity
    container_port: int = 8080
    ingress_enabled: bool = True
    ingress_host: Optional[str] = None  # defaults to "<app_name>.example.com"
    network_policy_enabled: bool = True

    # Probes
    health_path: str = "/healthz"
    ready_path: str = "/readyz"

    # Environment
    env: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.replicas < 1:
            raise ValueError("replicas must be >= 1")
        if self.hpa_enabled and self.hpa_max_replicas < self.replicas:
            raise ValueError("hpa_max_replicas must be >= replicas")
        r = self.resources
        if r.cpu_request_m > r.cpu_limit_m or r.memory_request_mi > r.memory_limit_mi:
            raise ValueError("resource requests must not exceed limits")

    @property
    def host(self) -> str:
        return self.ingress_host or f"{self.app_name}.example.com"
