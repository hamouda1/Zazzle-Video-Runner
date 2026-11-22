# Zazzle Creative Video Runner

Stages the reviewed private creative engine on Ubuntu/Python 3.12. The exact engine commit and workflow expectations live in `workflow-contract.json`.

## Proposed runtime

- Collector and publisher use the existing prepare/checkpoint/single-Pin/result-checkpoint protocol.
- Creative engine 4.2.0 is installed with Linux wheel hashes in a separate virtual environment.
- The renderer receives local image/metadata files, never Pinterest or GitHub credentials.
- Live preparation verifies account identity and uses the current Pinterest display name.
- Six distinct photographs and a seventh closing scene are required. A failed creative render never falls back to the old renderer silently.
- Unknown/uncertain Pin outcomes remain blocked for reconciliation.

Manual runs default to `dry_run=true`. Public preview upload defaults to false; selecting it exposes MP4/JPG files to this public repository's readers for one day. No runtime, queue or credential files are uploaded.

The proposed schedule requires both `VIDEO_PUBLISH_ENABLED=true` and `CREATIVE_IMAGE_RIGHTS_CONFIRMED=true`. A manual non-preview run is rejected before checkout/state access unless both opt-ins are present. This change does not set either variable or dispatch a publishing run.

## Validation

The PR workflow checks the engine pin, preview defaults, credential scoping and durable checkpoint ordering. For an owner-authored same-repository PR, it checks out the exact private engine commit with the existing GH_PAT secret, installs the separate environments, and executes the real dry-run pipeline against an isolated fixture queue. It does not upload artifacts from that private-engine check to this public repository.

A separate availability probe retrieves the real Zazzle page/images and attempts a dry-run render in a temporary queue. It cannot construct a Pinterest uploader, changes no live queue, and reports availability separately from the offline fixture result. An unavailable gallery is a deployment limitation, not proof that rendering or Pin publication succeeded.

## Coordinated rollout

The current production workflow is unchanged until this proposed change is merged. It still follows private engine main through the legacy entrypoint. Merging replacement engine entrypoints alone can therefore break the current Runner.

1. Review the private engine Linux checks and this Runner's contract/private-checkout checks.
2. During an explicitly approved cutover, deploy the Runner pinned to the tested engine commit before replacing the private engine main entrypoint. The pinned commit is already reachable from the tested engine feature branch; it need not be on main to be checked out.
3. Merge the engine feature requests with merge commits so the tested pinned revision remains reachable. Preserve live queue/history files and account scope.
4. Review a fresh manual dry-run on the intended board. Keep public artifact upload off unless specifically wanted.
5. Only after an explicitly authorized live test and final queue checkpoint should scheduled publication be enabled. The two opt-ins can cause the new schedule to remain paused; that transition must be planned rather than inferred from a code merge.

GH_PAT remains scoped to checkout and state-sync steps; Pinterest credentials remain scoped to media preparation and one Pin creation. No secret values belong in source or workflow inputs.
