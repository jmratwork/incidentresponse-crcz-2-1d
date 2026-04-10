import json
import subprocess
import importlib.util
import re
import sys
from pathlib import Path

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
        REPO_ROOT / "provisioning" / "case-1d" / "topology.yml",
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
