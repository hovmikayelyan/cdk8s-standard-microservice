"""Per-environment overrides applied on top of the base service definition."""
import dataclasses

from microservice import MicroserviceProps, Resources

BASE = MicroserviceProps(
    app_name="orders",
    namespace="shop",
    image="registry.example.com/shop/orders:1.0.0",
    env={"FEATURE_X": "false"},
)

PROD_OVERRIDES = dict(
    replicas=4,
    hpa_max_replicas=20,
    resources=Resources(cpu_request_m=500, cpu_limit_m=1000, memory_request_mi=512, memory_limit_mi=1024),
    env={"FEATURE_X": "true", "LOG_LEVEL": "warn"},
)


def for_environment(name: str) -> MicroserviceProps:
    if name == "dev":
        return BASE
    if name == "prod":
        return dataclasses.replace(BASE, **PROD_OVERRIDES)
    raise ValueError(f"unknown environment {name!r}")
