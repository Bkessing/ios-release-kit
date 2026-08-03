# Lane reference

Arguments are **environment variables placed before the command**, not
fastlane's `key:value` syntax:

```bash
VERSION=1.2.0 WHATS_NEW="Fixed the thing" fastlane new_version
```

Anything missing fails immediately with the exact line to add, rather than
surfacing later as a confusing Apple error.

## Read-only — safe to run any time

| Lane | Args | Does |
|---|---|---|
| `verify` | — | Proves the API key works. Lists the team's apps and prints the Team ID. The first thing to run when anything looks wrong. |
| `release_status` | — | Version states, attached build, current review submission. |
| `tf_state` | — | TestFlight groups, testers, unexpired builds. |
| `build_status` | — | Processing and TestFlight state of recent uploads. |
| `asc_check` | `STRICT=1` to fail | Pre-submission guard: version state, both screenshot sets, Guideline 3.1.2 subscription metadata. |
| `pull_metadata` | — | Pulls the live listing into `fastlane/metadata/`. Writes locally, changes nothing at Apple. |

## Setup — run once per app

| Lane | Args | Does |
|---|---|---|
| `create_app` | — | Registers the bundle id. Cannot create the app record itself: Apple has no API for it. Reports which half is done. |
| `signing_cert` | — | Creates the Apple Distribution certificate if the account has none. |
| `setup_internal` | `TESTER_EMAIL=` | Creates the internal TestFlight group and adds a tester. Defaults to `IRK_CONTACT_EMAIL`. |

## Build and distribute

| Lane | Args | Does |
|---|---|---|
| `beta_internal` | `CHANGELOG=` | Builds, signs, uploads to TestFlight internal testers. No Beta App Review, no 24-hour wait — this is the fast path to getting it on their phone. |
| `public_beta` | `CHANGELOG=` | Distributes an already-uploaded build to **external** testers. Goes through Beta App Review. **Outward-facing: confirm first.** |

`beta_internal` regenerates the xcodegen project first if `IRK_USES_XCODEGEN` is
set, and exports with manual signing when `IRK_EXPORT_PROFILE` names a profile.

## Version and submission

| Lane | Args | Does |
|---|---|---|
| `new_version` | `VERSION=` `WHATS_NEW=` | Creates or reuses an editable version. |
| `attach_build` | `BUILD=` | Attaches an uploaded build to the editable version. |
| `set_release_type` | `RELEASE_TYPE=` | `AFTER_APPROVAL` (default), `MANUAL`, or `SCHEDULED`. |
| `submit` | — | Submits for review. **Outward-facing: confirm first.** |
| `resubmit` | `BUILD=` | Cancels a stuck submission and reattaches. Retries, because cancelling does not free the version immediately. |

## Metadata and assets

| Lane | Args | Does |
|---|---|---|
| `push_metadata` | — | Pushes `fastlane/metadata/` to the editable version. Submits nothing. |
| `upload_shots` | `IRK_SHOTS_DIR=` | Replaces **both** iPhone screenshot sets. Validates pixel dimensions from each PNG header before uploading anything. |
| `stage` | — | Support URL and App Review contact details. Requires `IRK_CONTACT_PHONE`. |
| `set_privacy_policy` | `URL=` | Privacy policy URL on every locale. Separate from `stage` because it lives on a different resource. |
| `open_territories` | — | Makes the app available in every App Store territory. Creates the record if absent, reports and exits if it exists. |

## Ordering

A first release, once the manual gates in `manual-steps.md` are cleared:

```bash
fastlane verify                                    # key works
fastlane signing_cert                              # certificate exists
fastlane create_app                                # bundle id registered
CHANGELOG="First build" fastlane beta_internal     # on their phone via TestFlight
```

Stop there if TestFlight was the goal. To go on to the App Store:

```bash
VERSION=1.0.0 WHATS_NEW="Initial release" fastlane new_version
BUILD=<number> fastlane attach_build
fastlane push_metadata
IRK_SHOTS_DIR=./shots fastlane upload_shots
fastlane stage
URL=https://example.com/privacy fastlane set_privacy_policy
fastlane open_territories
fastlane asc_check                                 # read the output before continuing
fastlane submit                                    # confirm with the user first
```

## Things a lane will refuse to do

These are guards, not bugs. When one fires, the message is the answer.

- `upload_shots` refuses the **entire** upload if any screenshot is the wrong
  size, rather than updating one set and leaving the other stale.
- `new_version` will not touch a version that is not editable.
- `open_territories` will not modify an existing availability record. There is no
  PATCH for it, so it reports what exists rather than pretending it changed
  something.
- `stage` refuses without `IRK_CONTACT_PHONE`. Apple requires a review contact
  phone number and there is no sensible default.
- Any missing `IRK_*` variable fails with the exact line to add to the Fastfile.
