# ng-siem role

This role installs Docker requirements and deploys the NG-SIEM stack from a compose bundle obtained from an SMB share or a configured fallback source.

## Variables

- `ng_siem_compose_source`: Controls where the compose bundle is retrieved from. When `archive` is `false`, the role expects `compose_path` to exist on the SMB share mounted at `mount_point`.
- `ng_siem_compose_fallback`: Optional fallback used when `ng_siem_compose_source.archive` is `false` and the compose file is missing on the SMB share.
  - `enabled`: Set to `true` to allow the fallback to be used.
  - `type`: `file` to copy a compose file available on the controller (for example, one bundled with the repository) or `url` to download it via HTTP/S.
  - `path`: Source path for `type: file`.
  - `url`: Download URL for `type: url`.
  - `mode`: File permissions applied to the downloaded or copied compose file.

If the compose file cannot be found on the SMB share and no fallback is enabled, the role fails with guidance on how to provide the file.
