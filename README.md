# incidentresponse-crcz

This repository gathers only the materials required to run the practical exercises of the **CyberRangeCZ** initiative. It does not include generic infrastructure or dependencies from the KYPO/CRCZ laboratory; every asset focuses on the NG-SOC automation workflow validated for CYNET subcase 1d of the architecture diagram.

## Scope of the exercises

- **Subcase 1d – NG-SOC operation**: documents how the NG-SOC/NG-SIEM and NG-SOAR components coordinate the automated response with support from the CICMS Operator, CTI-SS and the playbook/standards library (NVD/NIST, MITRE ATT&CK).

The detailed flow is summarised below to facilitate reproduction during the practical sessions.

See Figure 6 for the segment of the CYNET activity diagram relevant to this subcase.

![Figure 6: CYNET Activity Diagram](docs/figures/cynet-activity.png)

*Figure 6. Activity diagram illustrating the automated NG-SOC response for subcase 1d.*

## Subcase 1d flow

1. **Detection in NG-SOC/NG-SIEM**
   - NG-SIEM receives events from CyberRangeCZ telemetry sources and raises prioritised alerts.
   - The NG-SOC analyst validates the alert and selects the relevant CACAO playbook.
2. **CACAO playbook orchestration**
   - The NG-SOC orchestrator invokes NG-SOAR to run the chosen playbook.
   - NG-SOAR coordinates automated tasks (enrichment, containment and notification) following the CACAO sequence.
3. **Support from transversal systems**
   - **CICMS Operator** centralises incident documentation and channels post-incident reports.
   - **CTI-SS** provides threat intelligence and additional context for decision-making.
   - **Playbook and standards library (NVD/NIST, MITRE ATT&CK)** guides the selection of response and recovery actions.
4. **Closure and feedback**
   - NG-SOAR consolidates the outcomes and returns the final status to NG-SOC/NG-SIEM.
   - CICMS Operator produces the post-incident report and references lessons learnt in the playbook library.

## Key files

- `training_linear.json`: lists the learning modules that support the NG-SOC automation scenario in subcase 1d, including step-by-step activities and the tools involved.
- `topology.yml`: KYPO-compatible topology for the NG-SOC exercise sandbox, matching the provisioning descriptors.
- `docs/`: support materials and complementary guides. `docs/deployment-prerequisites.md`, `docs/artifacts.md` and `docs/provisioning-guide.md` document platform prerequisites, external artifacts and reproducible deployment steps for subcase 1d.
- `inventory.sample`: canonical subcase 1d inventory template with the host groups `ng-soc`, `ng-siem`, `ng-soar`, `cti-ss`, `cicms-operator`, `playbook-library` and `telemetry-feeder`. Provide secrets at runtime via environment variables or Ansible Vault (do not commit credentials).
- `provisioning/`: KYPO/CRCZ topology files and Ansible playbooks that replicate the infrastructure defined in the CYNET activity diagram for the 1d flow.
- Docker-based services in subcase 1d are implemented with a **selective decomposition** of upstream `ng-soc-ansible` `docker_server` tasks into local roles (`cti-ss`, `cicms`, `ng-siem`, `ng-soar`), not by importing a monolithic `docker_server` role.

## Validating the repository

Basic structural checks are provided to confirm that the learning sequence and topology descriptors stay consistent. Install the development dependencies and run the automated validation suite with:

```bash
pip install -r requirements-dev.txt
pytest
```

The tests verify that:

- `training_linear.json` follows the expected layout, with sequential steps and non-empty metadata for each activity.
- `topology.yml` and the provisioning topologies only include KYPO sandbox fields and consistent host/network mappings.
- The KYPO topologies in `provisioning/` reference valid hosts, routers and networks in their mapping sections.
- `inventory.sample` is automatically checked against `topology.yml` for required host groups, host names and `ansible_host` IPs to prevent inventory/topology drift.
- `topology.yml` is automatically checked against `provisioning/case-1d/topology.yml` so host/IP mappings stay coherent across both topology descriptors.
- The Jinja role templates under `provisioning/roles` and `provisioning/case-1d/provisioning/roles` render correctly, including quoting edge cases in TAXII configuration fields.

## Credential management

Before executing Ansible playbooks, **secret injection is mandatory**: keep credentials outside the repository and provide them only through Ansible Vault values or environment-variable lookups referenced from `inventory.sample`.

The affected roles fail fast with `ansible.builtin.assert` if sensitive values are empty or set to `changeme`:

- `cti_ss_taxii_siem_ingestor_password`
- `cti_ss_taxii_telemetry_feeder_password`
- `cti_ss_registry_username` (optional, only for private registry login)
- `cti_ss_registry_password` (required when `cti_ss_registry_username` is set)
- `ng_siem_pipeline.sources[cti_taxii].password`
- `ng_soar_integrations[siem_ingest].token`
- `telemetry_feeder_agent.outputs[taxii].password`
- `cicms_registry.password` (when `cicms_registry.username` is defined)

Set them from Vault or environment lookups before execution (for example `lookup('env', 'CTI_SS_TAXII_SIEM_INGESTOR_PASSWORD')`, `lookup('env', 'CTI_SS_TAXII_TELEMETRY_FEEDER_PASSWORD')`, `lookup('env', 'CTI_SS_REGISTRY_USERNAME')`, `lookup('env', 'CTI_SS_REGISTRY_PASSWORD')`, `lookup('env', 'NG_SIEM_TAXII_PASSWORD')`, `lookup('env', 'NG_SOAR_SIEM_INGEST_TOKEN')`, `lookup('env', 'TELEMETRY_FEEDER_TAXII_PASSWORD')`, `lookup('env', 'CICMS_DOCKER_PASSWORD')`).


Temporal backward compatibility is enabled in CTI-SS defaults: legacy variables `cti_ss_taxii_siem_password`, `cti_ss_taxii_telemetry_password`, and `cti_ss_docker_password` are still accepted as aliases, but they are **deprecated** and should be replaced by the canonical names above.

For subcase 1d provisioning, keep these external runtime dependencies available:
- Docker Hub credential variables (`CTI_SS_REGISTRY_USERNAME`, `CTI_SS_REGISTRY_PASSWORD`, `CICMS_DOCKER_PASSWORD`).
- SMB/CIFS share content required by containerized roles (for example `dfir-iris-custom.zip`).
- `community.docker` Ansible collection installed on the control node.

## Licence

The content is provided strictly for educational purposes.


## Reproducible control-node setup and preflight

```bash
./scripts/bootstrap-control-node.sh
source .venv/bin/activate
./scripts/preflight.sh
```

Use `inventory.example.ini`, `.env.example` and `vault.example.yml` as secure templates.
