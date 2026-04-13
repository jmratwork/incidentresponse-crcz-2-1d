#!/usr/bin/env python3
from __future__ import annotations
import os
import shutil
import sys
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOPOLOGY = os.path.join(
    ROOT, os.getenv("TOPOLOGY_FILE", os.path.join("provisioning", "case-1d", "topology.yml"))
)

EXPECTED_HOSTS = {"ng-soc", "ng-siem", "ng-soar", "cti-ss", "cicms-operator", "playbook-library", "telemetry-feeder"}
EXPECTED_NETWORKS = {"soc-operations", "automation-zone", "intelligence-zone", "coordination-zone", "telemetry-zone"}
EXPECTED_MAPPING_HOSTS = EXPECTED_HOSTS.copy()
REQUIRED_TOOLS = ["ansible-playbook", "ansible-galaxy", "python3"]

REQUIRED_ENV = [
    "CTI_SS_TAXII_SIEM_INGESTOR_PASSWORD",
    "CTI_SS_TAXII_TELEMETRY_FEEDER_PASSWORD",
    "NG_SIEM_TAXII_PASSWORD",
    "NG_SOAR_SIEM_INGEST_TOKEN",
    "TELEMETRY_FEEDER_TAXII_PASSWORD",
]
OPTIONAL_ENV = ["CTI_SS_REGISTRY_USERNAME", "CTI_SS_REGISTRY_PASSWORD", "CICMS_DOCKER_PASSWORD"]


def err(msg: str) -> None:
    print(f"[ERROR] {msg}")


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def main() -> int:
    failed = False

    for tool in REQUIRED_TOOLS:
      if shutil.which(tool) is None:
          err(f"Falta dependencia del nodo de control: '{tool}'")
          failed = True
      else:
          ok(f"Dependencia disponible: {tool}")

    if not os.path.exists(TOPOLOGY):
        err(f"No existe topology esperada: {TOPOLOGY}")
        return 1

    with open(TOPOLOGY, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    hosts = {h.get("name") for h in data.get("hosts", [])}
    networks = {n.get("name") for n in data.get("networks", [])}
    mappings = {m.get("host") for m in data.get("net_mappings", [])}

    if hosts != EXPECTED_HOSTS:
        err(
            "Hosts inválidos en topology.yml. "
            f"Esperados={sorted(EXPECTED_HOSTS)} actuales={sorted(hosts)}"
        )
        failed = True
    else:
        ok("Topología contiene todos los hosts esperados")

    if networks != EXPECTED_NETWORKS:
        err(
            "Redes inválidas en topology.yml. "
            f"Esperadas={sorted(EXPECTED_NETWORKS)} actuales={sorted(networks)}"
        )
        failed = True
    else:
        ok("Topología contiene todas las redes esperadas")

    if not EXPECTED_MAPPING_HOSTS.issubset(mappings):
        err(f"net_mappings incompleto: faltan {sorted(EXPECTED_MAPPING_HOSTS - mappings)}")
        failed = True
    else:
        ok("net_mappings contiene todos los hosts del subcaso 1d")

    for name in REQUIRED_ENV:
        value = os.getenv(name, "").strip()
        if not value:
            err(f"Falta secreto obligatorio: {name}")
            failed = True
        elif value.lower() == "changeme":
            err(f"Secreto inválido en {name}: valor 'changeme' no permitido")
            failed = True
        else:
            ok(f"Secreto obligatorio presente: {name}")

    for name in OPTIONAL_ENV:
        if os.getenv(name, "").strip():
            ok(f"Secreto opcional presente: {name}")

    if failed:
        print("\nPreflight FALLÓ. Corrige los errores y reintenta.")
        return 1
    print("\nPreflight OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
