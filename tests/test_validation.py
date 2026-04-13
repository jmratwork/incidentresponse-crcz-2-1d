import json
import subprocess
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ROLES_SYNC_SCRIPT = REPO_ROOT / "provisioning" / "scripts" / "check_roles_sync.py"

_spec = importlib.util.spec_from_file_location("check_roles_sync", ROLES_SYNC_SCRIPT)
_check_roles_sync = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules[_spec.name] = _check_roles_sync
_spec.loader.exec_module(_check_roles_sync)
_load_allowlist = _check_roles_sync._load_allowlist


@pytest.fixture(scope="module")
def training_data():
    training_file = REPO_ROOT / "training_linear.json"
    with training_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_training_linear_structure(training_data):
    assert isinstance(training_data, dict)
    for key in ("name", "description", "modules"):
        assert key in training_data, f"Missing key '{key}' in training file"

    modules = training_data["modules"]
    assert isinstance(modules, list) and modules, "Modules list must not be empty"

    for module in modules:
        assert set(module.keys()) >= {"id", "title", "phases"}
        assert module["id"]
        assert module["title"].strip()
        phases = module["phases"]
        assert isinstance(phases, list) and phases

        steps = []
        for phase in phases:
            assert set(phase.keys()) >= {"name", "activities"}
            assert phase["name"].strip()
            activities = phase["activities"]
            assert isinstance(activities, list) and activities
            for activity in activities:
                assert set(activity.keys()) >= {"step", "description", "tools"}
                steps.append(activity["step"])
                assert isinstance(activity["step"], int)
                assert activity["description"].strip()
                tools = activity["tools"]
                assert isinstance(tools, list) and tools
                for tool in tools:
                    assert isinstance(tool, str) and tool.strip()

        sorted_steps = sorted(steps)
        expected_steps = list(range(1, len(sorted_steps) + 1))
        assert sorted_steps == expected_steps, (
            f"Module {module['id']} steps should be sequential starting at 1"
        )


@pytest.mark.parametrize(
    "topology_path",
    [
        REPO_ROOT / "topology.yml",
        REPO_ROOT / "topology.full.yml",
        REPO_ROOT / "provisioning" / "case-1d" / "topology.yml",
        REPO_ROOT / "provisioning" / "case-1d" / "topology.full.yml",
    ],
)
def test_kypo_topologies(topology_path):
    with topology_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    required_keys = {
        "name",
        "hosts",
        "routers",
        "networks",
        "net_mappings",
        "router_mappings",
        "groups",
    }
    assert set(data.keys()) == required_keys, (
        f"{topology_path.name} must only contain KYPO keys: {sorted(required_keys)}"
    )

    assert isinstance(data["hosts"], list) and data["hosts"], (
        f"{topology_path.name} must list at least one host"
    )
    assert isinstance(data["routers"], list) and data["routers"], (
        f"{topology_path.name} must list at least one router"
    )
    assert isinstance(data["networks"], list) and data["networks"], (
        f"{topology_path.name} must list at least one network"
    )
    assert isinstance(data["net_mappings"], list) and data["net_mappings"], (
        f"{topology_path.name} must include host network mappings"
    )
    assert isinstance(data["router_mappings"], list) and data["router_mappings"], (
        f"{topology_path.name} must include router network mappings"
    )
    assert isinstance(data["groups"], list), f"{topology_path.name} groups must be a list"

    hosts = {host["name"] for host in data["hosts"]}
    routers = {router["name"] for router in data["routers"]}
    networks = {net["name"] for net in data["networks"]}

    assert len(hosts) == len(data["hosts"]), "Duplicate host names detected"
    assert len(routers) == len(data["routers"]), "Duplicate router names detected"
    assert len(networks) == len(data["networks"]), "Duplicate network names detected"

    for mapping in data["net_mappings"]:
        assert mapping["host"] in hosts, (
            f"Mapping references unknown host '{mapping['host']}' in {topology_path.name}"
        )
        assert mapping["network"] in networks, (
            f"Mapping references unknown network '{mapping['network']}' in {topology_path.name}"
        )

    for mapping in data["router_mappings"]:
        assert mapping["router"] in routers, (
            f"Router mapping references unknown router '{mapping['router']}' in {topology_path.name}"
        )
        assert mapping["network"] in networks, (
            f"Router mapping references unknown network '{mapping['network']}' in {topology_path.name}"
        )


