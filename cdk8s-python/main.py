import os
import sys

import cdk8s

from environments import for_environment
from microservice import MicroserviceChart


def build_app(env: str, outdir: str) -> cdk8s.App:
    app = cdk8s.App(outdir=outdir)
    MicroserviceChart(app, f"orders-{env}", for_environment(env))
    return app


if __name__ == "__main__":
    env = os.environ.get("ENVIRONMENT", "dev")
    outdir = sys.argv[1] if len(sys.argv) > 1 else f"../dist/{env}"
    build_app(env, outdir).synth()
