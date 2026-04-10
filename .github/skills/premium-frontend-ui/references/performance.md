# Performance Imperative

A beautiful site that stutters is a failure. Enforce these guardrails in all generated code.

## Hardware Acceleration

Only animate properties that do **not** trigger layout recalculations:

| Safe to Animate | Never Animate |
|----------------|---------------|
| `transform` | `width` / `height` |
| `opacity` | `top` / `left` / `right` / `bottom` |
| `filter` | `margin` / `padding` |
| `clip-path` | `border-width` |

## Render Optimization

Apply `will-change` intelligently on complex moving elements, but remove it post-animation to conserve memory.

```js
// Apply before animation
element.style.willChange = 'transform';

// Animate...
element.addEventListener('transitionend', () => {
  element.style.willChange = 'auto';
});
```

## Responsive Degradation

Wrap custom cursor logic and heavy hover animations in media queries to ensure performance on touch devices.

```css
@media (hover: hover) and (pointer: fine) {
  .custom-cursor { display: block; }
  .magnetic-btn:hover { /* magnetic effect */ }
}

@media (hover: none) {
  .custom-cursor { display: none; }
}
```

## Accessibility

Wrap heavy continuous animations in a motion preference query. Never sacrifice accessibility for aesthetics.

```css
@media (prefers-reduced-motion: no-preference) {
  .hero-element {
    animation: float 6s ease-in-out infinite;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Loading Strategy

- Lazy-load images below the fold with `loading="lazy"`.
- Preload critical fonts with `<link rel="preload" as="font" crossorigin>`.
- Use `font-display: swap` to prevent invisible text during font loading.
- Defer non-critical JS with `defer` or dynamic `import()`.
