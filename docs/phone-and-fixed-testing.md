# Fixed cases and Android testing

For remote judges and phones, open the [hosted fixed test hub](https://matchos-judging.victoriousgrass-e3cb5a12.northcentralus.azurecontainerapps.io/testing.html); no local server, shared Wi-Fi or hotspot is needed. Share the public root or test-hub URL rather than a browser-owned matchday link.

For local development, open `http://127.0.0.1:5173/testing.html` with the usual frontend/backend running. This hub lists all 12 versions, the exact goal/red-card times and a test checklist. A case opens from kickoff with an explicit version, independent of randomization. Each launch uses a private random ID so different browser sessions cannot claim each other's tests. Return to the hub in the same tab to release the previous fixed test before starting another. Pause first. Do not click New matchday within a case: that starts normal random selection. Capacity failures are reported rather than silently substituting a different version.

The test hub does not automatically jump the clock or call AI. Use Fast to approach the listed checkpoint, then pause. Goals at :11 enter at the next 30-second update. Inspect the actual AI/fallback label and source events. Check English/Spanish, both audiences and voices, goal/recovery/pass chronology, quiet matches, red-card alerts elsewhere, dismiss/follow/expiry, pause/resume and all three clocks. Start with one case per version, not repeated requests until an answer passes.

## Phone on a private network

The phone and computer must be able to connect directly. Eduroam may isolate clients. If the link times out there, connect the computer to your phone's hotspot or use a home/private Wi-Fi network, then rerun `ipconfig` on the computer and use its new IPv4 address. Do not disable the firewall. If a Windows permission prompt appears, allow the preview only on a trusted private network. No router port forwarding or public deployment is needed.

From CMD in the project directory, stop the existing backend with Ctrl+C, then start it with the exact private computer IP. Example only: replace `192.168.1.50` with your computer's actual private IPv4 address:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start_backend.ps1" -AI -Speech -PhoneAddress "192.168.1.50"
```

Enter Foundry and Speech keys only into the hidden local prompts. In another CMD window in the same project directory:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start_phone_frontend.ps1" -Address "192.168.1.50"
```

Then open `http://192.168.1.50:5176/testing.html` in an Android browser. Samsung Internet worked in the owner's test; Android Chrome returned `ERR_TOO_MANY_RETRIES` on that setup. The address changes when you change networks; replace it in both commands and the phone link. This separate preview serves built assets, forwards the API to loopback, permits only the explicitly configured backend origin and blocks development draft diagnostics. The backend remains on 127.0.0.1:8000. Stop the phone preview with Ctrl+C when finished. It is not a public production host.

Local HTTP may not provide browser device voices, but configured Azure audio uses the existing server. Replay IDs support private-network HTTP without requiring randomUUID. Actual Android audio, connectivity and touch behavior must be checked on the device; desktop emulation alone does not prove them.

## Mobile layout check

Use normal Android font/display settings first; do not disable accessibility zoom. Test 360–412px portrait widths and landscape. Confirm no horizontal scrolling, readable 14px recap body, compact header/scoreboard/pitch, touch controls at least 44px tall, no toast hiding the main action, keyboard-free selection controls, pause/replay and Catch Me Up. This layout reduces scrolling; it does not squeeze every feature onto a single screen.
