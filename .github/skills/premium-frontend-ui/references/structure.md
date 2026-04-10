# Structural Requirements for Immersive UI

## The Entry Sequence (Preloading & Initialization)

A blank screen is unacceptable. The user's first interaction must set expectations.

- Generate a lightweight preloader component that handles asset resolution (fonts, initial images, 3D models).
- Transition the preloader away fluidly — split-door reveal, scale-up zoom, or staggered text sweep.

```css
/* Example: scale-up preloader exit */
.preloader {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: grid;
  place-items: center;
  background: var(--bg);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.preloader.loaded {
  opacity: 0;
  transform: scale(1.05);
  pointer-events: none;
}
```

## The Hero Architecture

The top fold must command attention immediately.

- **Full-bleed containers**: Use `100vh` / `100dvh` with overflow hidden.
- **Typography Engine**: Break headlines into `<span>` elements by word or character for cascading entrance animations.
- **Depth**: Use subtle floating elements or background `clip-path` to create scale and depth behind primary copy.

```html
<!-- Syntactically split headline for animation -->
<h1 class="hero-headline">
  <span class="word"><span class="char">I</span><span class="char">m</span><span class="char">m</span><span class="char">e</span><span class="char">r</span><span class="char">s</span><span class="char">e</span></span>
</h1>
```

## Fluid & Contextual Navigation

- **Sticky + reactive**: Headers that hide on scroll-down, reveal on scroll-up.
- **Rich hover states**: Mega-menus that display image previews of the hovered link.
- Never generate a standard static navbar for premium contexts.

```js
// Scroll-direction-aware sticky header
let lastScroll = 0;
window.addEventListener('scroll', () => {
  const currentScroll = window.scrollY;
  const header = document.querySelector('.site-header');
  header.classList.toggle('hidden', currentScroll > lastScroll && currentScroll > 100);
  lastScroll = currentScroll;
});
```
