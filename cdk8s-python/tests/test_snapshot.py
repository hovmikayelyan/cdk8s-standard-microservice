import cdk8s
import pytest

from environments import for_environment
from microservice import MicroserviceChart


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_manifests_match_golden_snapshot(env, snapshot):
    app = cdk8s.App()
    chart = MicroserviceChart(app, f"orders-{env}", for_environment(env))
    assert cdk8s.Testing.synth(chart) == snapshot
