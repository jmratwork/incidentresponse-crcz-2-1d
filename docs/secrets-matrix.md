# Matriz de secretos por rol

| Rol | Variable | Finalidad | Inyección soportada | Obligatoria |
|---|---|---|---|---|
| cti-ss | `cti_ss_taxii_siem_ingestor_password` | Usuario TAXII para NG-SIEM | Vault, `lookup('env', 'CTI_SS_TAXII_SIEM_INGESTOR_PASSWORD')` | Sí |
| cti-ss | `cti_ss_taxii_telemetry_feeder_password` | Usuario TAXII para telemetry-feeder | Vault, `lookup('env', 'CTI_SS_TAXII_TELEMETRY_FEEDER_PASSWORD')` | Sí |
| cti-ss | `cti_ss_registry_username` | Pull privado de imágenes | Vault/env | No |
| cti-ss | `cti_ss_registry_password` | Password/token registry | Vault/env | Condicional |
| ng-siem | `ng_siem_pipeline.sources[cti_taxii].password` | Ingesta TAXII | Vault/env (`NG_SIEM_TAXII_PASSWORD`) | Sí |
| ng-soar | `ng_soar_integrations[siem_ingest].token` | Integración SOAR↔SIEM | Vault/env (`NG_SOAR_SIEM_INGEST_TOKEN`) | Sí |
| telemetry-feeder | `telemetry_feeder_agent.outputs[taxii].password` | Publicación TAXII | Vault/env (`TELEMETRY_FEEDER_TAXII_PASSWORD`) | Sí |
| cicms | `cicms_registry.password` | Pull privado DFIR-IRIS (si aplica) | Vault/env (`CICMS_DOCKER_PASSWORD`) | Condicional |
