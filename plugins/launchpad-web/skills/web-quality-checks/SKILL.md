---
name: web-quality-checks
description: Use when finishing a user-facing web feature or page — before calling web work polished — or when asked about web performance, Core Web Vitals, accessibility, or a11y compliance of a change.
---

# Web Quality Checks

Beyond "it renders" (`browser-verified-web-work` covers that): is it fast and usable
by everyone? Run these when a user-facing surface is about to ship, not on every tweak.

## Performance

- Measure, don't guess: Lighthouse audit or a DevTools performance trace on the
  changed page (throttled, cold load).
- Watch the big three: LCP (hero content < 2.5s), CLS (no layout jank on load),
  INP (interactions respond < 200ms).
- Usual suspects for regressions you just introduced: unoptimized images (size,
  format, `loading="lazy"`), render-blocking scripts, fonts without `font-display`,
  accidental client-side data waterfalls.

## Accessibility

- Keyboard first: tab through the changed UI — everything interactive reachable,
  focus visible, no traps.
- Semantics: real `<button>`/`<a>`/heading hierarchy over div-with-onclick; labels on
  every input; alt text that says what the image is *for*.
- Contrast: text meets 4.5:1 (3:1 for large text). Check disabled/placeholder states.
- Run an automated pass (Lighthouse a11y / axe) — it catches the mechanical 30%;
  the keyboard walk catches what it can't.

## When NOT to Use

Internal tooling nobody outside the team touches (keyboard/contrast still apply —
teammates use keyboards too), API-only changes, prototypes explicitly marked
throwaway.
