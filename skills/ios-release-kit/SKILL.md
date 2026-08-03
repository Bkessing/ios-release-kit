---
name: ios-release-kit
description: Ship an iOS app to TestFlight or the App Store, and walk a first-timer through the parts Apple will not let a script do. Use when the user wants to get their app onto their phone, onto TestFlight, or into the App Store; when setting up releases for a new app; when a version needs a build attached, metadata pushed, screenshots uploaded, or submitting for review; or when they ask what is left before they can ship.
---

# ios-release-kit

Shared fastlane lanes that do the shipping. Assume the user has never released
an app and does not know what a provisioning profile is. Most of the work is
automatable; the rest is Apple insisting on a human, and your job is to make
those parts painless rather than to hand over a checklist.

## How to run this

**Find out where they are before telling them anything.** A first-timer given a
twelve-step list closes the tab. Run the state check, then give them exactly one
next action.

```bash
# From inside the app's directory. Safe, read-only, no side effects.
fastlane release_status 2>/dev/null || echo "kit not wired up yet"
```

Then work down this table and stop at the first row that is not satisfied. Do
the automatable ones yourself. For a manual one, read
`reference/manual-steps.md` and walk them through **that one step only**.

| # | Gate | Who does it | How you check |
|---|---|---|---|
| 1 | Paid Apple Developer membership | **Them** (~10 min + Apple's review) | `fastlane verify` fails to auth |
| 2 | App Store Connect API key | **Them** (~3 min) | `fastlane verify` |
| 3 | fastlane installed | You | `which fastlane` |
| 4 | Kit wired into their Fastfile | You | `fastlane lanes` lists `beta_internal` |
| 5 | Distribution certificate | **You** — `fastlane signing_cert` | `security find-identity -v -p codesigning \| grep Distribution` |
| 6 | App record in App Store Connect | **Them** (~2 min, no API for it) | `fastlane create_app` |
| 7 | Build on TestFlight | You — `fastlane beta_internal` | `fastlane build_status` |
| 8 | Screenshots | **Them** (they must look at them) | `fastlane asc_check` |
| 9 | Listing metadata | You — `push_metadata`, `stage`, `set_privacy_policy` | `fastlane asc_check` |
| 10 | Territories | You — `fastlane open_territories` | included in `asc_check` |
| 11 | Age rating + App Privacy answers | **Them** (dashboard only) | `appstore-doctor --bundle …`, or ask them to confirm |
| 12 | Submit | You — `fastlane submit` | `fastlane release_status` |
| 13 | Agreements, Tax and Banking | **Them**, before any money moves | dashboard only, no API |

Load these as you need them:

- `reference/manual-steps.md` — the human-only gates, each with exact navigation
  and a command that proves it worked. **Read this before walking anyone through
  one**, so you give them Apple's current path rather than a half-remembered one.
- `reference/lanes.md` — every lane, its arguments, and what it will refuse to do.
- `reference/troubleshooting.md` — what breaks mid-release and what it means.

## Talking to a first-timer

- **One step at a time.** Say what to click, then wait. Do not preview step 7.
- **Never make them look something up.** If you need their Team ID, fetch it
  with `fastlane verify` rather than telling them where it lives.
- **Say which parts you are doing.** "I'll handle the certificate, you'll need
  to create the app record because Apple has no API for it" sets expectations
  and stops them wondering why they are suddenly clicking.
- **Verify every manual step yourself.** They click, you run the check and tell
  them it landed. Do not take "I did it" as proof — Apple's UI has several
  screens where you can hit Save and change nothing.
- **Translate.** They do not know what a bundle id, a provisioning profile, or
  a build number is. Say "the reverse-domain name that identifies your app, like
  `com.yourname.myapp`" the first time, then use the term.
- Costs are worth being upfront about: the membership is **$99/year** and there
  is no free tier that reaches the App Store. TestFlight needs it too.

## Wiring the kit into a new app

The app's own `fastlane/Fastfile`, created if absent:

```ruby
opt_out_usage
default_platform(:ios)

ENV["IRK_APP_ID"]  ||= "com.acme.app"      # bundle identifier
ENV["IRK_PROJECT"] ||= "Acme.xcodeproj"
ENV["IRK_SCHEME"]  ||= "Acme"
ENV["IRK_TEAM_ID"] ||= "XXXXXXXXXX"        # `fastlane verify` prints it

import_from_git(url: "https://github.com/Bkessing/ios-release-kit")
```

Credentials go in `fastlane/.env`, which **must be gitignored**:

```
ASC_KEY_ID=XXXXXXXXXX
ASC_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

The key id and issuer id are identifiers, not secrets. The `.p8` file is a real
credential and belongs at `~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8`.
**Never ask anyone to paste a `.p8` into the conversation.**

Two things that will bite you:

- `import_from_git` fetches from the **GitHub remote**, not a local clone. If you
  edit a lane, it is invisible until pushed.
- Lane arguments are environment variables, not fastlane's `key:value` syntax:
  `VERSION=1.2.0 fastlane new_version`, not `fastlane new_version version:1.2.0`.

## Scope

These lanes write to a live App Store Connect account. `submit` and
`public_beta` are outward-facing and irreversible in the sense that they put
your app in front of Apple or real testers — **confirm before running either**,
even if the user asked for "the whole thing". Everything else is safe to run.

For diagnosing a failure rather than performing a step, use the companion
`appstore-doctor` skill; it is read-only and will not touch the account.
