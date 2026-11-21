# Zazzle Video Runner

Public orchestration for the private Zazzle video engine, workflow contract v2.
Each cycle handles one candidate, with account/board rotation in the engine.

## Boundaries

- Engine code and GitHub Actions are pinned to reviewed commits.
- Latest queue state is read independently from the engine main branch.
- Runs are serialized and never cancel a previous publication.
- Installers/tests do not receive Pinterest credentials or a persisted Git token.
- A remote queue reservation is confirmed before one Pin creation attempt.
- Uncertain results require reconciliation instead of automatic republication.

## Rollout

Merge the companion engine PR first **with a merge commit**, then this Runner PR.
Keep ENGINE_CODE_SHA on the tested, reachable commit. The old live entrypoint is
intentionally incompatible with the new protocol.

Scope GH_PAT to the private engine metadata read and Contents read/write. Store
PINTEREST_ACCOUNTS_JSON in this Runner's Actions Secrets; other vaults do not
update it automatically. No secret values belong in source or workflow inputs.

Scheduling is off unless VIDEO_PUBLISH_ENABLED is exactly true. Manual runs
default to dry_run=true. Optional target_board must match a configured board;
it never falls back to another board.

Preview upload is off by default. Choosing upload_preview exposes rendered media
to readers of this public repository for one day. Only MP4/JPG previews are
uploaded, never runtime/state/credential files.

Review a preview before authorizing a live test. After the live Pin and final
queue checkpoint are verified, enable scheduling if desired. This change does
not set that variable or dispatch a live run.

See docs/OPERATIONS.md in the private engine for migration and recovery.
