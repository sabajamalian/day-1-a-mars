# Typography & Visual Texture

## Type Hierarchy

Enforce massive contrast in scale between headlines and body copy.

- **Headlines**: Use extreme sizing via `clamp()` spanning up to `12vw`.
- **Body copy**: Minimum `16px–18px` for crisp readability.

```css
.headline {
  font-size: clamp(2.5rem, 8vw + 1rem, 12vw);
  line-height: 0.95;
  letter-spacing: -0.03em;
  font-weight: 800;
}

.body {
  font-size: clamp(1rem, 0.5vw + 0.875rem, 1.125rem);
  line-height: 1.6;
  max-width: 65ch;
}
```

## Font Selection

Always implement highly specified variable fonts or premium typefaces over system defaults.

Recommended pairings:
- **Display**: Inter Variable, Satoshi, General Sans, ClashDisplay
- **Body**: Instrument Sans, Plus Jakarta Sans, DM Sans
- **Monospace**: JetBrains Mono, Berkeley Mono, Fira Code

```css
@font-face {
  font-family: 'Satoshi';
  src: url('/fonts/Satoshi-Variable.woff2') format('woff2');
  font-weight: 300 900;
  font-display: swap;
}
```

## Atmospheric Filters

Remove digital sterility by adding photographic grain and glass depth.

### Noise Overlay

```css
.noise-overlay {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9998;
  background-image: url('/textures/noise.svg');
  mix-blend-mode: overlay;
  opacity: 0.035;
}
```

### Frosted Glass

```css
.glass-panel {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
}
```
