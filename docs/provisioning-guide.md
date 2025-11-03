# Provisioning workflow for subcase 1d

This guide explains how to instantiate the CyberRangeCZ infrastructure aligned with the CYNET activity diagram for the NG-SOC automation scenario. The process is divided into two phases: importing the KYPO/CRCZ topology and configuring the virtual machines with Ansible. The instructor-led training assets from subcase 1a are now maintained in the dedicated repository for educational sessions.

## 1. Import the topology in KYPO/CRCZ

1. Sign in to the KYPO portal with an account that can create sandboxes.
2. Upload `provisioning/subcase-1d-topology.yml` to provision:
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
ansible-playbook -i inventory.ini provisioning/subcase-1d/site.yml
```

This playbook configures the NG ecosystem by installing packages, enabling services and seeding working directories that match the operational flow described in the NG-SOC documentation. Use tags (e.g. `--tags ng_soar`) to target specific components during troubleshooting.

## 5. Validation steps

- Check SSH or WinRM connectivity with `ansible all -i inventory.ini -m ping` (use `ansible.windows.win_ping` for Windows groups).
- Verify that key services are running (`nginx` on the playbook library, `redis-server` on NG-SOAR, `grafana-server` on CICMS Operator).
- Trigger the telemetry simulator script (`/opt/telemetry-simulator/scenarios/generate.sh`) and confirm that NG-SIEM receives events through `rsyslog`.
- Confirm that NG-SOAR updates the incident status in CICMS Operator and that CTI-SS enrichment artifacts are stored in `/opt/cti-ss/share`.

Following these steps ensures the infrastructure mirrors the flow of subcase 1d and is ready for the exercises described in `docs/subcase-1d-playbook-automation.md`.
