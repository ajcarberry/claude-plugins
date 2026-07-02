---
name: electron-landing-mechanics
description: Use when packaging, signing, or releasing an Electron app and verifying the built artifact — /land's deploy, observe, and validate steps for a desktop app release.
---

# Electron Landing Mechanics

For a desktop app, "deploy" means **package and release**, and validation means the
*installed artifact* works — not the dev build.

## Package

- Build with the project's packager (electron-builder/forge). The packaged app is a
  different animal from `npm start`: asar paths, native modules, missing dev deps
  all break here first.
- macOS: sign and notarize; verify with `spctl -a -vv` and `xcrun notarytool`
  history rather than assuming the pipeline did it.

## Smoke Test (the landing V-checks)

Install and launch the **packaged** artifact on the target platform:

1. Cold launch from Finder/Explorer (not the terminal) — window appears, no error
   dialog.
2. Exercise the changed feature in the installed app.
3. Check logs where the packaged app writes them (`~/Library/Logs/<app>`,
   `%APPDATA%`) — clean of new errors.
4. If auto-update shipped: verify the previous version actually updates to this one
   against the release feed.

## Rollback

Releases roll back by pulling/re-pointing the release feed to the previous version —
keep the previous artifact published until the new one has survived its smoke test.
