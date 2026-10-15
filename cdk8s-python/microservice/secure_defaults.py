"""Hardened container/pod defaults: non-root, no capabilities, read-only rootfs."""
import cdk8s_plus_31 as kplus


class SecureContainerDefaults:
    UID = 10001
    GID = 10001

    @staticmethod
    def container_context() -> kplus.ContainerSecurityContextProps:
        return kplus.ContainerSecurityContextProps(
            ensure_non_root=True,
            user=SecureContainerDefaults.UID,
            group=SecureContainerDefaults.GID,
            read_only_root_filesystem=True,
            allow_privilege_escalation=False,
            privileged=False,
            capabilities=kplus.ContainerSecutiryContextCapabilities(drop=[kplus.Capability.ALL]),
            seccomp_profile=kplus.SeccompProfile(type=kplus.SeccompProfileType.RUNTIME_DEFAULT),
        )

    @staticmethod
    def pod_context() -> kplus.PodSecurityContextProps:
        return kplus.PodSecurityContextProps(
            ensure_non_root=True,
            user=SecureContainerDefaults.UID,
            group=SecureContainerDefaults.GID,
            fs_group=SecureContainerDefaults.GID,
        )
