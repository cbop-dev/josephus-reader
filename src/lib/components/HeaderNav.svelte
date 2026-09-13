<script lang="ts">
  import {
    currentWork,
    currentBook,
    viewMode,
    theme,
    morphEnabled,
    fontSize,
    showPdfModal,
    showAttributionModal,
    type WorkId,
    type Theme,
  } from "$lib/stores/readerStore";

  let { manifest = [] } = $props<{ manifest?: any[] }>();

  let isMobileMenuOpen = $state(false);
  let isThemeMenuOpen = $state(false);

  let selectedWorkMeta = $derived(
    manifest.find((w: any) => w.id === $currentWork) || manifest[0],
  );
  let numBooks = $derived(selectedWorkMeta?.books?.length || 1);

  function setWork(id: WorkId) {
    $currentWork = id;
    $currentBook = 1;
    isMobileMenuOpen = false;
  }

  function setBook(b: number) {
    $currentBook = b;
    isMobileMenuOpen = false;
  }

  function selectTheme(t: Theme) {
    $theme = t;
    document.documentElement.setAttribute("data-theme", t);
    isThemeMenuOpen = false;
  }

  function closeThemeMenu() {
    isThemeMenuOpen = false;
  }

  function decreaseFontSize() {
    $fontSize = Math.max(13, $fontSize - 2);
  }

  function increaseFontSize() {
    $fontSize = Math.min(27, $fontSize + 2);
  }

  function toggleMobileMenu() {
    isMobileMenuOpen = !isMobileMenuOpen;
  }
</script>

<svelte:window onclick={closeThemeMenu} />

