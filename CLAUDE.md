# dev_tools

A monorepo of personal projects. Each top-level folder is self-contained, with its own
README, dependencies and Makefile; see that folder's `CLAUDE.md` for its rules.
Run build/test commands from inside the project folder, not the repo root.

## Git

- **Always work on a branch and open a PR.** Never push or commit straight to `main`,
  even when asked to "just push it" — say the PR is the path instead. `main` also has a
  ruleset requiring a pull request, which the owner can bypass, but don't use the bypass.
- `main`'s ruleset also requires **signed commits**.
- PRs merge as a **squash commit whose message is the PR title and body** (squash is the
  only method enabled). So the PR description is the permanent commit message — write it
  as one, and keep review chatter in comments rather than the body.
- Signing is set up on the living-room box: `gpg.format=ssh` with `commit.gpgsign=true`
  and `user.signingkey=~/.ssh/id_ed25519.pub`, registered on GitHub as the signing key
  `hactl-livingroom`. Commits made here satisfy the signature rule as-is — don't disable
  signing to work around a failure, fix the key instead.
- The `gh` credential helper reads the keyring. If a `git push` or `gh` call stalls for
  minutes, the KWallet keyring is locked — that's the cause, not the network.
