# Standard Microservice – cdk8s (Python) "Golden Path" library

Give it an app name, image and a few knobs; get a production-ready set of Kubernetes manifests.

```
cdk8s-python/   source, tests, Makefile (entry point: main.py)
dist/dev/       synthesized dev manifests
dist/prod/      synthesized prod manifests (higher replicas/limits)
```

## Run

```bash
cd cdk8s-python
make install          # venv + pip install -r requirements.txt
make synth            # -> ../dist/dev/orders-dev.k8s.yaml
make synth-prod       # -> ../dist/prod/orders-prod.k8s.yaml
make test             # unit + snapshot tests
make update-snapshots # accept an intentional manifest change
```

## Layout

| File | Role |
|---|---|
| `microservice/chart.py` | `MicroserviceChart` – orchestrates all resources |
| `microservice/props.py` | `MicroserviceProps` / `Resources` – the input contract (validated) |
| `microservice/secure_defaults.py` | `SecureContainerDefaults` – container + pod hardening |
| `microservice/probes.py` | `StandardProbes` – liveness/readiness |
| `microservice/network_policy.py` | `NetworkPolicyBaseline` – default-deny + minimal allows |
| `environments.py` | dev base + prod overrides |

## Inputs (`MicroserviceProps`)

| Group | Field | Default |
|---|---|---|
| Metadata | `app_name`, `image` (required), `namespace`, `replicas` | `default`, `2` |
| Scaling | `resources` (cpu/memory request+limit), `hpa_enabled`, `hpa_max_replicas`, `hpa_cpu_target_percent` | 100m/500m, 128Mi/256Mi, on, 5, 70 |
| Connectivity | `container_port`, `ingress_enabled`, `ingress_host`, `network_policy_enabled` | 8080, on, `<app>.example.com`, on |
| Probes | `health_path`, `ready_path` | `/healthz`, `/readyz` |
| Environment | `env` (map → ConfigMap, injected via `envFrom`) | `{}` |

Invalid input (replicas < 1, requests > limits, HPA max < replicas) raises at synth time.

## Generated objects

Deployment, Service, ServiceAccount, ConfigMap, Secret (dummy values, `envFrom`), PodDisruptionBudget,
HorizontalPodAutoscaler (CPU), NetworkPolicy (x2), Ingress (host rule + TLS secret reference) + TLS Secret (dummy).

## Golden Path rules enforced

- Containers run as non-root (UID/GID 10001), `runAsNonRoot`, no privilege escalation, not privileged.
- All Linux capabilities dropped; `seccompProfile: RuntimeDefault`; read-only root filesystem (writable `/tmp` emptyDir).
- Requests *and* limits always set.
- Liveness + readiness probes always set.
- ServiceAccount token is not automounted.
- PodDisruptionBudget (`minAvailable: 1`) always created.
- When the HPA is on, the Deployment omits `replicas` (HPA owns it; `minReplicas = replicas`).
- NetworkPolicy: default-deny ingress+egress, then allow only ingress from the `ingress-nginx` namespace on the
  container port and DNS egress to `kube-system`. Anything else needs an explicit extension.
- Secrets in the repo are placeholders only.

## Credentials and secrets
No real credentials are used. The `Secret` and TLS `Secret` in the manifests contain dummy placeholder values
(`dummy-api-key`, `dummy-password`, `dummy-cert`) for demonstration; supply real values through your secret manager or
sealed/external secrets in an actual deployment.
