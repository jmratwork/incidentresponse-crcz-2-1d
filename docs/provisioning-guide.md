# Provisioning workflow for subcase 1d

This guide explains how to instantiate the CyberRangeCZ infrastructure aligned with the CYNET activity diagram for the NG-SOC automation scenario. The process is divided into two phases: importing the KYPO/CRCZ topology and configuring the virtual machines with Ansible. The instructor-led training assets from subcase 1a are now maintained in the dedicated repository for educational sessions.

## 1. Import the topology in KYPO/CRCZ

1. Sign in to the KYPO portal with an account that can create sandboxes.
2. Upload `provisioning/case-1d/topology.yml` to provision:
   - Core NG-SOC hosts (`ng-soc`, `ng-siem`, `ng-soar`).
   - Supporting services (`cti-ss`, `cicms-operator`, `playbook-library`, `telemetry-simulator`).
   - Segmented networks that emulate the SOC, automation, intelligence, coordination and telemetry zones.
3. Deploy the sandbox and wait for KYPO/CRCZ to report that all machines are reachable.

## 2. Prepare credentials

1. Duplicate `inventory.sample` and rename it to `inventory.ini` (or keep the `.sample` extension).
2. Keep the hostnames and IP addresses defined by the topology file.
3. Export credentials as environment variables before executing Ansible, for example:

```bash
export ANSIBLE_PASSWORD_NG_SOC='********'
export ANSIBLE_PASSWORD_NG_SOAR='********'
```

4. If you prefer to store secrets in Ansible Vault files, replace the `lookup('env', ...)` expressions with `ansible-vault` variables and reference the vault when running the playbooks.

## 3. Install Ansible dependencies

```bash
python3 -m pip install --upgrade ansible
python3 -m pip install pywinrm
ansible-galaxy collection install ansible.windows community.general
```

- Install `pywinrm` to enable Ansible WinRM connectivity. Use `python3 -m pip install "pywinrm[credssp]"` when the sandbox requires CredSSP delegation support.
- Windows connectivity for auxiliary workstations requires WinRM over TLS (port 5986). Configure certificates or use the inventory option `ansible_winrm_server_cert_validation=ignore` for lab environments.

## 4. Execute the playbooks

```bash
ansible-playbook -i inventory.ini provisioning/case-1d/provisioning/playbook.yml
```

This playbook configures the NG ecosystem by installing packages, enabling services and seeding working directories that match the operational flow described in the NG-SOC documentation. Use tags (e.g. `--tags ng_soar`) to target specific components during troubleshooting.

## 5. Validation steps

- Check SSH or WinRM connectivity with `ansible all -i inventory.ini -m ping` (use `ansible.windows.win_ping` for Windows groups).
- Verify that key services are running (`nginx` on the playbook library, `redis-server` on NG-SOAR, `grafana-server` on CICMS Operator).
- Trigger the telemetry simulator script (`/opt/telemetry-simulator/scenarios/generate.sh`) and confirm that NG-SIEM receives events through `rsyslog`.
- Confirm that NG-SOAR updates the incident status in CICMS Operator and that CTI-SS enrichment artifacts are stored in `/opt/cti-ss/share`.

Following these steps ensures the infrastructure mirrors the flow of subcase 1d and is ready for the exercises described in `docs/subcase-1d-playbook-automation.md`.

## 6. Reusing the Docker deployment tasks from `ng-soc-ansible`

The NG-SIEM and NG-SOAR roles import the container deployment snippets maintained in the `ng-soc-ansible` repository (branch `central`). The logic lives locally under `provisioning/roles/ng-siem/tasks/docker-deploy.yml` and `provisioning/roles/ng-soar/tasks/docker-deploy.yml` and mirrors the upstream tasks that install Docker, mount the SMB share, uncompress the compose bundle and run `docker compose`.

To refresh them from upstream when a new release is published:

```bash
git clone --branch central https://github.com/CyberRangeCZ/ng-soc-ansible.git /tmp/ng-soc-ansible
cp /tmp/ng-soc-ansible/roles/ng-siem/tasks/docker-deploy.yml provisioning/roles/ng-siem/tasks/
cp /tmp/ng-soc-ansible/roles/ng-soar/tasks/docker-deploy.yml provisioning/roles/ng-soar/tasks/
```

Both roles expose a `*_compose_source` structure that controls the SMB path (or an alternate source), whether the compose file is compressed, and the destination directory. Set `ng_siem_containerized` or `ng_soar_containerized` to `false` to skip the import entirely when you want to rely on pre-installed services instead of the Dockerised lab images.

## 7. Injecting IP/port variables for external services

NG-SIEM and NG-SOAR consume external services such as MISP, DFIR-IRIS and Cortex. Default endpoints now reside in `provisioning/group_vars/ng_stack.yml` so a single set of IP/port values can be shared across hosts. Override them per environment through `group_vars`, `host_vars` or the CLI, for example:

```bash
ansible-playbook -i inventory.ini provisioning/case-1d/provisioning/playbook.yml \
  --extra-vars "ng_external_services.misp.host=192.168.50.15 ng_external_services.dfir_iris.port=8443"
```

or by setting host-specific values through `host_vars`:

```
# provisioning/host_vars/ng-siem.yml
ng_external_services:
  misp:
    host: 10.0.0.25
    port: 8443

# provisioning/host_vars/ng-soar.yml
ng_external_services:
  dfir_iris:
    host: 10.0.0.30
    port: 443
```

The roles inherit these mappings via `ng_siem_external_services` and `ng_soar_external_services`, keeping playbook templates aligned with the integration endpoints used by the rest of the lab.

## 8. Single-node vs. split-node deployments

You can choose between consolidating NG-SIEM and NG-SOAR on one VM or deploying them separately:

- **Single node:** Point both the `ng_siem` and `ng_soar` inventory groups to the same host. The compose bundles will land under `/opt/ng-siem` and `/opt/ng-soar` on that node, and the shared `ng_external_services` values keep integrations consistent.
- **Split nodes:** Keep distinct hosts under each group as defined in `provisioning/case-1d/topology.yml`. Override IP/port variables per host or per group if the service endpoints differ by zone.

Use tags during provisioning (e.g. `--tags ng_siem` or `--tags ng_soar`) to drive individual deployments regardless of the topology you select.
