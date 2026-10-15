import dataclasses

import cdk8s
import pytest

from environments import BASE, for_environment
from microservice import MicroserviceChart


def synth(props):
    app = cdk8s.App()
    chart = MicroserviceChart(app, "t", props)
    return cdk8s.Testing.synth(chart)


def kinds(manifests, kind):
    return [m for m in manifests if m["kind"] == kind]


def test_deployment_exists_with_resources_probes_and_hardening():
    (dep,) = kinds(synth(BASE), "Deployment")
    c = dep["spec"]["template"]["spec"]["containers"][0]
    assert c["resources"]["limits"] and c["resources"]["requests"]
    assert "httpGet" in c["livenessProbe"] and "httpGet" in c["readinessProbe"]
    sc = c["securityContext"]
    assert sc["runAsNonRoot"] is True
    assert sc["readOnlyRootFilesystem"] is True
    assert sc["allowPrivilegeEscalation"] is False
    assert sc["capabilities"] == {"drop": ["ALL"]}


def test_full_golden_path_objects_present():
    m = synth(BASE)
    for kind in ["Deployment", "Service", "ServiceAccount", "ConfigMap", "Secret",
                 "PodDisruptionBudget", "HorizontalPodAutoscaler", "NetworkPolicy", "Ingress"]:
        assert kinds(m, kind), kind


def test_hpa_and_pdb_target_the_deployment():
    m = synth(BASE)
    (dep,) = kinds(m, "Deployment")
    (hpa,) = kinds(m, "HorizontalPodAutoscaler")
    (pdb,) = kinds(m, "PodDisruptionBudget")
    assert hpa["spec"]["scaleTargetRef"]["name"] == dep["metadata"]["name"]
    assert pdb["spec"]["selector"]["matchLabels"] == dep["spec"]["selector"]["matchLabels"]


def test_hpa_toggle_off_sets_fixed_replicas():
    m = synth(dataclasses.replace(BASE, hpa_enabled=False, replicas=3))
    assert not kinds(m, "HorizontalPodAutoscaler")
    assert kinds(m, "Deployment")[0]["spec"]["replicas"] == 3


def test_network_policy_toggle():
    on = kinds(synth(BASE), "NetworkPolicy")
    assert len(on) == 2
    deny = [p for p in on if "ingress" not in p["spec"] and "egress" not in p["spec"]]
    assert len(deny) == 1 and deny[0]["spec"]["policyTypes"] == ["Ingress", "Egress"]
    assert not kinds(synth(dataclasses.replace(BASE, network_policy_enabled=False)), "NetworkPolicy")


def test_ingress_toggle_and_tls():
    (ing,) = kinds(synth(BASE), "Ingress")
    assert ing["spec"]["rules"][0]["host"] == "orders.example.com"
    assert ing["spec"]["tls"][0]["secretName"]
    assert not kinds(synth(dataclasses.replace(BASE, ingress_enabled=False)), "Ingress")


def test_env_map_lands_in_configmap():
    (cm,) = kinds(synth(BASE), "ConfigMap")
    assert cm["data"]["FEATURE_X"] == "false"


def test_prod_overrides_are_higher():
    dev, prod = for_environment("dev"), for_environment("prod")
    assert prod.replicas > dev.replicas
    assert prod.resources.cpu_limit_m > dev.resources.cpu_limit_m


def test_invalid_props_rejected():
    with pytest.raises(ValueError):
        dataclasses.replace(BASE, replicas=0)
