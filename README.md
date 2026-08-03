# ios-release-kit

Shared fastlane lanes for shipping iOS apps to TestFlight and the App Store.

One lane library, imported by every app. Fix a lane once, every app gets it.

Extracted from three shipped apps. The comments explaining *why* each lane is
shaped the way it is are the point — most of them encode a specific failure that
cost a real day.

## Use it

In your app's `fastlane/Fastfile`:

```ruby
opt_out_usage
default_platform(:ios)

ENV["IRK_APP_ID"]  ||= "com.acme.app"
ENV["IRK_PROJECT"] ||= "Acme.xcodeproj"
ENV["IRK_SCHEME"]  ||= "Acme"
ENV["IRK_TEAM_ID"] ||= "XXXXXXXXXX"

import_from_git(url: "https://github.com/Bkessing/ios-release-kit")
```

Then `fastlane lanes` shows everything below. Anything app-specific stays in
your own Fastfile and coexists fine.

### Config

| Variable | Required | Purpose |
|---|---|---|
| `IRK_APP_ID` | yes | bundle identifier |
| `IRK_PROJECT` | yes | `.xcodeproj` name |
| `IRK_SCHEME` | yes | build scheme |
| `IRK_TEAM_ID` | yes | Apple team id |
| `IRK_APP_NAME` | no | display name, defaults to the scheme |
| `IRK_EXPORT_PROFILE` | no | provisioning profile name — see manual signing below |
| `IRK_SHOTS_DIR` | for `upload_shots` | screenshots directory |
| `IRK_CONTACT_*` | for `public_beta` | review contact first/last/email/phone |

Auth is an App Store Connect API key, from your app's gitignored `fastlane/.env`:

```
ASC_KEY_ID=XXXXXXXXXX
ASC_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

with `AuthKey_<KEY_ID>.p8` in `~/.appstoreconnect/private_keys/`.

Missing config fails immediately with the exact line to add, rather than
surfacing later as a confusing Apple error.

## Lanes

**Account**

| Lane | Does |
|---|---|
| `verify` | prove the API connection, list the team's apps |
| `create_app` | register the bundle id, report whether the app record exists |
| `signing_cert` | create the Apple Distribution certificate |

**Build and upload**

| Lane | Does |
|---|---|
| `beta_internal` | build, sign, upload to TestFlight internal. No Beta App Review, no 24h wait |
| `public_beta` | distribute an already-uploaded build to external testers |

**Version and submission**

| Lane | Does |
|---|---|
| `new_version` | create or reuse an editable version, set What's New |
| `attach_build` | attach an uploaded build to it |
| `set_release_type` | `AFTER_APPROVAL`, `MANUAL` or `SCHEDULED` |
| `submit` | submit for review |
| `resubmit` | cancel a stuck submission, reattach, ready to resubmit |

**Assets and metadata**

| Lane | Does |
|---|---|
| `upload_shots` | replace **both** iPhone screenshot sets, with size validation |
| `pull_metadata` | pull the live listing into `fastlane/metadata/` |
| `push_metadata` | push it back. Submits nothing |

**Status**

| Lane | Does |
|---|---|
| `release_status` | version states, attached builds, review submissions |
| `tf_state` | TestFlight groups and unexpired builds |

## The failures these encode

**Manual signing at export.** Automatic signing needs an Apple ID signed into
Xcode. A headless or agent-driven run has none, and fails with `exportArchive No
Accounts` followed by `No profiles for '<bundle>' were found` — which is
misleading, because the profile is not missing. Set `IRK_EXPORT_PROFILE` to a
profile name and `beta_internal` exports with manual signing, removing the
account dependency entirely.

**Both screenshot sets.** `APP_IPHONE_67` (6.9in) is what modern iPhones render
in search results; `APP_IPHONE_65` is secondary. Writing only one silently
leaves the other serving stale artwork to most of your traffic. `upload_shots`
writes both and validates pixel dimensions from the PNG header before uploading.

**The resubmit race.** Cancelling a submission does not free the version
immediately — Apple takes time to move it out of the queue, and attaching during
that window fails. `resubmit` retries rather than assuming.

**DerivedData outside `~/Documents`.** codesign chokes on the extended
attributes iCloud adds to synced files, so builds go to `/tmp`.

**The app record is the one manual step.** Apple's API has no CREATE on the apps
resource. `create_app` registers the bundle id and tells you exactly what to
click for the rest.

## Companion

[appstore-doctor](https://github.com/Bkessing/appstore-doctor) — read-only
diagnostics for when one of these fails. Checks signing state, certificates
against your keychain, and App Store Connect submission readiness.

## License

MIT.
