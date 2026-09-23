# Home Assistant project notes

- `config/` mirrors HA's `/config`. Put new hand-written features in `config/packages/<feature>.yaml`.
  Leave `automations.yaml`, `scripts.yaml` and `scenes.yaml` as plain lists or maps, because the HA UI rewrites them.
- Use current HA syntax: `triggers:`/`trigger:`, `conditions:`, `actions:`/`action:` (not `platform:`/`service:`).
  Give every automation a stable `id`.
- Every `!secret` you reference must also be added to `config/secrets.example.yaml` with a placeholder,
  or the CI config check fails. Never commit `secrets.yaml`, `.env`, or anything from `.storage/`.
- Before pushing, run `make lint test` from this folder. CI also runs HA's `check_config` in Docker.
- Don't run `hactl deploy`, `reload`, or `call` (they change the live house) unless the user asks.
