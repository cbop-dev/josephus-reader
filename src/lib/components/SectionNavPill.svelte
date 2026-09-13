<script lang="ts">
  import { onDestroy } from 'svelte';
  import { viewMode } from '$lib/stores/readerStore';

  let { sections = [] } = $props<{ sections?: any[] }>();

  let activeIdx = $state(0);
  let observer: IntersectionObserver | null = null;

  function scrollToSection(idx: number) {
    if (idx < 0 || idx >= sections.length) return;
    activeIdx = idx;
    const sec = sections[idx];
    if (!sec) return;
    const el = document.getElementById(`sec-${sec.niese}`);
    if (el) {
      const headerOffset = 80;
      const elementPosition = el.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  }

  function toggleGkEn() {
    const sec = sections[activeIdx];
    if (!sec) return;
    const secEl = document.getElementById(`sec-${sec.niese}`);
    if (!secEl) return;

    const grcEl = secEl.querySelector('.greek-body, .greek-col') as HTMLElement | null;
    const engEl = secEl.querySelector('.english-body, .english-col') as HTMLElement | null;

    if (!grcEl || !engEl) return;

    const headerOffset = 80;
    const grcRect = grcEl.getBoundingClientRect();
    const engRect = engEl.getBoundingClientRect();

    // If English block is closer to top of viewport, scroll to Greek; otherwise scroll to English
    const isEngCurrentlyVisible = Math.abs(engRect.top - headerOffset) < Math.abs(grcRect.top - headerOffset);
    const targetEl = isEngCurrentlyVisible ? grcEl : engEl;

    const elementPosition = targetEl.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }

  function setupObserver() {
    if (observer) observer.disconnect();
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return;

    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            if (id && id.startsWith('sec-')) {
              const nieseStr = id.replace('sec-', '');
              const foundIdx = sections.findIndex((s: any) => s.niese === nieseStr);
              if (foundIdx !== -1) {
                activeIdx = foundIdx;
              }
            }
          }
        }
      },
      {
        root: null,
        rootMargin: '-20% 0px -60% 0px',
        threshold: 0
      }
    );

    sections.forEach((sec: any) => {
      const el = document.getElementById(`sec-${sec.niese}`);
      if (el) observer?.observe(el);
    });
  }

  $effect(() => {
    if (sections.length > 0) {
      setTimeout(() => {
        setupObserver();
      }, 100);
    }
  });

  onDestroy(() => {
    if (observer) observer.disconnect();
  });
</script>

{#if sections && sections.length > 0}
  <div class="section-nav-pill-wrapper">
    <div class="section-nav-pill">
      <!-- First Section -->
      <button
        class="nav-pill-btn"
        disabled={activeIdx === 0}
        onclick={() => scrollToSection(0)}
        title="First Section"
        aria-label="First Section"
      >
        <span class="symbol">|◄</span>
      </button>

      <!-- Previous Section -->
      <button
        class="nav-pill-btn"
        disabled={activeIdx === 0}
        onclick={() => scrollToSection(activeIdx - 1)}
        title="Previous Section"
        aria-label="Previous Section"
      >
        <span class="symbol">◄</span>
      </button>

      <!-- Choose Section Dropdown -->
      <div class="select-container">
        <select
          class="section-select"
          value={activeIdx}
          onchange={(e) => scrollToSection(Number((e.target as HTMLSelectElement).value))}
          aria-label="Choose Section"
        >
          {#each sections as sec, i}
            <option value={i}>
              § {sec.niese}
            </option>
          {/each}
        </select>
      </div>

      <!-- Next Section -->
      <button
        class="nav-pill-btn"
        disabled={activeIdx >= sections.length - 1}
        onclick={() => scrollToSection(activeIdx + 1)}
        title="Next Section"
        aria-label="Next Section"
      >
        <span class="symbol">►</span>
      </button>

      <!-- Last Section -->
      <button
        class="nav-pill-btn"
        disabled={activeIdx >= sections.length - 1}
        onclick={() => scrollToSection(sections.length - 1)}
        title="Last Section"
        aria-label="Last Section"
      >
        <span class="symbol">►|</span>
      </button>

      <!-- Unified Gk/En Toggle Button -->
      <div class="lang-jump-group" class:force-show={$viewMode === 'stacked'}>
        <button
          class="nav-pill-btn lang-btn"
          onclick={toggleGkEn}
          title="Toggle scroll focus between Greek and English text blocks"
        >
          Gk/En
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .section-nav-pill-wrapper {
    position: fixed;
    bottom: 1.25rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 800;
    pointer-events: none;
  }

  .section-nav-pill {
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    background-color: var(--bg-card, #ffffff);
    border: 1px solid var(--border-color, #e0e0e0);
    border-radius: 9999px;
    padding: 0.35rem 0.6rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    color: var(--text-color, #222222);
    transition: all 0.2s ease;
  }

  .nav-pill-btn {
    background: transparent;
    border: none;
    color: var(--text-color, #222222);
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.35rem 0.55rem;
    border-radius: 9999px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.15s ease, opacity 0.15s ease;
  }

  .nav-pill-btn:hover:not(:disabled) {
    background-color: rgba(0, 0, 0, 0.08);
  }

  .nav-pill-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .symbol {
    font-size: 0.8rem;
    line-height: 1;
  }

  .select-container {
    position: relative;
    display: flex;
    align-items: center;
  }

  .section-select {
    background-color: var(--bg-secondary, #f0f0f0);
    color: var(--text-color, #222222);
    border: 1px solid var(--border-color, #cccccc);
    border-radius: 9999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    outline: none;
    transition: border-color 0.15s ease;
  }

  .section-select:focus {
    border-color: var(--accent-color, #4a6fa5);
  }

  .lang-jump-group {
    display: none;
    align-items: center;
    padding-left: 0.3rem;
    border-left: 1px solid var(--border-color, #e0e0e0);
  }

  .lang-jump-group.force-show {
    display: flex;
  }

  .lang-btn {
    font-size: 0.85rem;
    font-weight: 700;
    padding: 0.25rem 0.6rem;
    background-color: var(--bg-secondary, #f0f0f0);
    border: 1px solid var(--border-color, #d0d0d0);
  }

  .lang-btn:hover {
    background-color: var(--accent-color, #4a6fa5);
    color: #ffffff;
    border-color: var(--accent-color, #4a6fa5);
  }

  @media (max-width: 768px) {
    .lang-jump-group {
      display: flex;
    }
  }
</style>
