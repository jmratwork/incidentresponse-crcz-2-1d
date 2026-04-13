# Artefactos externos y política de fallback

Este laboratorio no versiona bundles privados ni binarios pesados.

## Convención
- Carpeta local sugerida: `artifacts/`.
- Variables por rol para resolución de compose/bundles.
- Prioridad común: **local > URL > SMB/CIFS**.

## Matriz rápida
| Rol | Artefacto esperado | Ubicación soportada | Fallback |
|---|---|---|---|
| `ng-siem` | `docker-compose.yml` o zip | `artifacts/ng-siem`, URL, share SMB | Sí |
| `ng-soar` | `docker-compose.yml` o zip | `artifacts/ng-soar`, URL, share SMB | Sí |
| `cicms` | `dfir-iris-custom.zip` | share SMB (o ruta equivalente parametrizada) | Parcial |
| `cti-ss` | repositorio MISP + opcional SMB | git + share SMB | N/A |

## Credenciales opcionales de registry
Nunca se guardan en git. Inyectar por Vault/env:
- `CTI_SS_REGISTRY_USERNAME`
- `CTI_SS_REGISTRY_PASSWORD`
- `CICMS_DOCKER_PASSWORD`