<header class="header">
  <div class="top-row">
    <div class="header-main-bar">
      <div class="brand">
        <h1 class="logo-title">JOSEPHUS</h1>
        <span class="sub-title">Greek & English Reader</span>
      </div>

      <!-- Always Visible Work & Book Selector -->
      <div class="nav-selectors-group">
        <!-- Work Selector -->
        <select
          class="nav-select work-select"
          value={$currentWork}
          onchange={(e) =>
            setWork((e.target as HTMLSelectElement).value as WorkId)}
        >
          <option value="antiquities">Ant. Iud.</option>
          <option value="war">Bel. Iud.</option>
          <option value="life">Vita</option>
          <option value="apion">Con. Ap.</option>
        </select>

        <!-- Book Selector -->
        <select
          class="nav-select book-select"
          value={$currentBook}
          onchange={(e) => setBook(Number((e.target as HTMLSelectElement).value))}
        >
          {#each Array(numBooks) as _, i}
            <option value={i + 1}>Bk {i + 1}</option>
          {/each}
        </select>
      </div>

      <!-- Mobile Hamburger Menu Button -->
      <button
        class="hamburger-btn"
        onclick={toggleMobileMenu}
        title="Toggle Menu"
        aria-label="Toggle Navigation Menu"
      >
        <svg
          class="hamburger-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          {#if isMobileMenuOpen}
            <path d="M18 6L6 18M6 6l12 12" />
          {:else}
            <path d="M4 6h16M4 12h16M4 18h16" />
          {/if}
        </svg>
      </button>
    </div>

    <!-- Controls Toolbar (Collapsible on Mobile) -->
    <div class="toolbar" class:is-open={isMobileMenuOpen}>

      <!-- View Mode Buttons (Icon Only) -->
      <div class="button-group mode-group">
        <button
          class="btn mode-btn"
          class:active={$viewMode === "parallel"}
          onclick={() => {
            $viewMode = "parallel";
            isMobileMenuOpen = false;
          }}
          title="Side-by-Side Facing Columns"
          aria-label="Parallel View"
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
        </button>

        <button
          class="btn mode-btn"
          class:active={$viewMode === "greek"}
          onclick={() => {
            $viewMode = "greek";
            isMobileMenuOpen = false;
          }}
          title="Greek Text Only"
          aria-label="Greek Only View"
        >
          <span class="greek-sym">Ω</span>
        </button>

        <button
          class="btn mode-btn"
          class:active={$viewMode === "english"}
          onclick={() => {
            $viewMode = "english";
            isMobileMenuOpen = false;
          }}
          title="English Text Only"
          aria-label="English Only View"
        >
          <span class="eng-sym">EN</span>
        </button>

        <button
          class="btn mode-btn"
          class:active={$viewMode === "stacked"}
          onclick={() => {
            $viewMode = "stacked";
            isMobileMenuOpen = false;
          }}
          title="Stacked Verse-by-Verse"
          aria-label="Stacked View"
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
      </button>

      <!-- Font Size Controls -->
      <div class="button-group font-size-group">
        <button
          class="btn font-btn font-decrease"
          onclick={decreaseFontSize}
          disabled={$fontSize <= 13}
          title="Decrease reader text font size"
          aria-label="Decrease Font Size"
        >
          <span class="font-sym-small">A<sup>-</sup></span>
        </button>
        <button
          class="btn font-btn font-increase"
          onclick={increaseFontSize}
          disabled={$fontSize >= 27}
          title="Increase reader text font size"
          aria-label="Increase Font Size"
        >
          <span class="font-sym-large">A<sup>+</sup></span>
        </button>
      </div>

      <!-- Theme Switcher Dropdown -->
      <div class="theme-dropdown-container">
        <button
          class="btn icon-btn theme-toggle-btn"
          onclick={(e) => {
            e.stopPropagation();
            isThemeMenuOpen = !isThemeMenuOpen;
          }}
          title="Switch Theme"
          aria-label="Theme Selection Menu"
        >
          {#if $theme === "sepia"}
            <span class="theme-icon">📜</span>
          {:else if $theme === "dark"}
            <span class="theme-icon">🌙</span>
          {:else}
            <span class="theme-icon">☀️</span>
          {/if}
        </button>

        {#if isThemeMenuOpen}
          <div
            class="theme-popover-menu"
            onclick={(e) => e.stopPropagation()}
            onkeydown={(e) => {
              if (e.key === "Escape") closeThemeMenu();
            }}
            role="menu"
            tabindex="-1"
          >
            <button
              class="theme-option-btn"
              class:active={$theme === "sepia"}
              onclick={() => selectTheme("sepia")}
              role="menuitem"
            >
              <span class="theme-icon">📜</span> Sepia
            </button>
            <button
              class="theme-option-btn"
              class:active={$theme === "dark"}
              onclick={() => selectTheme("dark")}
              role="menuitem"
            >
              <span class="theme-icon">🌙</span> Dark
            </button>
            <button
              class="theme-option-btn"
              class:active={$theme === "light"}
              onclick={() => selectTheme("light")}
              role="menuitem"
            >
              <span class="theme-icon">☀️</span> Light
            </button>
          </div>
        {/if}
      </div>

      <!-- PDF Export Button -->
      <button
        class="btn primary-btn pdf-btn"
        onclick={() => {
          $showPdfModal = true;
          isMobileMenuOpen = false;
        }}
        title="Generate Facing-Page Printable PDF"
      >
        PDF
      </button>

      <!-- Source Data & License Attribution Button -->
      <button
        class="btn icon-btn info-btn"
        onclick={() => {
          $showAttributionModal = true;
          isMobileMenuOpen = false;
        }}
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

  .header-main-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .nav-selectors-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
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

  .hamburger-btn {
    display: none;
    background: transparent;
    border: none;
    color: var(--text-primary);
    padding: 0.35rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .hamburger-icon {
    width: 22px;
    height: 22px;
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
  }

  .nav-select {
    background-color: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 0.4rem 0.65rem;
    font-family: var(--font-sans);
    font-size: 0.88rem;
    font-weight: 600;
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
    justify-content: center;
    gap: 0.3rem;
    padding: 0.35rem 0.6rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 600;
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

  .greek-sym,
  .eng-sym {
    font-weight: 700;
    font-size: 0.85rem;
  }

  .icon {
    width: 16px;
    height: 16px;
  }

  .font-btn {
    padding: 0.35rem 0.3rem;
  }

  .font-sym-small {
    font-size: 0.65rem;
    font-weight: 700;
    line-height: 1;
  }

  .font-sym-large {
    font-size: 0.9rem;
    font-weight: 700;
    line-height: 1;
  }

  .font-btn sup {
    font-size: 0.65em;
    font-weight: 700;
    vertical-align: super;
    line-height: 0;
  }

  .font-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .primary-btn {
    background-color: var(--accent-color);
    color: #ffffff;
    border-radius: 6px;
    font-weight: 600;
    padding: 0.4rem 0.75rem;
  }

  .primary-btn:hover {
    background-color: var(--accent-hover);
    color: #ffffff;
  }

  .info-sym {
    font-size: 1.1rem;
  }

  .theme-dropdown-container {
    position: relative;
    display: inline-block;
  }

  .theme-popover-menu {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-shadow: var(--shadow-md);
    padding: 0.35rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 110px;
    z-index: 500;
  }

  .theme-option-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.4rem 0.6rem;
    background: transparent;
    border: none;
    border-radius: 5px;
    color: var(--text-primary);
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.15s ease;
  }

  .theme-option-btn:hover {
    background-color: var(--bg-secondary);
  }

  .theme-option-btn.active {
    background-color: var(--accent-color);
    color: #ffffff;
  }

  @media (max-width: 768px) {
    .header {
      padding: 0.6rem 1rem;
    }

    .header-main-bar {
      width: 100%;
      justify-content: space-between;
      gap: 0.4rem;
    }

    .hamburger-btn {
      display: flex;
      margin-left: auto;
    }

    .sub-title {
      display: none;
    }

    .toolbar {
      display: none;
      width: 100%;
      margin-top: 0.5rem;
      padding-top: 0.6rem;
      border-top: 1px solid var(--border-color);
    }

    .toolbar.is-open {
      display: flex;
    }
  }
</style>
