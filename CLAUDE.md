# dev_tools

A monorepo of personal projects. Each top-level folder is self-contained, with its own
README, dependencies and Makefile; see that folder's `CLAUDE.md` for its rules.
Run build/test commands from inside the project folder, not the repo root.

## Git

- **Always work on a branch and open a PR.** Never push or commit straight to `main`,
  even when asked to "just push it" — say the PR is the path instead. `main` also has a
  ruleset requiring a pull request, which the owner can bypass, but don't use the bypass.
- `main`'s ruleset also requires **signed commits**.
- Commits are not signed by default on the living-room box — there is no signing key in
  `~/.gitconfig`, so a commit made here will trip the signature rule until one is set up.
- The `gh` credential helper reads the keyring. If a `git push` or `gh` call stalls for
  minutes, the KWallet keyring is locked — that's the cause, not the network.
