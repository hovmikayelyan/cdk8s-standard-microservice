"""Default-deny NetworkPolicy with the minimum explicit allows."""
from typing import Mapping

from constructs import Construct
from cdk8s_plus_31 import k8s


class NetworkPolicyBaseline(Construct):
    """Deny all ingress+egress for the pods, then allow:

    - ingress on the container port from the ingress controller namespace
    - egress DNS (UDP/TCP 53) to kube-system
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        pod_labels: Mapping[str, str],
        port: int,
        ingress_namespace: str = "ingress-nginx",
    ) -> None:
        super().__init__(scope, id)
        selector = k8s.LabelSelector(match_labels=dict(pod_labels))

        # An empty rule list with both policyTypes == deny all.
        k8s.KubeNetworkPolicy(
            self,
            "default-deny",
            spec=k8s.NetworkPolicySpec(
                pod_selector=selector,
                policy_types=["Ingress", "Egress"],
            ),
        )

        k8s.KubeNetworkPolicy(
            self,
            "allow",
            spec=k8s.NetworkPolicySpec(
                pod_selector=selector,
                policy_types=["Ingress", "Egress"],
                ingress=[
                    k8s.NetworkPolicyIngressRule(
                        from_=[
                            k8s.NetworkPolicyPeer(
                                namespace_selector=k8s.LabelSelector(
                                    match_labels={"kubernetes.io/metadata.name": ingress_namespace}
                                )
                            )
                        ],
                        ports=[k8s.NetworkPolicyPort(port=k8s.IntOrString.from_number(port), protocol="TCP")],
                    )
                ],
                egress=[
                    k8s.NetworkPolicyEgressRule(
                        to=[
                            k8s.NetworkPolicyPeer(
                                namespace_selector=k8s.LabelSelector(
                                    match_labels={"kubernetes.io/metadata.name": "kube-system"}
                                )
                            )
                        ],
                        ports=[
                            k8s.NetworkPolicyPort(port=k8s.IntOrString.from_number(53), protocol="UDP"),
                            k8s.NetworkPolicyPort(port=k8s.IntOrString.from_number(53), protocol="TCP"),
                        ],
                    )
                ],
            ),
        )
