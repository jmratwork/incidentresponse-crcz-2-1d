# Guía de aprovisionamiento reproducible (subcaso 1d)

## 1) Preparar nodo de control
```bash
./scripts/bootstrap-control-node.sh
source .venv/bin/activate
```

## 2) Preparar inventario y secretos
1. Copia `inventory.example.ini` a `inventory.ini`.
2. Copia `.env.example` a `.env` (solo local).
3. Si usas Vault, parte de `vault.example.yml`.

## 3) Importar topología en KYPO/CRCZ (manual)
1. En el portal KYPO/CRCZ, importa `provisioning/case-1d/topology.yml`.
2. Crea sandbox y espera estado operativo.
3. Verifica acceso a VMs (SSH/WinRM).

> Límite explícito: este repositorio no automatiza el portal KYPO.

## 4) Preflight
```bash
./scripts/preflight.sh
```
Valida:
- dependencias del nodo de control,
- estructura de topología subcaso 1d,
- secretos obligatorios,
- sintaxis del playbook de preflight.

## 5) Ejecutar preflight remoto (opcional recomendado)
```bash
ansible-playbook -i inventory.ini provisioning/case-1d/provisioning/preflight.yml
```

## 6) Desplegar
```bash
ansible-playbook -i inventory.ini provisioning/case-1d/provisioning/playbook.yml
```

## 7) Verificación post-despliegue
- `cti-ss` ↔ `cicms-operator` (MISP API key / endpoint)
- `telemetry-feeder` ↔ `ng-siem` (ingesta)
- `ng-soar` ↔ `cti-ss` y `ng-soar` ↔ `cicms`

## Modos de instalación por rol
Valores permitidos: `preinstalled|package|container|artifact`

| Rol | Variable | Modo por defecto |
|---|---|---|
| ng-soc | `ng_soc_install_mode` | `preinstalled` |
| ng-siem | `ng_siem_install_mode` | `container` |
| ng-soar | `ng_soar_install_mode` | `container` |
| cti-ss | `cti_ss_install_mode` | `container` |
| cicms | `cicms_install_mode` | `artifact` |
| playbook-library | `playbook_library_install_mode` | `preinstalled` |
| telemetry-feeder | `telemetry_feeder_install_mode` | `preinstalled` |

## Trazabilidad con upstream NG-SOC
Referencia funcional: `NG-SOC-eu/ng-soc-ansible` rol `docker_server`.

Adaptado en este repo:
- instalación Docker y prerequisitos,
- staging de artefactos SMB,
- despliegue compose para NG-SIEM/NG-SOAR,
- flujo MISP/API key para CTI-SS/CICMS.

Descartado o fuera de alcance del subcaso:
- componentes no usados en 1d (por ejemplo Portainer/RITA),
- credenciales/IPs hardcodeadas del upstream.
