---
name: browser-verified-web-work
description: Use after changing anything rendered in a browser — UI components, pages, templates, styles, client-side scripts, static site or blog content — before claiming the change works or is complete. Also use when a web change "compiles fine" or "tests pass" but has not been observed rendering.
---

# Flight Rule: See It Render

A web change isn't done until it has been **observed in a browser**. Passing builds
and green unit tests do not prove a page renders, a style applies, or a click works.
This is `verification-before-completion` specialized for the web.

## Process

1. **Serve** — start or reload the app/site (dev server, preview build, deployed
   env). Note the URL of the affected page.
2. **Load** — open that page with the available browser tooling (Chrome DevTools MCP,
   claude-in-chrome, or the project's own preview harness).
3. **Console** — read the browser console. New errors or warnings introduced by the
   change are failures, even if the page "looks fine".
4. **Interact** — exercise the changed element: click the button, submit the form,
   resize if the change was responsive.
5. **Capture** — screenshot the result as evidence, and check it actually shows the
   intended change (right page, right state).
6. On any failure → `systematic-debugging`. Do not patch styles blind.

## Rules

- Check the pages that *consume* the change, not just the component in isolation.
- For visual changes, before/after screenshots are the failing-check-first pattern
  (`test-driven-development`): capture the wrong state first when practical.
- No browser tooling available? Say so explicitly — give the user the URL and the
  exact things to look at. An honest "unverified: please check X" beats a false
  "done".

## When NOT to Use

Pure backend/API changes (curl the endpoint instead), CLI tools, and infrastructure
with no rendered surface.
