/* ==========================================================================
   Serious Outcome Prediction — App Logic
   ========================================================================== */

(function () {
  'use strict';

  // ========================================================================
  // PRELOADER
  // ========================================================================
  const preloader = document.getElementById('preloader');
  const preloaderBar = document.getElementById('preloaderBar');
  let progress = 0;

  const preloadInterval = setInterval(() => {
    progress += Math.random() * 15 + 5;
    if (progress >= 100) progress = 100;
    preloaderBar.style.width = progress + '%';
    if (progress >= 100) {
      clearInterval(preloadInterval);
      setTimeout(() => {
        preloader.classList.add('loaded');
        setTimeout(initAnimations, 400);
      }, 400);
    }
  }, 200);

  // ========================================================================
  // CUSTOM CURSOR
  // ========================================================================
  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    const cursor = document.getElementById('cursor');
    const follower = document.getElementById('cursorFollower');
    let mouseX = 0, mouseY = 0, followerX = 0, followerY = 0;

    document.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      cursor.style.transform = `translate(${mouseX}px, ${mouseY}px) translate(-50%, -50%)`;
    });

    function animateCursor() {
      followerX += (mouseX - followerX) * 0.12;
      followerY += (mouseY - followerY) * 0.12;
      follower.style.transform = `translate(${followerX}px, ${followerY}px) translate(-50%, -50%)`;
      requestAnimationFrame(animateCursor);
    }
    animateCursor();

    // Magnetic buttons
    document.querySelectorAll('.magnetic').forEach((btn) => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform = `translate(${x * 0.25}px, ${y * 0.25}px)`;
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'translate(0, 0)';
      });
    });
  }

  // ========================================================================
  // SCROLL-AWARE HEADER
  // ========================================================================
  const header = document.getElementById('siteHeader');
  let lastScroll = 0;

  window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;
    header.classList.toggle('scrolled', currentScroll > 50);
    header.classList.toggle('hidden', currentScroll > lastScroll && currentScroll > 200);
    lastScroll = currentScroll;
  }, { passive: true });

  // ========================================================================
  // GSAP ANIMATIONS
  // ========================================================================
  function initAnimations() {
    if (typeof gsap === 'undefined') return;

    gsap.registerPlugin(ScrollTrigger);

    // Hero entrance sequence
    const heroTl = gsap.timeline({ defaults: { ease: 'expo.out' } });

    heroTl
      .to('.hero__badge', { opacity: 1, y: 0, duration: 0.8 })
      .to('.hero__headline .word', {
        opacity: 1, y: 0, rotateX: 0,
        stagger: 0.12, duration: 1
      }, '-=0.4')
      .to('.hero__sub', { opacity: 1, y: 0, duration: 0.8 }, '-=0.5')
      .to('.hero__actions', { opacity: 1, y: 0, duration: 0.8 }, '-=0.5')
      .to('.hero__stats', { opacity: 1, y: 0, duration: 0.8 }, '-=0.4')
      .to('.hero__scroll-indicator', { opacity: 0.5, duration: 1 }, '-=0.3');

    // Animate stat counters
    document.querySelectorAll('.hero__stat-value').forEach((el) => {
      const target = el.dataset.count ? parseInt(el.dataset.count) : null;
      const decimal = el.dataset.decimal ? parseFloat(el.dataset.decimal) : null;
      const suffix = el.dataset.suffix || '';

      if (target) {
        gsap.to(el, {
          innerText: target,
          duration: 2,
          ease: 'power2.out',
          snap: { innerText: 1 },
          onUpdate() {
            el.textContent = Math.floor(parseFloat(el.innerText)).toLocaleString() + suffix;
          }
        });
      } else if (decimal !== null) {
        const counter = { val: 0 };
        gsap.to(counter, {
          val: decimal,
          duration: 2,
          ease: 'power2.out',
          onUpdate() {
            el.textContent = counter.val.toFixed(2);
          }
        });
      }
    });

    // Reveal elements on scroll
    document.querySelectorAll('[data-reveal]').forEach((el, i) => {
      gsap.to(el, {
        scrollTrigger: {
          trigger: el,
          start: 'top 85%',
          toggleActions: 'play none none none',
        },
        opacity: 1,
        y: 0,
        duration: 0.9,
        delay: (i % 4) * 0.1,
        ease: 'expo.out',
      });
    });

    // Metric bar fills
    document.querySelectorAll('.metric-card__bar-fill').forEach((bar) => {
      const targetWidth = bar.dataset.width;
      ScrollTrigger.create({
        trigger: bar,
        start: 'top 90%',
        onEnter: () => { bar.style.width = targetWidth + '%'; },
      });
    });

    // Animate metric values
    document.querySelectorAll('.metric-card__value').forEach((el) => {
      const decimal = el.dataset.decimal ? parseFloat(el.dataset.decimal) : null;
      if (decimal !== null) {
        const counter = { val: 0 };
        ScrollTrigger.create({
          trigger: el,
          start: 'top 85%',
          onEnter: () => {
            gsap.to(counter, {
              val: decimal,
              duration: 1.5,
              ease: 'power2.out',
              onUpdate() {
                el.textContent = counter.val.toFixed(3);
              }
            });
          }
        });
      }
    });

    // Parallax on hero grid
    gsap.to('.hero__grid-bg', {
      y: '-20%',
      scrollTrigger: { trigger: '.hero', scrub: true },
    });

    gsap.to('.hero__radial', {
      y: '-30%',
      scrollTrigger: { trigger: '.hero', scrub: true },
    });
  }

  // ========================================================================
  // CHARTS (Chart.js)
  // ========================================================================
  function initCharts() {
    if (typeof Chart === 'undefined') return;

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";

    // ROC Curve
    const rocCtx = document.getElementById('rocChart');
    if (rocCtx) {
      // Simulated ROC curve data points
      const fpr = [0, 0.02, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.45, 0.55, 0.65, 0.78, 0.88, 0.95, 1.0];
      const tprXgb = [0, 0.15, 0.35, 0.48, 0.58, 0.68, 0.76, 0.84, 0.89, 0.93, 0.96, 0.98, 0.99, 1.0, 1.0];
      const tprLr = [0, 0.10, 0.28, 0.40, 0.52, 0.62, 0.71, 0.79, 0.85, 0.90, 0.94, 0.97, 0.99, 1.0, 1.0];

      new Chart(rocCtx, {
        type: 'line',
        data: {
          labels: fpr,
          datasets: [
            {
              label: 'XGBoost (AUC=0.834)',
              data: tprXgb,
              borderColor: '#00f0ff',
              backgroundColor: 'rgba(0, 240, 255, 0.05)',
              fill: true,
              tension: 0.4,
              pointRadius: 0,
              borderWidth: 2,
            },
            {
              label: 'Logistic Regression (AUC=0.809)',
              data: tprLr,
              borderColor: '#e879f9',
              backgroundColor: 'rgba(232, 121, 249, 0.05)',
              fill: true,
              tension: 0.4,
              pointRadius: 0,
              borderWidth: 2,
            },
            {
              label: 'Random (AUC=0.5)',
              data: fpr,
              borderColor: 'rgba(255,255,255,0.15)',
              borderDash: [6, 4],
              pointRadius: 0,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { padding: 20, usePointStyle: true, pointStyleWidth: 10 } },
          },
          scales: {
            x: { title: { display: true, text: 'False Positive Rate' }, grid: { color: 'rgba(255,255,255,0.03)' } },
            y: { title: { display: true, text: 'True Positive Rate' }, grid: { color: 'rgba(255,255,255,0.03)' } },
          },
        },
      });
    }

    // Confusion Matrix (heatmap via bar chart)
    const confCtx = document.getElementById('confusionChart');
    if (confCtx) {
      new Chart(confCtx, {
        type: 'bar',
        data: {
          labels: ['True Negative', 'False Positive', 'False Negative', 'True Positive'],
          datasets: [{
            label: 'Count',
            data: [12845, 1420, 2650, 1242],
            backgroundColor: [
              'rgba(0, 240, 255, 0.7)',
              'rgba(248, 113, 113, 0.5)',
              'rgba(251, 191, 36, 0.5)',
              'rgba(52, 211, 153, 0.7)',
            ],
            borderColor: [
              'rgba(0, 240, 255, 0.9)',
              'rgba(248, 113, 113, 0.7)',
              'rgba(251, 191, 36, 0.7)',
              'rgba(52, 211, 153, 0.9)',
            ],
            borderWidth: 1,
            borderRadius: 6,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
          },
          scales: {
            x: { grid: { display: false } },
            y: {
              title: { display: true, text: 'Count' },
              grid: { color: 'rgba(255,255,255,0.03)' },
            },
          },
        },
      });
    }

    // Target Distribution
    const targetCtx = document.getElementById('targetChart');
    if (targetCtx) {
      new Chart(targetCtx, {
        type: 'doughnut',
        data: {
          labels: ['Non-Serious', 'Hospitalized', 'Life-Threatening', 'Death'],
          datasets: [{
            data: [71230, 14200, 3600, 1756],
            backgroundColor: [
              'rgba(148, 163, 184, 0.6)',
              'rgba(0, 240, 255, 0.7)',
              'rgba(251, 191, 36, 0.7)',
              'rgba(248, 113, 113, 0.7)',
            ],
            borderColor: 'rgba(6, 8, 13, 0.8)',
            borderWidth: 3,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '55%',
          plugins: {
            legend: { position: 'bottom', labels: { padding: 20, usePointStyle: true, pointStyleWidth: 10 } },
          },
        },
      });
    }

    // Feature Importance
    const featCtx = document.getElementById('featureChart');
    if (featCtx) {
      const featureLabels = [
        'tfidf_hospitalisation', 'tfidf_death', 'tfidf_dyspnoea',
        'tfidf_cardiac', 'age_years', 'tfidf_pain', 'tfidf_nausea',
        'tfidf_vomiting', 'tfidf_dizziness', 'industry_Dietary Supp.',
        'tfidf_pyrexia', 'tfidf_fatigue', 'gender_female', 'tfidf_rash',
        'tfidf_seizure'
      ];
      const featureValues = [
        0.142, 0.118, 0.089, 0.072, 0.065, 0.058, 0.052, 0.047,
        0.041, 0.038, 0.035, 0.031, 0.028, 0.025, 0.022
      ];

      new Chart(featCtx, {
        type: 'bar',
        data: {
          labels: featureLabels,
          datasets: [{
            label: 'Feature Importance (Gain)',
            data: featureValues,
            backgroundColor: featureLabels.map((_, i) => {
              if (i < 4) return 'rgba(0, 240, 255, 0.7)';
              if (i < 9) return 'rgba(0, 240, 255, 0.45)';
              return 'rgba(0, 240, 255, 0.25)';
            }),
            borderColor: 'rgba(0, 240, 255, 0.8)',
            borderWidth: 1,
            borderRadius: 4,
          }],
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
          },
          scales: {
            x: {
              title: { display: true, text: 'Importance (Gain)' },
              grid: { color: 'rgba(255,255,255,0.03)' },
            },
            y: {
              grid: { display: false },
              ticks: {
                font: { family: "'JetBrains Mono', monospace", size: 11 },
              },
            },
          },
        },
      });
    }
  }

  // Init charts when Chart.js is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(initCharts, 1200));
  } else {
    setTimeout(initCharts, 1200);
  }

  // ========================================================================
  // PREDICTION FORM — calls real model API
  // ========================================================================
  const API_BASE = 'http://127.0.0.1:5001';
  const form = document.getElementById('predictForm');
  const resultPlaceholder = document.getElementById('resultPlaceholder');
  const resultData = document.getElementById('resultData');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const age = parseFloat(document.getElementById('age').value) || null;
    const gender = document.getElementById('gender').value;
    const industry = document.getElementById('industry').value;
    const symptoms = document.getElementById('symptoms').value;
    const selectedModel = document.getElementById('model').value;

    if (!symptoms.trim()) {
      alert('Please enter at least one symptom.');
      return;
    }

    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnHTML = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Running inference…</span>';

    try {
      const response = await fetch(`${API_BASE}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ age, gender, symptoms, industry }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || `API error ${response.status}`);
      }

      const result = await response.json();

      // Pick the selected model's result
      const modelResult = selectedModel === 'xgboost' ? result.xgboost : result.logistic_regression;
      const otherResult = selectedModel === 'xgboost' ? result.logistic_regression : result.xgboost;
      const score = modelResult.probability;

      // Show result
      resultPlaceholder.style.display = 'none';
      resultData.style.display = 'block';

      // Animate ring
      const ringFill = document.getElementById('ringFill');
      const ringPct = document.getElementById('ringPct');
      const circumference = 326.73;
      const offset = circumference * (1 - score);
      ringFill.style.strokeDashoffset = offset;
      ringPct.textContent = Math.round(score * 100) + '%';

      // Color based on severity
      let ringColor;
      if (score >= 0.6) {
        ringColor = '#f87171';
      } else if (score >= 0.35) {
        ringColor = '#fbbf24';
      } else {
        ringColor = '#34d399';
      }
      ringFill.style.stroke = ringColor;
      ringPct.style.color = ringColor;

      // Verdict
      const verdictLabel = document.getElementById('verdictLabel');
      const verdictDetail = document.getElementById('verdictDetail');
      const modelName = selectedModel === 'xgboost' ? 'XGBoost' : 'Logistic Regression';
      const otherName = selectedModel === 'xgboost' ? 'Logistic Regression' : 'XGBoost';

      if (score >= 0.5) {
        verdictLabel.textContent = 'Serious Outcome Predicted';
        verdictLabel.style.color = '#f87171';
        verdictDetail.textContent = `${modelName} predicts ${(score * 100).toFixed(1)}% probability of serious outcome. ${otherName} gives ${(otherResult.probability * 100).toFixed(1)}%.`;
      } else if (score >= 0.3) {
        verdictLabel.textContent = 'Borderline Risk';
        verdictLabel.style.color = '#fbbf24';
        verdictDetail.textContent = `${modelName} predicts ${(score * 100).toFixed(1)}% probability. ${otherName} gives ${(otherResult.probability * 100).toFixed(1)}%. Near the decision boundary.`;
      } else {
        verdictLabel.textContent = 'Non-Serious Predicted';
        verdictLabel.style.color = '#34d399';
        verdictDetail.textContent = `${modelName} predicts ${(score * 100).toFixed(1)}% probability of serious outcome. ${otherName} gives ${(otherResult.probability * 100).toFixed(1)}%.`;
      }

      // Feature contributions from real model
      const factorsEl = document.getElementById('resultFactors');
      if (result.top_features && result.top_features.length > 0) {
        const maxContrib = Math.max(...result.top_features.map(f => Math.abs(f.contribution)));
        factorsEl.innerHTML = result.top_features.map((f) => {
          const pct = (Math.abs(f.contribution) / maxContrib * 100).toFixed(1);
          const color = f.contribution > 0 ? '#00f0ff' : '#94a3b8';
          const displayName = f.feature.replace('tfidf_', '').replace('industry_x0_', 'industry: ');
          return `
            <div class="result__factor">
              <span class="result__factor-label">${displayName}</span>
              <div class="result__factor-bar">
                <div class="result__factor-bar-fill" style="width:${pct}%;background:${color}"></div>
              </div>
              <span class="result__factor-value">${f.importance.toFixed(3)}</span>
            </div>
          `;
        }).join('');
      } else {
        factorsEl.innerHTML = '<p style="color:var(--text-dim);font-size:0.85rem;">No significant feature contributions detected.</p>';
      }

    } catch (err) {
      resultPlaceholder.style.display = 'none';
      resultData.style.display = 'block';
      resultData.innerHTML = `
        <div style="text-align:center;padding:2rem;">
          <p style="color:#f87171;font-size:1.1rem;font-weight:600;margin-bottom:0.75rem;">API Connection Failed</p>
          <p style="color:var(--text-muted);font-size:0.85rem;max-width:320px;margin:0 auto;line-height:1.6;">
            ${err.message}<br><br>
            Make sure the API server is running:<br>
            <code style="font-size:0.8rem;">python3 api.py</code>
          </p>
        </div>
      `;
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHTML;
    }
  });

  // ========================================================================
  // SMOOTH SCROLL for anchor links
  // ========================================================================
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

})();
