# The steps Apple will not let a script do

Each of these has to be done by a human in a browser. Walk the user through
**one at a time**, then run the verification command yourself and tell them it
landed. Do not read them the whole file.

Apple moves things around in App Store Connect. Where a path below is stale,
describe what they are looking for rather than insisting on the exact menu, and
say plainly that the UI may have shifted.

---

## 1. Apple Developer Program membership

**Cost: $99/year. There is no free path to TestFlight or the App Store.** A free
Apple ID can run an app on a device you own, and that is it. Say this early —
finding out at step 6 feels like a bait and switch.

Send them to <https://developer.apple.com/programs/enroll/>. As an individual
they need an Apple ID with two-factor on and a payment method; enrolment is
usually quick but Apple sometimes takes a day or two. As a company they will
need a D-U-N-S number for the business, which can take longer, so if they are
undecided and want to ship this week, enrolling as an individual is the faster
road. The tradeoff is that the App Store then lists their personal name as the
seller, and switching later is not trivial.

**Verify:** nothing to run yet. They will have an email from Apple, and
<https://appstoreconnect.apple.com> will load a dashboard rather than a signup.

---

## 2. App Store Connect API key

This is what lets everything else be automated, so it is worth doing carefully.

In App Store Connect: **Users and Access** → **Integrations** tab → **App Store
Connect API** → the **+** to generate a key.

Two things to get right:

- **Role.** Pick **App Manager**. Developer is enough to read but not to push
  metadata or submit, and discovering that halfway through is a bad afternoon.
  Admin also works and is more access than this needs.
- **The `.p8` downloads exactly once.** Apple will not show it again. If they
  lose it, the only fix is to revoke the key and make a new one.

Have them save the file to `~/.appstoreconnect/private_keys/` keeping Apple's
filename, which looks like `AuthKey_ABC123XYZ.p8`. Create the directory first:

```bash
mkdir -p ~/.appstoreconnect/private_keys
```

Then ask them for the **Key ID** and **Issuer ID** from that same page. Both are
identifiers rather than secrets, so it is fine for them to paste those into the
chat — **the `.p8` is not**, and if they offer to paste its contents, tell them
not to and point them at the directory instead.

Write those two into the app's `fastlane/.env` and make sure that file is
gitignored.

**Verify:**

```bash
fastlane verify
```

It lists the team's apps. That single command proves the key exists, the file is
in the right place, the role is sufficient, and the ids match.

---

## 3. The app record in App Store Connect

**Apple's API has no CREATE for the apps resource.** This one genuinely cannot be
automated, so do not spend time looking for a way around it.

First, register the bundle identifier, which *is* automatable:

```bash
fastlane create_app
```

It registers the identifier and then tells them what remains. In App Store
Connect: **My Apps** → **+** → **New App**, and they will need

- **Platform:** iOS
- **Name:** what appears on the store. It has to be globally unique, and good
  names are frequently taken. If Apple rejects it as unavailable, a longer form
  like `Name: What It Does` usually clears, and the home-screen name is set
  separately in the project so it can stay short.
- **Primary language**
- **Bundle ID:** picked from the dropdown, which is why `create_app` runs first
- **SKU:** internal only, never shown to anyone. The bundle id is a fine answer.

**Verify:**

```bash
fastlane create_app
```

Run it again. It now reports the app record as found.

---

## 4. Screenshots

Automatable to capture, not automatable to approve — someone has to look at them
and decide they are not embarrassing. Apple also rejects screenshots that
misrepresent the app, so a human should see what is being uploaded.

Two sets are required, and both must be exact:

| Set | Size | Why |
|---|---|---|
| 6.9 inch | **1290x2796** | what modern iPhones show in search results |
| 6.5 inch | **1284x2778** | secondary, still served to a lot of traffic |

Uploading only one leaves the other quietly serving whatever was there before,
which is usually nothing or something a year old.

Layout: the 6.9in files sit in the directory, the 6.5in versions go in a `65/`
subdirectory **using the same filenames**.

```
shots/
  01-home.png      ← 1290x2796
  02-detail.png
  65/
    01-home.png    ← 1284x2778
    02-detail.png
```

**Verify:**

```bash
IRK_SHOTS_DIR=./shots fastlane upload_shots
```

The lane reads each PNG's real dimensions and refuses the whole upload if any
file is the wrong size, so a mistake here fails immediately and loudly rather
than half-updating one set.

---

## 5. Age rating and the App Privacy questionnaire

Both are dashboard-only. `appstore-doctor` can see whether the age rating is
declared; the privacy questionnaire returns 404 on the API, so nobody can check
it programmatically — it has to be confirmed by eye.

**Age rating:** the app's page → **App Information** → **Age Rating** → Edit.
A questionnaire about violence, language, and so on. Answering honestly matters
more than answering low; a wrong answer is a rejection.

**App Privacy:** the app's page → **App Privacy**. They declare what data the app
collects and whether it tracks users. If the app genuinely collects nothing,
this is quick, but it still has to be answered — an unanswered questionnaire
blocks submission.

Two traps worth naming out loud, because they cause rejections rather than
warnings: analytics SDKs count as collection even when the data is anonymous,
and crash reporters usually do too.

**Verify:**

```bash
appstore-doctor --bundle com.example.app
```

Age rating shows up there. For App Privacy, ask them to confirm the section no
longer shows as needing attention, and say honestly that you cannot check it.

---

## 6. Agreements, Tax and Banking

**Nothing about this blocks a free app from shipping.** It blocks *money*. Bring
it up when they add a paid app or an in-app purchase, not during a first free
release, or it is one more hurdle in front of the thing they actually want.

App Store Connect → **Business** (Apple renamed this from "Agreements, Tax, and
Banking", so an older tutorial will send them somewhere that no longer exists).
Three parts: the Paid Applications agreement, banking details, and tax forms.

**Only the Account Holder can do this.** Not Admin, not App Manager. If they set
their account up with a separate holder, that person has to sign in themselves.

Worth setting expectations: Apple pays roughly 30–45 days after the close of the
fiscal month, so August earnings arrive in early October. First revenue feeling
slow is normal, not a sign something is misconfigured.

**Verify:** none possible. `/v1/agreements` returns 404 — the endpoint does not
exist. Ask them to confirm the Business section shows no outstanding actions.

---

## 7. Unlocking the keychain

Not App Store Connect, but it comes up constantly and no agent can do it. If a
build fails with `errSecInternalComponent`, or `git push` fails with `-25293`,
the login keychain is locked.

Ask them to run this **in their own terminal**, because it prompts for their Mac
password:

```bash
security unlock-keychain ~/Library/Keychains/login.keychain-db
```

Do not try to automate around it and do not ask them for the password.

**Verify:** re-run whatever failed.
