# Artifact staging convention

This repository does **not** ship private or heavyweight deployment artifacts. Use this folder as a local staging area.

## Resolution policy (NG-SIEM / NG-SOAR)

Priority order is consistent across roles:

1. Local file (`*_compose_local_path`)
2. URL download (`*_compose_url`)
3. SMB/CIFS (`*_compose_source.share` + path)

## Expected external artifacts

- NG-SIEM compose bundle/file (`docker-compose.yml` or `.zip`)
- NG-SOAR compose bundle/file (`docker-compose.yml` or `.zip`)
- CICMS DFIR-IRIS archive (`dfir-iris-custom.zip`)

Keep credentials for SMB or private registries outside git (env vars or Ansible Vault).
