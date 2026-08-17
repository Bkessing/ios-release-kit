# ios-release-kit

Shared fastlane lanes for shipping iOS apps to TestFlight and the App Store.

One lane library, imported by every app. Fix a lane once, every app gets it.

Extracted from three shipped apps. The comments explaining *why* each lane is
shaped the way it is are the point — most of them encode a specific failure that
cost a real day.

## Never shipped an app before?

Use it through [Claude Code](https://claude.com/claude-code) and let it drive.
Copy the skill in, then say what you want:

```bash
git clone https://github.com/Bkessing/ios-release-kit
mkdir -p ~/.claude/skills
cp -R ios-release-kit/skills/ios-release-kit ~/.claude/skills/
```

Then: *"get my app onto TestFlight"*.

It works out which of the steps below are already done, does the automatable
ones, and walks you through the ones Apple insists a human do — creating the App
Store Connect API key, the app record, the age rating — one at a time, checking
each landed before moving on. It will not read you a twelve-step checklist.

Worth knowing up front: the Apple Developer Program is **$99/year** and there is
no free route to TestFlight or the App Store.

Pair it with [appstore-doctor](https://github.com/Bkessing/appstore-doctor) for
diagnosis when something fails. This repo does; that one reads.

## The three tools

| | | |
|---|---|---|
| [ios-bootstrapper](https://brandonkessinger.com/tools/) | build the app | $49 founder |
| [ios-release-kit](https://github.com/Bkessing/ios-release-kit) | ship it | free |
| [appstore-doctor](https://github.com/Bkessing/appstore-doctor) | diagnose it | free |

The two free tools are the whole release story and stand on their own — nothing
here is crippled to sell you something. **ios-bootstrapper** is the step before
them: it creates the app itself, with persistence that will not wipe your users
on update, analytics you can filter your own traffic out of, and the purchase and
crash-reporting wiring already done.

## Install both

The short way, with the [skills CLI](https://skills.sh):

```bash
npx skills add Bkessing/appstore-doctor
npx skills add Bkessing/ios-release-kit
```

Or by hand:

These are two halves of one job: this one writes, the other reads. Install the
pair and Claude picks whichever the moment calls for.

```bash
git clone https://github.com/Bkessing/appstore-doctor
git clone https://github.com/Bkessing/ios-release-kit

mkdir -p ~/.claude/skills
cp -R appstore-doctor/skills/appstore-doctor  ~/.claude/skills/
cp -R ios-release-kit/skills/ios-release-kit  ~/.claude/skills/
```

They are deliberately separate packages. appstore-doctor issues **GET requests
only** — that is why handing it an API key is reasonable, and it would not
survive being merged into something that can submit an app for review. It also
runs on a stock Mac with no Apple membership and no fastlane, which matters when
the broken thing *is* your fastlane setup.

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
| `setup_internal` | create the internal TestFlight group and add a tester |

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
| `resubmit` | cancel a submission stuck in the review QUEUE, reattach |
| `resubmit_rejected` | unstick a REJECTED version whose old submission never resolved |

**Assets and metadata**

| Lane | Does |
|---|---|
| `upload_shots` | replace **both** iPhone screenshot sets, with size validation |
| `pull_metadata` | pull the live listing into `fastlane/metadata/` |
| `push_metadata` | push it back. Submits nothing |
| `stage` | support URL + App Review contact details |
| `set_privacy_policy` | privacy policy URL on every locale |
| `open_territories` | make the app available in every territory |
| `analytics_report` | turn on App Store analytics. `SNAPSHOT=1` backfills history |

**Status**

| Lane | Does |
|---|---|
| `release_status` | version states, attached builds, review submissions |
| `tf_state` | TestFlight groups and unexpired builds |
| `build_status` | processing and TestFlight state of recent uploads |
| `asc_check` | pre-submission guard: version state, screenshots, 3.1.2 metadata |

## The failures these encode

**Manual signing at export.** Automatic signing needs an Apple ID signed into
Xcode. A headless or agent-driven run has none, and fails with `exportArchive No
Accounts` followed by `No profiles for '<bundle>' were found` — which is
misleading, because the profile is not missing. Set `IRK_EXPORT_PROFILE` to a
profile name and `beta_internal` exports with manual signing, removing the
account dependency entirely.

**A capability breaks the archive, and the error blames your Apple ID.** The
archive step signs automatically even though the export names a profile, and
automatic resolves to the team wildcard, `iOS Team Provisioning Profile: *`,
which carries no capabilities. Add Game Center, push, iCloud or HealthKit and
the build dies with `No Accounts: Add a new account in Accounts settings`
followed by `doesn't include the ... capability`. The first line is a red
herring; the correct profile is installed and named for a later step. Fix it in
your app's own target (Release config, manual signing, name the profile) — not
in this kit's `xcargs`, which apply to every target and are rejected outright by
SPM package targets. Enable the capability on the App ID *before* cutting the
profile: a profile only carries what the App ID had when it was created. And
once the app's project names a Release profile, that name and
`IRK_EXPORT_PROFILE` must agree — `beta_internal` checks this before archiving
and fails with both values printed, because the natural drift (a re-cut
profile gets a new date-stamped name and only one of the two places is
updated) otherwise surfaces minutes later wearing the same misleading "No
Accounts" costume. `IRK_SKIP_PROFILE_CHECK=1` bypasses.

**Analytics do not accrue until you ask.** Apple generates App Store analytics
only for apps that have an `analyticsReportRequest`. Without one there are no
impressions, no source types, no download reports — not empty, absent. You find
out on the day you first want to know where an install came from, which is the
day it is already too late. Worse, `ONGOING` starts from the moment you ask and
cannot see backwards; only `ONE_TIME_SNAPSHOT` recovers history. Run
`analytics_report` when the app record is created, then again with `SNAPSHOT=1`.
Apple also stops a feed nobody collects from, and the only tell is
`stoppedDueToInactivity` on the request.

**Both screenshot sets.** `APP_IPHONE_67` (6.9in) is what modern iPhones render
in search results; `APP_IPHONE_65` is secondary. Writing only one silently
leaves the other serving stale artwork to most of your traffic. `upload_shots`
writes both and validates pixel dimensions from the PNG header before uploading.

**The resubmit race.** Cancelling a submission does not free the version
immediately — Apple takes time to move it out of the queue, and attaching during
that window fails. `resubmit` retries rather than assuming.

**DerivedData outside `~/Documents`.** codesign chokes on the extended
attributes iCloud adds to synced files, so builds go to `/tmp`.

**Approved and selling nowhere.** An app can sit at `READY_FOR_SALE`, fully
approved, and be purchasable in zero storefronts because the availability record
was never created. Nothing warns you; a 404 is the only signal. `open_territories`
creates it. Reading an existing one has to follow Apple's own relationship link —
asking for `territoryAvailabilities` under `/v1/` returns a path error that reads
exactly like "no territories" when the app has all of them.

**The privacy policy is not where you think.** It lives on `appInfoLocalizations`,
while the support URL and review contact live on the version localizations. A
fully staged version can still be missing it, and Apple blocks submission on it.
That is why `set_privacy_policy` is a separate lane from `stage`.

**The app record is the one manual step.** Apple's API has no CREATE on the apps
resource. `create_app` registers the bundle id and tells you exactly what to
click for the rest.

## Support

A lane that failed on your setup, or an App Store Connect state these do not
handle yet: support@brandonkessinger.com.

## License

MIT.
