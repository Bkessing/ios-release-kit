# When a release goes wrong

iOS release errors name a symptom, not a cause. Reasoning from the message text
sends you the wrong way often enough that it is worth not doing at all — run
`appstore-doctor` and read the actual state.

The table below is for recognising which way to go, not for diagnosing from.

| What they see | What it usually is |
|---|---|
| `exportArchive No Accounts` | No distribution certificate, **or** export using automatic signing with no Apple ID in Xcode. Not a logged-out Xcode. |
| `CodeSign … errSecInternalComponent` | Locked login keychain. Nothing to do with the framework it names. |
| `No profiles for '<bundle>' were found` | Usually **not** a missing profile. Automatic signing at export cannot authenticate. Set `IRK_EXPORT_PROFILE`. |
| `doesn't include signing certificate` | A cached profile still bound to a certificate that no longer exists. |
| `The bundle version must be higher…` | That build number is already uploaded. |
| `ITMS-90717 Invalid large app icon` | The icon PNG carries an alpha channel. A fully opaque RGBA export still fails — the channel's presence is what Apple rejects. |
| Approved, live, sells nowhere | No app-level availability record. `fastlane open_territories`. |
| `git push` fails with `-25293` | Locked keychain again, blocking the credential helper. |

## Specific situations

**A stuck submission.** Cancelling does not free the version immediately; Apple
takes time to move it out of the queue, and attaching a build during that window
fails. `resubmit` retries rather than assuming. If it still will not attach,
wait and run it again — this is normal, not a broken account.

**A rejection for Guideline 3.1.2.** Apps with auto-renewing subscriptions must
carry, in the metadata: subscription length, price, and working links to the
privacy policy and Terms of Use. Apple's automated rejection message often names
only one of these, so fixing exactly what it says earns a second rejection. Run
`fastlane asc_check`, which checks all of them.

**A rejection for Guideline 2.1 on in-app purchases.** Usually a reviewer who
could not reach the purchase because it sits behind progression, or demo
credentials that do not work. No API can see either. If the app has IAPs behind
any kind of gate, tell them to put the exact steps in the review notes.

**A version that says READY_FOR_SALE but nobody can buy.** Check territories
first. An app can be fully approved and available in zero storefronts because
the availability record was never created, and App Store Connect gives no
warning — a 404 on `appAvailabilityV2` is the only signal.

**Certificates and profiles are coupled.** A provisioning profile embeds the
certificates that existed when it was made, so replacing a certificate silently
invalidates every existing profile while they sit on disk looking fine. If
profiles are orphaned, delete them **and** create replacements. Doing only the
first produces a more confusing error than the one you started with.

**A build that will not appear in TestFlight.** Processing takes minutes, not
seconds, and `build_status` shows where it is. If it has been long enough and it
is still not there, check email — Apple sends the reason for a rejected binary
there rather than surfacing it in the API.

## Rules while fixing things

- **State changes at Apple are not instant.** After creating a version,
  attaching a build, or cancelling a submission, re-read the state rather than
  assuming the next call will see it.
- **A locked keychain cannot be fixed by an agent.** `security unlock-keychain`
  prompts interactively. Ask them to run it themselves.
- **`asc_check` passing does not guarantee approval.** It checks what an API can
  see. Whether a reviewer can reach a purchase, whether demo credentials work,
  and whether the screenshots represent the app are all outside it. Say so
  rather than letting a clean run read as a promise.
