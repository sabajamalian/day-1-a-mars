---
name: premium-frontend-ui
description: "Build premium, immersive frontend web experiences. Use when: creating Awwwards-style landing pages, interactive portfolios, cinematic hero sections, scroll-driven animations, magnetic buttons, custom cursors, glassmorphism, premium typography, or any request for high-end visual polish and motion design."
argument-hint: "Describe the page or component you want to build"
---

# Premium Frontend UI Craftsmanship

Build immersive, award-level web experiences with advanced motion, typography, and performance.

## When to Use

- "Build a modern UI for this model"
- "Build a premium landing page"
- "Create an Awwwards-style component"
- "Design an immersive UI"
- "Build a frontend for this ML solution"
- Requests for scroll-driven animations, cinematic hero sections, interactive portfolios
- Any frontend task requiring top-tier visual polish
- UI that needs to interact with a trained model (prediction forms, inference demos)

## Procedure

### 1. Establish Creative Direction

Before writing layout code, identify the emotional tone. Commit to one of these identities:

| Identity | Key Traits |
|----------|------------|
| **Editorial Brutalism** | High-contrast monochrome, oversized type, sharp edges, raw grids |
| **Organic Fluidity** | Soft gradients, deep radii, glassmorphism, spring physics |
| **Cyber / Technical** | Dark mode, neon accents, monospaced type, staggered reveals |
| **Cinematic Pacing** | Full-viewport imagery, slow cross-fades, negative space, scroll storytelling |

If the user hasn't specified a direction, ask before proceeding.

### 2. Scaffold the Architecture

Build these layers into every page. See [structural requirements](./references/structure.md) for implementation details.

1. **Entry Sequence** — Preloader with fluid exit animation (split-door, scale-up, text sweep). Never show a blank screen.
2. **Hero Architecture** — Full-bleed `100dvh` container, syntactically split headlines (`<span>` per word/char) for cascading entrance animations, depth via floating elements or clipping paths.
3. **Fluid Navigation** — Sticky header that hides on scroll-down, reveals on scroll-up. Rich hover states (mega-menus with image previews).

### 3. Implement the Motion System

Animation is connective tissue, not decoration. See [motion design reference](./references/motion.md).

- **Scroll-Driven Narratives**: Use GSAP ScrollTrigger — pinned containers, horizontal scroll journeys, parallax mapping with varying speeds.
- **Micro-Interactions**: Magnetic buttons (distance-based pull), custom cursor with lerp interpolation, dimensional hover states (`scale`, `rotateX`, `translate3d`).

### 4. Apply Typography & Visual Texture

See [typography reference](./references/typography.md).

- **Type Hierarchy**: Extreme scale contrast — headlines via `clamp()` up to `12vw`, body at `16px–18px` min.
- **Font Selection**: Use variable fonts or premium typefaces, never system defaults.
- **Atmospheric Filters**: CSS/SVG noise overlays (`mix-blend-mode: overlay`, opacity `0.02–0.05`), `backdrop-filter: blur()` with semi-transparent borders.

### 5. Enforce Performance Guardrails

Every generated line must meet these constraints. See [performance reference](./references/performance.md).

- **Only animate** `transform` and `opacity` — never `width`, `height`, `top`, `margin`.
- **Use** `will-change: transform` on complex moving elements; remove post-animation.
- **Wrap** custom cursor / heavy hover logic in `@media (hover: hover) and (pointer: fine)`.
- **Wrap** continuous animations in `@media (prefers-reduced-motion: no-preference)`.

### 6. Connect to ML Models (When Applicable)

If the UI interacts with a trained model (e.g. prediction forms, inference demos), **always create a Flask API backend** to serve real model predictions. Never fake model outputs with hardcoded heuristics. See [model integration reference](./references/model-integration.md).

**When this applies**: Any UI that includes prediction forms, inference demos, model playgrounds, or interactive features that reference a trained model in the codebase.

**Required steps**:

1. **Save model artifacts** — Update the model's training script to export: serialized model (pickle), fitted preprocessors (TF-IDF vectorizers, encoders, scalers), and a `metadata.json` with feature names, categories, and evaluation metrics.
2. **Create a Flask API** (`api.py`) that loads artifacts at startup and exposes `POST /api/predict` with identical feature engineering to training. Include `flask-cors` for cross-origin requests from the static frontend.
3. **Wire the frontend** — The prediction form must `fetch()` the API endpoint, show a loading state during inference, display real model probabilities, and render actual feature contributions. Include a clear error state with startup instructions if the API is unreachable.
4. **Expose a metadata endpoint** — `GET /api/metadata` returns model details (feature count, categories, AUC scores) so the frontend can populate dropdowns and display metrics dynamically.

**Key rules**:
- Feature engineering at inference must exactly mirror training (same vectorizer, same encoder, same normalization logic).
- The API must validate inputs and return structured JSON with probabilities from `predict_proba()`, not just class labels.
- The frontend must gracefully degrade if the API is not running — show connection error with the command to start the server.

### 7. Select Implementation Stack

| Target | Libraries |
|--------|-----------|
| **React / Next.js** | Framer Motion (layout transitions, springs), Lenis (`@studio-freight/lenis`) for smooth scroll, React Three Fiber for WebGL/3D |
| **Vanilla / HTML / Astro** | GSAP (timeline sequencing), Lenis via CDN (scroll smoothing), SplitType (typography chunking) |
| **Model API** | Flask + flask-cors, pickle for artifact loading, scipy/sklearn/xgboost for inference |

### 8. Final Checklist

- [ ] Scroll-smoothed architecture wraps the output
- [ ] CSS uses only composited-layer animations
- [ ] Sweeping, staggered component entrances
- [ ] Fluid typographic scale
- [ ] Intentional, memorable aesthetic footprint
- [ ] Accessibility: `prefers-reduced-motion` respected, semantic HTML, sufficient contrast
- [ ] If model-backed: Flask API created with real inference, frontend calls API (no hardcoded heuristics), error state shown when API is down