def test_roles_sync_policy_check():
    result = subprocess.run(
        [sys.executable, str(ROLES_SYNC_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "check_roles_sync.py exited with a non-zero status.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_roles_sync_allowlist_requires_reason(tmp_path):
    allowlist = tmp_path / "allowlist.yml"
    allowlist.write_text(
        "allowed_drift:\n"
        "  - path: ng-siem/tasks/main.yml\n"
        "    kinds: [content]\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="reason"):
        _load_allowlist(allowlist)


def test_roles_sync_allowlist_rejects_unknown_kind(tmp_path):
    allowlist = tmp_path / "allowlist.yml"
    allowlist.write_text(
        "allowed_drift:\n"
        "  - path: ng-siem/tasks/main.yml\n"
        "    kinds: [renamed]\n"
        "    reason: test\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported kind"):
        _load_allowlist(allowlist)


CTI_SS_ACTIVE_ROLE_FILES = [
    REPO_ROOT / "provisioning" / "roles" / "cti-ss" / "defaults" / "main.yml",
    REPO_ROOT / "provisioning" / "roles" / "cti-ss" / "tasks" / "main.yml",
    REPO_ROOT / "provisioning" / "case-1d" / "provisioning" / "roles" / "cti-ss" / "defaults" / "main.yml",
    REPO_ROOT / "provisioning" / "case-1d" / "provisioning" / "roles" / "cti-ss" / "tasks" / "main.yml",
]

CTI_SS_DOC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "provisioning-guide.md",
    REPO_ROOT / "inventory.sample",
]


REQUIRED_INVENTORY_GROUPS = {
    "ng-soc",
    "ng-siem",
    "ng-soar",
    "cti-ss",
    "cicms-operator",
    "playbook-library",
    "telemetry-feeder",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _host_ips_from_topology(path: Path) -> dict[str, str]:
    data = _load_yaml(path)
    ips: dict[str, str] = {}
    for mapping in data.get("net_mappings", []):
        host = mapping.get("host")
        ip = mapping.get("ip")
        if host in ips:
            raise AssertionError(
                f"{path} has duplicate net_mappings for host '{host}' "
                f"(IPs: '{ips[host]}' and '{ip}')"
            )
        ips[host] = ip
    return ips


def _host_flavors_from_topology(path: Path) -> dict[str, str]:
    data = _load_yaml(path)
    return {host["name"]: host["flavor"] for host in data.get("hosts", [])}


def _parse_inventory_ini(path: Path) -> tuple[set[str], dict[str, str]]:
    groups: set[str] = set()
    host_ips: dict[str, str] = {}
    current_group: str | None = None

    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_group = line[1:-1].strip()
            groups.add(current_group)
            continue
        if current_group is None:
            continue

        tokens = line.split()
        hostname = tokens[0]
        ansible_host = None
        for token in tokens[1:]:
            if token.startswith("ansible_host="):
                ansible_host = token.split("=", 1)[1]
                break

        assert ansible_host, (
            f"{path.name}:{lineno} missing ansible_host for host '{hostname}' "
            f"in group '{current_group}'"
        )
        if hostname in host_ips:
            raise AssertionError(
                f"{path.name}:{lineno} duplicate host '{hostname}' "
                f"(previous IP '{host_ips[hostname]}', new IP '{ansible_host}')"
            )
        host_ips[hostname] = ansible_host

    return groups, host_ips


def _extract_cti_ss_variables(path: Path) -> set[str]:
    content = path.read_text(encoding="utf-8")
    return set(re.findall(r"\bcti_ss_[a-z0-9_]*(?:password|username)\b", content))


def test_cti_ss_secret_names_are_consumed_by_active_roles():
    consumed_by_roles = set()
    for file_path in CTI_SS_ACTIVE_ROLE_FILES:
        consumed_by_roles |= _extract_cti_ss_variables(file_path)

    referenced_in_docs = set()
    for file_path in CTI_SS_DOC_FILES:
        referenced_in_docs |= _extract_cti_ss_variables(file_path)

    undocumented_or_unknown = sorted(referenced_in_docs - consumed_by_roles)
    assert not undocumented_or_unknown, (
        "CTI-SS docs/inventory reference variables not consumed by active roles: "
        f"{undocumented_or_unknown}"
    )


def test_inventory_sample_matches_topology_net_mappings():
    inventory_path = REPO_ROOT / "inventory.sample"
    topology_path = REPO_ROOT / "topology.yml"
    groups, inventory_host_ips = _parse_inventory_ini(inventory_path)
    topology_host_ips = _host_ips_from_topology(topology_path)

    missing_groups = sorted(REQUIRED_INVENTORY_GROUPS - groups)
    assert not missing_groups, (
        f"{inventory_path.name} missing required groups: {missing_groups}"
    )

    extra_inventory_hosts = sorted(set(inventory_host_ips) - set(topology_host_ips))
    missing_inventory_hosts = sorted(set(topology_host_ips) - set(inventory_host_ips))
    assert not extra_inventory_hosts, (
        f"{inventory_path.name} contains hosts not present in {topology_path.name}: "
        f"{extra_inventory_hosts}"
    )
    assert not missing_inventory_hosts, (
        f"{inventory_path.name} is missing hosts present in {topology_path.name}: "
        f"{missing_inventory_hosts}"
    )

    mismatched_ips = []
    for host, topology_ip in sorted(topology_host_ips.items()):
        inventory_ip = inventory_host_ips.get(host)
        if inventory_ip != topology_ip:
            mismatched_ips.append(
                f"host '{host}': inventory ansible_host='{inventory_ip}' "
                f"!= topology net_mappings ip='{topology_ip}'"
            )
    assert not mismatched_ips, (
        f"IP drift between {inventory_path.name} and {topology_path.name}: "
        f"{'; '.join(mismatched_ips)}"
    )


def test_topology_yml_matches_case_1d_topology():
    primary_path = REPO_ROOT / "topology.yml"
    case_path = REPO_ROOT / "provisioning" / "case-1d" / "topology.yml"
    primary_host_ips = _host_ips_from_topology(primary_path)
    case_host_ips = _host_ips_from_topology(case_path)

    missing_in_case = sorted(set(primary_host_ips) - set(case_host_ips))
    missing_in_primary = sorted(set(case_host_ips) - set(primary_host_ips))
    assert not missing_in_case, (
        f"{case_path} missing hosts present in {primary_path}: {missing_in_case}"
    )
    assert not missing_in_primary, (
        f"{primary_path} missing hosts present in {case_path}: {missing_in_primary}"
    )

    mismatched_ips = []
    for host, primary_ip in sorted(primary_host_ips.items()):
        case_ip = case_host_ips.get(host)
        if case_ip != primary_ip:
            mismatched_ips.append(
                f"host '{host}': {primary_path.name} ip='{primary_ip}' "
                f"!= {case_path.name} ip='{case_ip}'"
            )
    assert not mismatched_ips, (
        f"Topology IP drift detected between {primary_path} and {case_path}: "
        f"{'; '.join(mismatched_ips)}"
    )


def test_full_profile_matches_low_footprint_host_and_ip_layout():
    low_path = REPO_ROOT / "topology.yml"
    full_path = REPO_ROOT / "topology.full.yml"
    low_case_path = REPO_ROOT / "provisioning" / "case-1d" / "topology.yml"
    full_case_path = REPO_ROOT / "provisioning" / "case-1d" / "topology.full.yml"

    assert _host_ips_from_topology(low_path) == _host_ips_from_topology(full_path)
    assert _host_ips_from_topology(low_case_path) == _host_ips_from_topology(full_case_path)

    low_flavors = _host_flavors_from_topology(low_path)
    full_flavors = _host_flavors_from_topology(full_path)
    assert set(low_flavors.values()) == {"standard.tiny"}
    assert low_flavors["ng-soc"] == "standard.tiny"
    assert full_flavors["ng-soc"] == "standard.medium"
