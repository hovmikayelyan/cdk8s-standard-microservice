"""Standard liveness/readiness probes."""
from dataclasses import dataclass

import cdk8s
import cdk8s_plus_31 as kplus


@dataclass(frozen=True)
class StandardProbes:
    liveness: kplus.Probe
    readiness: kplus.Probe

    @classmethod
    def http(cls, port: int, health_path: str, ready_path: str) -> "StandardProbes":
        return cls(
            liveness=kplus.Probe.from_http_get(
                health_path,
                port=port,
                initial_delay_seconds=cdk8s.Duration.seconds(10),
                period_seconds=cdk8s.Duration.seconds(10),
                timeout_seconds=cdk8s.Duration.seconds(2),
                failure_threshold=3,
            ),
            readiness=kplus.Probe.from_http_get(
                ready_path,
                port=port,
                initial_delay_seconds=cdk8s.Duration.seconds(5),
                period_seconds=cdk8s.Duration.seconds(5),
                timeout_seconds=cdk8s.Duration.seconds(2),
                failure_threshold=3,
            ),
        )
