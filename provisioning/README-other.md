# Provisioning artefacts for CyberRangeCZ

The `provisioning/` directory contains topology definitions and Ansible playbooks that reproduce the infrastructure flow of subcase 1d from the CYNET activity diagram.

## Topology files

- `subcase-1d-topology.yml` – KYPO/CRCZ topology for the NG-SOC, NG-SIEM, NG-SOAR, CTI-SS, CICMS Operator, playbook library and telemetry simulator services.

This file can be imported into KYPO to instantiate the virtual machines, routers and networks ahead of running the configuration playbooks.

## Playbooks

- `subcase-1d/` – Roles and site playbook to configure NG-SOC automation components, intelligence services and the telemetry generator.

Each subdirectory includes a README with prerequisites, variable references and execution instructions. Install the required Ansible collections before running the playbooks and store credentials using Ansible Vault or environment variables instead of plain text files. The instructor-led training artefacts for subcase 1a are published in the repository dedicated to educational exercises.
