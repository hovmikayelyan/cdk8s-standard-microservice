"""MicroserviceChart: orchestrates every object of the Golden Path."""
import cdk8s
import cdk8s_plus_31 as kplus
from cdk8s_plus_31 import k8s
from constructs import Construct

from .network_policy import NetworkPolicyBaseline
from .probes import StandardProbes
from .props import MicroserviceProps
from .secure_defaults import SecureContainerDefaults


class MicroserviceChart(cdk8s.Chart):
    def __init__(self, scope: Construct, id: str, props: MicroserviceProps) -> None:
        super().__init__(scope, id, namespace=props.namespace)
        self.props = props
        labels = {"app.kubernetes.io/name": props.app_name, "app.kubernetes.io/managed-by": "cdk8s"}

        # --- Config & secrets ------------------------------------------------
        config = kplus.ConfigMap(self, "ConfigMap", data={"LOG_LEVEL": "info", **props.env})
        secret = kplus.Secret(self, "Secret", string_data={"API_KEY": "dummy-api-key", "DB_PASSWORD": "dummy-password"})

        # --- Workload --------------------------------------------------------
        sa = kplus.ServiceAccount(self, "ServiceAccount", automount_token=False)
        deployment = kplus.Deployment(
            self,
            "Deployment",
            replicas=None if props.hpa_enabled else props.replicas,  # HPA owns replicas
            service_account=sa,
            automount_service_account_token=False,
            security_context=SecureContainerDefaults.pod_context(),
            pod_metadata=cdk8s.ApiObjectMetadata(labels=labels),
            metadata=cdk8s.ApiObjectMetadata(labels=labels),
        )

        probes = StandardProbes.http(props.container_port, props.health_path, props.ready_path)
        r = props.resources
        container = deployment.add_container(
            name=props.app_name,
            image=props.image,
            port_number=props.container_port,
            resources=kplus.ContainerResources(
                cpu=kplus.CpuResources(request=kplus.Cpu.millis(r.cpu_request_m), limit=kplus.Cpu.millis(r.cpu_limit_m)),
                memory=kplus.MemoryResources(
                    request=cdk8s.Size.mebibytes(r.memory_request_mi),
                    limit=cdk8s.Size.mebibytes(r.memory_limit_mi),
                ),
            ),
            security_context=SecureContainerDefaults.container_context(),
            liveness=probes.liveness,
            readiness=probes.readiness,
            env_from=[kplus.EnvFrom(config_map=config), kplus.EnvFrom(sec=secret)],
        )
        # Read-only rootfs: give the app a writable scratch dir.
        tmp = kplus.Volume.from_empty_dir(self, "tmp", "tmp")
        container.mount(
            "/tmp",
            tmp,
        )

        service = deployment.expose_via_service(
            name=props.app_name,
            ports=[kplus.ServicePort(port=80, target_port=props.container_port)],
        )

        # --- Resilience ------------------------------------------------------
        k8s.KubePodDisruptionBudget(
            self,
            "PodDisruptionBudget",
            spec=k8s.PodDisruptionBudgetSpec(
                min_available=k8s.IntOrString.from_number(1),
                selector=k8s.LabelSelector(match_labels=deployment.match_labels),
            ),
        )

        if props.hpa_enabled:
            kplus.HorizontalPodAutoscaler(
                self,
                "HorizontalPodAutoscaler",
                target=deployment,
                min_replicas=props.replicas,
                max_replicas=props.hpa_max_replicas,
                metrics=[kplus.Metric.resource_cpu(kplus.MetricTarget.average_utilization(props.hpa_cpu_target_percent))],
            )

        # --- Networking ------------------------------------------------------
        if props.network_policy_enabled:
            NetworkPolicyBaseline(
                self,
                "NetworkPolicy",
                pod_labels=deployment.match_labels,
                port=props.container_port,
            )

        if props.ingress_enabled:
            tls_secret = kplus.Secret(self, "TlsSecret", type="kubernetes.io/tls",
                                      string_data={"tls.crt": "dummy-cert", "tls.key": "dummy-key"})
            ingress = kplus.Ingress(self, "Ingress")
            ingress.add_host_rule(
                props.host, "/", kplus.IngressBackend.from_service(service), kplus.HttpIngressPathType.PREFIX
            )
            ingress.add_tls([kplus.IngressTls(hosts=[props.host], secret=tls_secret)])
