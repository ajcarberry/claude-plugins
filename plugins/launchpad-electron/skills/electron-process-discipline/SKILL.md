---
name: electron-process-discipline
description: Use when writing or changing Electron app code — main process, renderer, preload scripts, IPC handlers — or when debugging why an Electron feature works in the renderer but not end-to-end.
---

# Electron Process Discipline

Electron bugs cluster at the process boundary. Know which side you're on before
writing a line.

## The Boundary

- **Main** owns: windows, menus, filesystem, OS integration, auto-update, anything
  privileged. **Renderer** owns: UI. **Preload** is the only bridge.
- IPC via `contextBridge` + `ipcRenderer.invoke`/`ipcMain.handle` — typed
  request/response pairs, not ad-hoc `send` spaghetti. Adding a channel = updating
  preload's exposed API + both sides + the type surface.
- Security defaults are non-negotiable: `contextIsolation: true`,
  `nodeIntegration: false`, no `remote`. Renderer code never touches Node APIs
  directly — if it seems to need them, that logic belongs in main behind IPC.

## Run-and-Verify Loop

A change isn't done until observed **in the running app** — the Electron analog of
`browser-verified-web-work`:

1. Launch the dev app; exercise the changed feature via the UI.
2. Watch **both consoles**: renderer DevTools *and* the main-process terminal —
   errors split across them, and IPC failures often only surface in one.
3. IPC changes: verify the round trip end-to-end (trigger in renderer → observe main
   effect → response back), not just the renderer call.

## Debugging Rule

"Works in renderer, fails in app" is almost always the boundary: channel name
mismatch, preload not re-exposing the new API, or main handler not registered.
Trace the IPC chain before touching feature logic (`systematic-debugging`).
