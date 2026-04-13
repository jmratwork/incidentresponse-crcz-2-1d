# Deployment prerequisites (KYPO/CRCZ + control node)

## What this repo automates
- Ansible configuration for subcase 1d roles.
- Docker/compose-based deployments for NG-SIEM, NG-SOAR, CTI-SS (MISP), CICMS (DFIR-IRIS), when configured.
- Template rendering, secret assertions, and integration checks.

## What KYPO/CRCZ must provide
- Valid account with sandbox creation/import permissions.
- Ability to import at least one topology profile:
  - `provisioning/case-1d/topology.yml` (low-footprint `standard.tiny`, recomendado para pools con cuota reducida),
  - or `provisioning/case-1d/topology.full.yml` (full profile).
- Reachable VMs for all hosts in subcase 1d.

## Manual operator actions (cannot be automated from this repo)
1. Login to KYPO portal.
2. Create/import topology file.
3. Start sandbox and wait until all VMs are in ready/running state.
4. Verify console/SSH availability for each host.

## KYPO topology import verification
After import, validate these entities:
- Hosts: `ng-soc`, `ng-siem`, `ng-soar`, `cti-ss`, `cicms-operator`, `playbook-library`, `telemetry-feeder`
- Networks: `soc-operations`, `automation-zone`, `intelligence-zone`, `coordination-zone`, `telemetry-zone`
- Router mappings through `ng-ops-gateway`

Then run local preflight:

```bash
./scripts/preflight.sh
```

If using the full profile, run preflight against that topology:

```bash
TOPOLOGY_FILE=provisioning/case-1d/topology.full.yml ./scripts/preflight.sh
```

If portal automation is unavailable in your deployment, treat topology import and sandbox start as a strict manual prerequisite.
