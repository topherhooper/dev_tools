# Home Assistant project notes

- `config/` mirrors HA's `/config`. Put new hand-written features in `config/packages/<feature>.yaml`.
  Leave `automations.yaml`, `scripts.yaml` and `scenes.yaml` as plain lists or maps, because the HA UI rewrites them.
- Use current HA syntax: `triggers:`/`trigger:`, `conditions:`, `actions:`/`action:` (not `platform:`/`service:`).
  Give every automation a stable `id`.
- Thresholds and other shared Jinja belong in `config/custom_templates/*.jinja`, imported by a
  package — never copied into both an automation and a dashboard card. HA caches these, so
  after editing one call `homeassistant.reload_custom_templates`, not just a YAML reload.
- Every `!secret` you reference must also be added to `config/secrets.example.yaml` with a placeholder,
  or the CI config check fails. Never commit `secrets.yaml`, `.env`, or anything from `.storage/`.
- Before pushing, run `make lint test` from this folder, plus `make check-config` for HA's own
  validation. That target runs the official HA image with podman by default
  (`CONTAINER=docker` to override); CI runs the same check with docker.
- `make install` builds `.venv/` here; run the CLI as `.venv/bin/hactl`. `.env` and
  `config/secrets.yaml` are local, git-ignored copies of the `.example` files.
- Don't run `hactl deploy`, `reload`, or `call` (they change the live house) unless the user asks.
