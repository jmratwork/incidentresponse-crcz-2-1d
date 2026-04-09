# Provisioning workflow for subcase 1d

This guide explains how to instantiate the CyberRangeCZ infrastructure aligned with the CYNET activity diagram for the NG-SOC automation scenario. The process is divided into two phases: importing the KYPO/CRCZ topology and configuring the virtual machines with Ansible. The instructor-led training assets from subcase 1a are now maintained in the dedicated repository for educational sessions.

## 1. Import the topology in KYPO/CRCZ

1. Sign in to the KYPO portal with an account that can create sandboxes.
2. Upload `provisioning/case-1d/topology.yml` to provision:
   - Core NG-SOC hosts (`ng-soc`, `ng-siem`, `ng-soar`).
   - Supporting services (`cti-ss`, `cicms-operator`, `playbook-library`, `telemetry-feeder`).
   - Segmented networks that emulate the SOC, automation, intelligence, coordination and telemetry zones.
   - Canonical telemetry node naming for subcase 1d is `telemetry-feeder`.
3. Deploy the sandbox and wait for KYPO/CRCZ to report that all machines are reachable.

## 2. Prepare credentials

1. Use `inventory.sample` as the canonical subcase 1d inventory template (copy it to `inventory.ini` if you want a local runtime file).
2. Keep the host groups exactly as defined for subcase 1d: `ng-soc`, `ng-siem`, `ng-soar`, `cti-ss`, `cicms-operator`, `playbook-library`, `telemetry-feeder`.
3. Keep the hostnames and IP addresses defined by the topology file.
4. Export credentials as environment variables before executing Ansible, for example:

```bash
export ANSIBLE_PASSWORD_NG_SOC='********'
export ANSIBLE_PASSWORD_NG_SOAR='********'
```

5. You can alternatively source secrets from Ansible Vault variables instead of environment variables; do not embed credentials in inventory files.

## 3. Install Ansible dependencies

```bash
python3 -m pip install --upgrade ansible
python3 -m pip install pywinrm
ansible-galaxy collection install ansible.windows community.general
ansible-galaxy collection install community.docker
```

- Install `pywinrm` to enable Ansible WinRM connectivity. Use `python3 -m pip install "pywinrm[credssp]"` when the sandbox requires CredSSP delegation support.
- Windows connectivity for auxiliary workstations requires WinRM over TLS (port 5986). Configure certificates or use the inventory option `ansible_winrm_server_cert_validation=ignore` for lab environments.

## 4. Execute the playbooks

```bash
ansible-playbook -i inventory.ini provisioning/case-1d/provisioning/playbook.yml
```

This playbook configures the NG ecosystem by installing packages, enabling services and seeding working directories that match the operational flow described in the NG-SOC documentation. Use tags (e.g. `--tags ng-soar`) to target specific components during troubleshooting.

### External prerequisites required by this repository

- Optional container registry credentials (only when private image pulls are required):
  - `CTI_SS_REGISTRY_USERNAME`
  - `CTI_SS_REGISTRY_PASSWORD`
  - `cicms_registry.username` / `cicms_registry.password` provided from inventory, group vars, or vault.
- Optional TAXII credentials for CTI-SS users:
  - `CTI_SS_TAXII_SIEM_INGESTOR_PASSWORD`
  - `CTI_SS_TAXII_TELEMETRY_FEEDER_PASSWORD`
- A reachable SMB/CIFS share containing DFIR-IRIS artifacts (`dfir-iris-custom.zip`) and any referenced compose bundles.
- Network reachability between `cicms-operator` and `cti-ss` on the configured MISP URL/port (`cicms_iris_misp_url`).
- MISP API key propagation expects `cti-ss` and `cicms-operator` to run in the same playbook execution unless Ansible fact caching is enabled.

## 5. Validation steps

