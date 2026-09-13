<script lang="ts">
  import {
    currentWork,
    currentBook,
    viewMode,
    theme,
    morphEnabled,
    showPdfModal,
    showAttributionModal,
    type WorkId,
  } from "$lib/stores/readerStore";

  let { manifest = [] } = $props<{ manifest?: any[] }>();

  let selectedWorkMeta = $derived(
    manifest.find((w: any) => w.id === $currentWork) || manifest[0],
  );
  let numBooks = $derived(selectedWorkMeta?.books?.length || 1);

  function setWork(id: WorkId) {
    $currentWork = id;
    $currentBook = 1;
  }

  function setBook(b: number) {
    $currentBook = b;
  }

  function cycleTheme() {
    if ($theme === "sepia") $theme = "dark";
    else if ($theme === "dark") $theme = "light";
    else $theme = "sepia";
    document.documentElement.setAttribute("data-theme", $theme);
  }
</script>

<header class="header">
  <div class="top-row">
    <div class="brand">
      <h1 class="logo-title">JOSEPHUS</h1>
      <span class="sub-title">Greek & English Reader</span>
    </div>

    <!-- Controls Toolbar -->
    <div class="toolbar">
      <!-- Work Selector -->
      <select
        class="nav-select work-select"
        value={$currentWork}
        onchange={(e) =>
          setWork((e.target as HTMLSelectElement).value as WorkId)}
      >
        <option value="antiquities">Jewish Antiquities (20 Books)</option>
        <option value="war">The Jewish War (7 Books)</option>
        <option value="life">Life of Josephus (1 Book)</option>
        <option value="apion">Against Apion (2 Books)</option>
      </select>

      <!-- Book Selector -->
      <select
        class="nav-select book-select"
        value={$currentBook}
        onchange={(e) => setBook(Number((e.target as HTMLSelectElement).value))}
      >
        {#each Array(numBooks) as _, i}
          <option value={i + 1}>Book {i + 1}</option>
        {/each}
      </select>

      <!-- View Mode Buttons -->
      <div class="button-group mode-group">
        <button
          class="btn mode-btn"
          class:active={$viewMode === "parallel"}
          onclick={() => ($viewMode = "parallel")}
          title="Side-by-Side Facing Columns"
        >
          <svg
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <rect x="3" y="3" width="8" height="18" rx="1" />
            <rect x="13" y="3" width="8" height="18" rx="1" />
          </svg>
          <span class="btn-label">Parallel</span>
        </button>

        <button
          class="btn mode-btn"
          class:active={$viewMode === "greek"}
          onclick={() => ($viewMode = "greek")}
          title="Greek Text Only"
        >
          <span class="greek-sym">Ω</span>
          <span class="btn-label">Greek</span>
        </button>

        <button
          class="btn mode-btn"
          class:active={$viewMode === "english"}
          onclick={() => ($viewMode = "english")}
          title="English Text Only"
        >
          <span class="eng-sym">EN</span>
          <span class="btn-label">English</span>
        </button>

        <button
          class="btn mode-btn"
          class:active={$viewMode === "stacked"}
          onclick={() => ($viewMode = "stacked")}
          title="Stacked Verse-by-Verse"
        >
          <svg
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
          <span class="btn-label">Stacked</span>
        </button>
      </div>

      <!-- Morphology Toggle -->
      <button
        class="btn toggle-btn"
        class:active={$morphEnabled}
        onclick={() => ($morphEnabled = !$morphEnabled)}
        title="Toggle Greek Word Morph & Lemma Parsing"
      >
        <span class="icon-tag">Morph</span>
        <span class="status-badge" class:on={$morphEnabled}>
          {$morphEnabled ? "ON" : "OFF"}
        </span>
      </button>

      <!-- Theme Switcher -->
      <button
        class="btn icon-btn"
        onclick={cycleTheme}
        title="Switch Theme (Sepia / Dark / Light)"
      >
        {#if $theme === "sepia"}
          <span class="theme-icon">📜</span>
        {:else if $theme === "dark"}
          <span class="theme-icon">🌙</span>
        {:else}
          <span class="theme-icon">☀️</span>
        {/if}
      </button>

      <!-- PDF Export Button -->
      <button
        class="btn primary-btn pdf-btn"
        onclick={() => ($showPdfModal = true)}
        title="Generate Facing-Page Printable PDF"
      >
        <svg
          class="icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M6 9V2h12v7" />
          <path
            d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"
          />
          <path d="M6 14h12v8H6z" />
        </svg>
        <span>PDF</span>
      </button>

      <!-- Source Data & License Attribution Button -->
      <button
        class="btn icon-btn info-btn"
        onclick={() => ($showAttributionModal = true)}
        title="Source Data & License Attribution (CC BY-SA 4.0)"
        aria-label="Source Data and License Info"
      >
        <span class="info-sym">🛈</span>
      </button>
    </div>
  </div>
</header>

<style>
  .header {
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    padding: 0.75rem 1.5rem;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: var(--shadow-sm);
  }

  .top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .brand {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }

  .logo-title {
    font-family: var(--font-sans);
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: var(--accent-color);
  }

  .sub-title {
    font-family: var(--font-sans);
    font-size: 0.85rem;
    color: var(--text-muted);
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .nav-select {
    background-color: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 0.4rem 0.75rem;
    font-family: var(--font-sans);
    font-size: 0.9rem;
    font-weight: 500;
    outline: none;
    transition: border-color 0.2s;
  }

  .nav-select:focus {
    border-color: var(--accent-color);
  }

  .button-group {
    display: flex;
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 2px;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-secondary);
    transition: all 0.15s ease;
  }

  .btn:hover {
    color: var(--text-primary);
    background-color: var(--bg-secondary);
  }

  .btn.active {
    background-color: var(--accent-color);
    color: #ffffff;
  }

  .icon {
    width: 16px;
    height: 16px;
  }

  .status-badge {
    font-size: 0.7rem;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    background-color: var(--bg-secondary);
    color: var(--text-muted);
  }

  .status-badge.on {
    background-color: var(--accent-light);
    color: var(--accent-color);
    font-weight: 700;
  }

  .primary-btn {
    background-color: var(--accent-color);
    color: #ffffff;
    border-radius: 6px;
    font-weight: 600;
    padding: 0.45rem 0.9rem;
  }

  .primary-btn:hover {
    background-color: var(--accent-hover);
    color: #ffffff;
  }

  @media (max-width: 768px) {
    .header {
      padding: 0.5rem 0.75rem;
    }
    .btn-label {
      display: none;
    }
    .sub-title {
      display: none;
    }
  }
</style>
