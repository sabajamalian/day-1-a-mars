# Motion Design System

Animation is the connective tissue of a premium site. Always implement these motion principles.

## Scroll-Driven Narratives

Use modern scroll libraries (GSAP ScrollTrigger) to tie animations to user progress.

### Pinned Containers

Lock sections into the viewport while secondary content flows past or reveals itself.

```js
gsap.to('.panel', {
  scrollTrigger: {
    trigger: '.panel-wrapper',
    start: 'top top',
    end: '+=200%',
    pin: true,
    scrub: 1,
  },
  x: '-100%',
});
```

### Horizontal Journeys

Translate vertical scroll data into horizontal movement for galleries or showcases.

```js
const sections = gsap.utils.toArray('.horizontal-section');
gsap.to(sections, {
  xPercent: -100 * (sections.length - 1),
  ease: 'none',
  scrollTrigger: {
    trigger: '.horizontal-wrapper',
    pin: true,
    scrub: 1,
    end: () => `+=${document.querySelector('.horizontal-wrapper').offsetWidth}`,
  },
});
```

### Parallax Mapping

Assign varying scroll-speeds to background, midground, and foreground elements.

```js
gsap.to('.bg-layer', { y: '-30%', scrollTrigger: { scrub: true } });
gsap.to('.mid-layer', { y: '-15%', scrollTrigger: { scrub: true } });
gsap.to('.fg-layer', { y: '-5%', scrollTrigger: { scrub: true } });
```

## High-Fidelity Micro-Interactions

The cursor is the user's avatar. Build interactions around it.

### Magnetic Components

Calculate distance between the mouse pointer and a button, pulling the button towards the cursor.

```js
const magneticBtn = document.querySelector('.magnetic');
magneticBtn.addEventListener('mousemove', (e) => {
  const rect = magneticBtn.getBoundingClientRect();
  const x = e.clientX - rect.left - rect.width / 2;
  const y = e.clientY - rect.top - rect.height / 2;
  magneticBtn.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;
});
magneticBtn.addEventListener('mouseleave', () => {
  magneticBtn.style.transform = 'translate(0, 0)';
});
```

### Custom Tracking Cursor

Follow the mouse with calculated interpolation (lerp) for a smooth drag effect.

```js
const cursor = document.querySelector('.custom-cursor');
let mouseX = 0, mouseY = 0, cursorX = 0, cursorY = 0;

document.addEventListener('mousemove', (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;
});

function animate() {
  cursorX += (mouseX - cursorX) * 0.1;
  cursorY += (mouseY - cursorY) * 0.1;
  cursor.style.transform = `translate(${cursorX}px, ${cursorY}px)`;
  requestAnimationFrame(animate);
}
animate();
```

### Dimensional Hover States

Use CSS Transforms to give interactive elements weight and tactile feedback.

```css
.card {
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.card:hover {
  transform: scale(1.03) rotateX(2deg) translateY(-4px);
}
```
