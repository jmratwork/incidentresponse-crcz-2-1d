import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


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