- Check SSH or WinRM connectivity with `ansible all -i inventory.ini -m ping` (use `ansible.windows.win_ping` for Windows groups).
- Verify that key services are running (`nginx` on the playbook library, `redis-server` on NG-SOAR, `grafana-server` on CICMS Operator).
- Trigger the telemetry feeder script (`/opt/telemetry-feeder/scenarios/generate.sh`) and confirm that NG-SIEM receives events through `rsyslog`.
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


## 7. Descomposición selectiva de `docker_server` del upstream en roles locales

Este repositorio **no** incorpora un rol monolítico `docker_server`. En su lugar, toma sólo los fragmentos necesarios de `NG-SOC-eu/ng-soc-ansible` (`provisioning/roles/docker_server/tasks/main.yml`) y los reparte por componente de subcaso 1d.

### Tabla de mapeo

| Componente (`incidentresponse-crcz-2-1d`) | Fragmento relevante de `docker_server` upstream | Dónde vive/configura en este repo |
|---|---|---|
| `cti-ss` | Base Docker (prerrequisitos APT, repo, engine), despliegue MISP (`misp-docker`), generación/publicación de API key | `provisioning/case-1d/provisioning/roles/cti-ss/tasks/main.yml` + `defaults/main.yml` (`cti_ss_misp_*`, `cti_ss_registry`, `cti_ss_fact_delegate_host`). |
| `cicms` (`cicms-operator`) | Base Docker, staging SMB/CIFS de `dfir-iris-custom.zip`, despliegue DFIR-IRIS, inyección `IRIS_MISP_URL`/`IRIS_MISP_VERIFY_CERT`/`IRIS_MISP_KEY` | `provisioning/case-1d/provisioning/roles/cicms/tasks/main.yml` + `defaults/main.yml` (`cicms_compose_source`, `cicms_dfir_*`, `cicms_misp_fact_source`). |
| `ng-soar` | Despliegue containerizado NG-SOAR (Docker + SMB + `docker compose`) | `provisioning/case-1d/provisioning/roles/ng-soar/tasks/main.yml` (import) y `tasks/docker-deploy.yml` (snippet local sincronizable). |
| `ng-siem` | Base Docker/SMB necesaria para despliegue containerizado del stack NG-SIEM (`docker compose`) | `provisioning/case-1d/provisioning/roles/ng-siem/tasks/main.yml` (import) y `tasks/docker-deploy.yml` (snippet local sincronizable). |
| `ng-soc` | Sin correspondencia directa en `docker_server` para este subcaso | Rol propio del laboratorio: `provisioning/case-1d/provisioning/roles/ng-soc`. |
| `playbook-library` | Sin correspondencia directa en `docker_server` para este subcaso | Rol propio del laboratorio: `provisioning/case-1d/provisioning/roles/playbook-library`. |
| `telemetry-feeder` | Sin correspondencia directa en `docker_server` para este subcaso | Rol propio del laboratorio: `provisioning/case-1d/provisioning/roles/telemetry-feeder`. |

### Exclusiones explícitas de alcance

Aunque aparecen en el upstream `docker_server`, en este repositorio (subcaso 1d) quedan fuera de alcance:

- Portainer.
- RITA backend/frontend/tools.

La referencia compartida de endpoints externos para NG-SIEM y NG-SOAR se mantiene en `provisioning/group_vars/ng_stack.yml` mediante `ng_external_services`, heredado por `ng_siem_external_services` y `ng_soar_external_services`.

## 8. Injecting IP/port variables for external services

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

## 9. Single-node vs. split-node deployments

You can choose between consolidating NG-SIEM and NG-SOAR on one VM or deploying them separately:

- **Single node:** Point both the `ng_siem` and `ng_soar` inventory groups to the same host. The compose bundles will land under `/opt/ng-siem` and `/opt/ng-soar` on that node, and the shared `ng_external_services` values keep integrations consistent.
- **Split nodes:** Keep distinct hosts under each group as defined in `provisioning/case-1d/topology.yml`. Override IP/port variables per host or per group if the service endpoints differ by zone.

Use tags during provisioning (e.g. `--tags ng-siem` or `--tags ng-soar`) to drive individual deployments regardless of the topology you select.
