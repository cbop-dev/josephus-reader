<script lang="ts">
  import { onMount } from "svelte";
  import WordPopup from "./WordPopup.svelte";
  import SectionNavPill from "./SectionNavPill.svelte";
  import { fetchBook, type BookData, type Section } from "../lib/data";
  import { getWork, bookLabel } from "../lib/works";
  import {
    getHighlights,
    getWordHighlightInfo,
    preloadActiveLemmaFormSets,
    removeLemmaHighlight,
    removeFormHighlight,
    clearAllHighlights,
    type HighlightStore
  } from "../lib/highlights";

  let {
    work = "Antiquities",
    bookNum = 1,
    bookData = null,
  }: {
    work?: string;
    bookNum?: number;
    bookData?: BookData | null;
  } = $props();

  let sections = $state<Section[]>([]);
  let loading = $state(false);
  let viewMode = $state<"parallel" | "greek" | "english" | "stacked">(
    "parallel",
  );
  let fontSize = $state(18);
  let morphEnabled = $state(true);
  let selectedWord = $state<string | null>(null);
  let highlightsStore = $state<HighlightStore>({ lemmas: [], forms: [] });
  let showHighlightsModal = $state(false);

  let workMeta = $derived(getWork(work));
  let totalActiveHighlights = $derived(
    highlightsStore.lemmas.length + highlightsStore.forms.length
  );

  function refreshHighlights() {
    highlightsStore = getHighlights();
  }

  $effect(() => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("reader-state-changed", {
          detail: { viewMode, fontSize, morphEnabled },
        })
      );
    }
  });

  let targetWord = $state<string | null>(null);
  let targetLemma = $state<string | null>(null);

  function readHighlightParams() {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      targetWord = params.get("hl") || null;
      targetLemma = params.get("lemma") || null;
    }
  }

  function cleanWordText(text: string): string {
    if (!text) return "";
    return text.replace(/[.,·;:!?"'»«()\[\]]/g, "").trim();
  }

  function stripAccents(text: string): string {
    if (!text) return "";
    return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/ς/g, "σ");
  }

  function getHighlightInfo(word: string): { className: string; style: string } {
    // 1. Check Store highlights (Multi-lemma & multi-form highlight engine)
    const hlInfo = getWordHighlightInfo(word, highlightsStore);
    if (hlInfo.isForm) {
      return { className: "word-hl-form", style: hlInfo.style || "" };
    }
    if (hlInfo.isLemma) {
      return { className: "word-hl-lemma", style: hlInfo.style || "" };
    }

    // 2. Fallback to URL single-target highlights
    if (targetWord || targetLemma) {
      const cleanW = cleanWordText(word);
      if (cleanW) {
        if (targetWord) {
          const cleanT = cleanWordText(targetWord);
          if (cleanW === cleanT || stripAccents(cleanW) === stripAccents(cleanT)) {
            return { className: "word-hl-primary", style: "" };
          }
        }
        if (targetLemma) {
          const normW = stripAccents(cleanW);
          const normL = stripAccents(cleanWordText(targetLemma));
          if (normW === normL || (normL.length >= 3 && normW.startsWith(normL.slice(0, Math.min(normL.length, 5))))) {
            return { className: "word-hl-secondary", style: "" };
          }
        }
      }
    }

    return { className: "", style: "" };
  }

  onMount(() => {
    readHighlightParams();
    refreshHighlights();
    preloadActiveLemmaFormSets();

    const handleSetViewMode = (e: Event) => {
      const mode = (e as CustomEvent).detail;
      if (
        mode === "parallel" ||
        mode === "stacked" ||
        mode === "greek" ||
        mode === "english"
      ) {
        viewMode = mode;
      }
    };
    const handleSetFontSize = (e: Event) => {
      const action = (e as CustomEvent).detail;
      if (action === "inc") increaseFontSize();
      if (action === "dec") decreaseFontSize();
    };
    const handleToggleMorph = () => {
      morphEnabled = !morphEnabled;
    };
    const handleHighlightsChanged = () => {
      refreshHighlights();
    };
    const handleToggleHighlightsModal = () => {
      showHighlightsModal = !showHighlightsModal;
    };

    window.addEventListener("reader-set-viewmode", handleSetViewMode);
    window.addEventListener("reader-set-fontsize", handleSetFontSize);
    window.addEventListener("reader-toggle-morph", handleToggleMorph);
    window.addEventListener("reader-highlights-changed", handleHighlightsChanged);
    window.addEventListener("reader-toggle-highlights", handleToggleHighlightsModal);

    return () => {
      window.removeEventListener("reader-set-viewmode", handleSetViewMode);
      window.removeEventListener("reader-set-fontsize", handleSetFontSize);
      window.removeEventListener("reader-toggle-morph", handleToggleMorph);
      window.removeEventListener("reader-highlights-changed", handleHighlightsChanged);
      window.removeEventListener("reader-toggle-highlights", handleToggleHighlightsModal);
    };
  });

  function findSectionElement(hash: string): HTMLElement | null {
    if (typeof window === "undefined" || !hash) return null;
    const raw = hash.replace(/^#/, "");
    const decoded = decodeURIComponent(raw);

    // 1. Direct ID match (e.g. niese-1 or niese-1–5)
    let el = document.getElementById(raw) || document.getElementById(decoded);
    if (el) return el;

    // 2. Extract section identifier without 'niese-' prefix
    const cleanSec = decoded.replace(/^niese-/, "").trim();

    // 3. Match data-niese or data-section attribute
    el = (document.querySelector(`[data-niese="${cleanSec}"]`) as HTMLElement | null) ||
         (document.querySelector(`[data-section="${cleanSec}"]`) as HTMLElement | null);
    if (el) return el;

    // 4. Extract leading number (e.g. "1" from "1–5" or "53" from "53–56")
    const numMatch = cleanSec.match(/^\d+/);
    if (numMatch) {
      const num = numMatch[0];
      el = document.getElementById(`niese-${num}`) ||
           (document.querySelector(`[data-section="${num}"]`) as HTMLElement | null) ||
           (document.querySelector(`[data-niese^="${num}"]`) as HTMLElement | null);
      if (el) return el;
    }

    return null;
  }

  function scrollToHash() {
    if (typeof window === "undefined" || !window.location.hash) return;
    const hash = window.location.hash;

    const attemptScroll = (attemptsLeft: number) => {
      const el = findSectionElement(hash);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      } else if (attemptsLeft > 0) {
        setTimeout(() => attemptScroll(attemptsLeft - 1), 80);
      }
    };

    setTimeout(() => attemptScroll(8), 50);
  }

  $effect(() => {
    if (bookData && bookData.sections) {
      sections = bookData.sections;
      loading = false;
      scrollToHash();
    } else {
      loadBookData(work, bookNum);
    }
  });

  function loadBookData(w: string, b: number) {
    loading = true;
    fetchBook(w, b)
      .then((data) => {
        sections = data.sections || [];
        loading = false;
        scrollToHash();
      })
      .catch((err) => {
        console.error("Failed to load book data:", err);
        loading = false;
      });
  }

  function handleWordClick(w: string) {
    if (!morphEnabled) return;
    const cleanWord = w.replace(/[.,·;:!?"'»«]+$/, "").replace(/^[«»"']/, "");
    if (cleanWord) {
      selectedWord = cleanWord;
    }
  }

  function decreaseFontSize() {
    fontSize = Math.max(14, fontSize - 2);
  }

  function increaseFontSize() {
    fontSize = Math.min(28, fontSize + 2);
  }

  function getWords(text: string): string[] {
    if (!text) return [];
    return text.trim().split(/\s+/);
  }
</script>

<div class="reader-container" style={`--reader-font-size: ${fontSize}px`}>
  <!-- Sticky Reader Controls Strip -->
  <div class="controls-strip">
    <div class="controls-group view-modes">
      <button
        class="ctrl-btn icon-btn"
        class:active={viewMode === "parallel"}
        onclick={() => (viewMode = "parallel")}
        title="Side-by-side (Greek & English)"
        aria-label="Side-by-side view"
      >
        ◧
      </button>
      <button
        class="ctrl-btn icon-btn"
        class:active={viewMode === "stacked"}
        onclick={() => (viewMode = "stacked")}
        title="Stacked section text"
        aria-label="Stacked view"
      >
        ⬓
      </button>
      <button
        class="ctrl-btn icon-btn"
        class:active={viewMode === "greek"}
        onclick={() => (viewMode = "greek")}
        title="Greek text only"
        aria-label="Greek view"
      >
        Ω
      </button>
      <button
        class="ctrl-btn icon-btn"
        class:active={viewMode === "english"}
        onclick={() => (viewMode = "english")}
        title="English text only"
        aria-label="English view"
      >
        A
      </button>
    </div>

    <h1 class="work-title-heading">
      {workMeta?.englishTitle || work}{#if workMeta && workMeta.booksCount > 1} — Book {bookNum}{/if}
    </h1>

    <div class="right-controls">
      <div class="controls-group font-controls">
        <button
          class="ctrl-btn font-btn"
          onclick={decreaseFontSize}
          disabled={fontSize <= 14}
          title="Decrease text size"
        >
          A<sup>-</sup>
        </button>

        <button
          class="ctrl-btn font-btn"
          onclick={increaseFontSize}
          disabled={fontSize >= 28}
          title="Increase text size"
        >
          A<sup>+</sup>
        </button>
      </div>

      <div class="controls-group morph-controls">
        <button
          class="ctrl-btn morph-toggle"
          class:active={morphEnabled}
          onclick={() => (morphEnabled = !morphEnabled)}
          title="Toggle word lookup popups"
        >
          Morph
        </button>

        <button
          class="ctrl-btn hl-modal-toggle"
          class:has-highlights={totalActiveHighlights > 0}
          onclick={() => (showHighlightsModal = !showHighlightsModal)}
          title="Manage active word & lemma highlights"
        >
          Highlights{#if totalActiveHighlights > 0} <span class="hl-badge">{totalActiveHighlights}</span>{/if}
        </button>
      </div>
    </div>
  </div>

  <main class="reader-content">
    {#if loading}
      <div class="loading-state">Loading text data...</div>
    {:else if sections.length === 0}
      <div class="empty-state">
        No section data available for {work} Book {bookNum}.
      </div>
    {:else}
      <div class={`text-grid view-${viewMode}`}>
        {#each sections as sec, sIdx (sIdx)}
          <div
            class="section-row"
            id={`niese-${sec.section_num || sec.niese}`}
            data-niese={sec.niese}
            data-section={sec.section_num}
          >
            <div class="section-badge" title={`Niese Section ${sec.niese}`}>
              § {sec.niese}
            </div>

            <div class="columns-wrapper">
              {#if viewMode === "parallel" || viewMode === "greek" || viewMode === "stacked"}
                <div class="greek-col">
                  {#each getWords(sec.grc) as word, wIdx (wIdx)}
                    {@const hl = getHighlightInfo(word)}
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_static_element_interactions -->
                    <span
                      class={`greek-word ${hl.className}`.trim()}
                      style={hl.style}
                      class:interactive={morphEnabled}
                      onclick={() => handleWordClick(word)}>{word}</span
                    >{" "}
                  {/each}
                </div>
              {/if}

              {#if viewMode === "parallel" || viewMode === "english" || viewMode === "stacked"}
                <div class="english-col">
                  {sec.eng}
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <SectionNavPill {sections} {work} {bookNum} />
  </main>

  {#if selectedWord}
    <WordPopup word={selectedWord} onClose={() => (selectedWord = null)} />
  {/if}

  {#if showHighlightsModal}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="hl-modal-backdrop" onclick={() => (showHighlightsModal = false)} role="presentation">
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div class="hl-modal-card" onclick={(e) => e.stopPropagation()} role="dialog" aria-label="Active Highlights">
        <div class="hl-modal-header">
          <h2>Active Highlights ({totalActiveHighlights})</h2>
          <button class="action-btn" onclick={() => (showHighlightsModal = false)} aria-label="Close">×</button>
        </div>

        <div class="hl-modal-body">
          {#if totalActiveHighlights === 0}
            <div class="hl-empty-msg">
              No active highlights. Click on any word in the text to open its popup and highlight its lemma or exact form.
            </div>
          {:else}
            {#if highlightsStore.lemmas.length > 0}
              <div class="hl-modal-section">
                <h3>(1) Lemma Highlights</h3>
                <div class="hl-chips-grid">
                  {#each highlightsStore.lemmas as l (l.lemma)}
                    <div class="hl-chip lemma-chip" style={`--chip-hue: ${l.hue}`}>
                      <span class="chip-color-dot"></span>
                      <span class="chip-text">{l.displayLemma}</span>
                      <button class="chip-remove-btn" onclick={() => removeLemmaHighlight(l.lemma)} aria-label={`Remove ${l.displayLemma} highlight`}>×</button>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if highlightsStore.forms.length > 0}
              <div class="hl-modal-section">
                <h3>(2) Exact Form Highlights</h3>
                <div class="hl-chips-grid">
                  {#each highlightsStore.forms as f (f.word)}
                    <div class="hl-chip form-chip" style={`--chip-hue: ${f.hue}`}>
                      <span class="chip-color-dot"></span>
                      <span class="chip-text">{f.displayWord}</span>
                      <button class="chip-remove-btn" onclick={() => removeFormHighlight(f.word)} aria-label={`Remove ${f.displayWord} highlight`}>×</button>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          {/if}
        </div>

        {#if totalActiveHighlights > 0}
          <div class="hl-modal-footer">
            <button class="hl-clear-all-btn" onclick={clearAllHighlights}>
              Clear All Highlights
            </button>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .reader-container {
    max-width: 1300px;
    margin: 0 auto;
    padding: 1rem 1.5rem 5.5rem 1.5rem;
    font-size: var(--reader-font-size, 18px);
  }
  .work-title-heading {
    font-family: var(--font-english, "EB Garamond", Georgia, serif);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text, #171a1c);
    margin: 0;
    text-align: center;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 0 0.5rem;
  }
  .right-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .controls-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.5rem 0.75rem;
    background: var(--col-bg, #f5f6f2);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 6px;
    margin-bottom: 1.5rem;
    position: sticky;
    top: 60px;
    z-index: 50;
  }
  .controls-group {
    display: flex;
    gap: 0.25rem;
    background: var(--page-bg, #eceee7);
    padding: 2px;
    border-radius: 4px;
    border: 1px solid var(--border, #d4d8d3);
  }
  .ctrl-btn {
    background: transparent;
    border: none;
    border-radius: 3px;
    padding: 0.3rem 0.6rem;
    font-size: 0.85rem;
    font-family: var(--font-ui, system-ui, sans-serif);
    font-weight: 500;
    color: var(--text-mid, #545b5c);
    cursor: pointer;
  }
  .ctrl-btn:hover {
    color: var(--accent, #1f6f7a);
  }
  .ctrl-btn.active {
    background: var(--accent, #1f6f7a);
    color: #ffffff;
  }
  .ctrl-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  .text-grid {
    display: flex;
    flex-direction: column;
    gap: 1.75rem;
  }
  .section-row {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid var(--border, #d4d8d3);
    scroll-margin-top: 120px;
  }
  .section-badge {
    font-family: var(--font-ui, system-ui, sans-serif);
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--accent, #1f6f7a);
  }
  .columns-wrapper {
    display: grid;
    gap: 1.5rem;
  }
  .view-parallel .columns-wrapper {
    grid-template-columns: 1fr 1fr;
  }
  .view-greek .columns-wrapper,
  .view-english .columns-wrapper,
  .view-stacked .columns-wrapper {
    grid-template-columns: 1fr;
  }
  .greek-col {
    font-family: var(--font-greek, "Cardo", Georgia, serif);
    line-height: var(--lh-greek, 1.7);
    scroll-margin-top: 120px;
  }
  .english-col {
    font-family: var(--font-english, "EB Garamond", Georgia, serif);
    line-height: var(--lh-english, 1.72);
    color: var(--text-mid, #545b5c);
    scroll-margin-top: 120px;
  }
  .greek-word.interactive {
    cursor: pointer;
    border-radius: 2px;
    padding: 0 1px;
    transition: background-color 0.12s ease;
  }
  .greek-word.interactive:hover {
    background-color: var(--greek-hover, rgba(31, 111, 122, 0.12));
    color: var(--accent, #1f6f7a);
  }
  .loading-state,
  .empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-mid, #545b5c);
  }

  @media (max-width: 768px) {
    .view-parallel .columns-wrapper {
      grid-template-columns: 1fr;
    }
    .section-row,
    .greek-col,
    .english-col {
      scroll-margin-top: 70px;
    }
    .controls-strip {
      display: flex;
      justify-content: center;
      padding: 0.55rem 0.75rem;
      position: static;
      margin-bottom: 1.25rem;
    }
    .controls-strip .view-modes,
    .controls-strip .right-controls {
      display: none;
    }
    .work-title-heading {
      font-size: 1.1rem;
      white-space: normal;
      padding: 0;
    }
  }

  /* Highlights Modal & Controls CSS */

  .hl-modal-toggle {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }
  .hl-modal-toggle.has-highlights {
    border-color: var(--accent, #1f6f7a);
    color: var(--accent, #1f6f7a);
    font-weight: 700;
  }
  .hl-badge {
    background-color: var(--accent, #1f6f7a);
    color: #ffffff;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
  }
  .hl-modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(4px);
    z-index: 2400;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .hl-modal-card {
    background-color: var(--popup-bg, #ffffff);
    color: var(--text, #171a1c);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 12px;
    width: 90%;
    max-width: 520px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    padding: 1.25rem;
    box-shadow: var(--popup-shadow, 0 10px 30px rgba(0, 0, 0, 0.2));
  }
  .hl-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border, #d4d8d3);
    padding-bottom: 0.6rem;
    margin-bottom: 1rem;
  }
  .hl-modal-header h2 {
    font-size: 1.2rem;
    color: var(--accent, #1f6f7a);
    margin: 0;
  }
  .hl-modal-body {
    overflow-y: auto;
    max-height: 60vh;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }
  .hl-modal-section h3 {
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text-mid, #545b5c);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 0.6rem;
  }
  .hl-chips-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .hl-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.3rem 0.65rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    transition: all 0.15s ease;
  }
  .lemma-chip {
    background-color: hsl(var(--chip-hue, 160), 75%, 90%);
    border: 1.5px solid hsl(var(--chip-hue, 160), 65%, 50%);
    color: hsl(var(--chip-hue, 160), 85%, 20%);
  }
  .form-chip {
    background-color: hsl(var(--chip-hue, 160), 85%, 72%);
    border: 2px solid hsl(var(--chip-hue, 160), 80%, 36%);
    color: hsl(var(--chip-hue, 160), 90%, 15%);
    font-weight: 700;
    box-shadow: 0 0 6px hsl(var(--chip-hue, 160), 70%, 55%);
  }
  .chip-color-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: hsl(var(--chip-hue, 160), 80%, 45%);
  }
  .chip-text {
    font-family: var(--font-greek, serif);
  }
  .chip-remove-btn {
    background: transparent;
    border: none;
    font-size: 1.1rem;
    line-height: 1;
    cursor: pointer;
    color: inherit;
    opacity: 0.7;
    padding: 0 0.1rem;
  }
  .chip-remove-btn:hover {
    opacity: 1;
  }
  .hl-empty-msg {
    text-align: center;
    color: var(--text-mid, #545b5c);
    padding: 1.5rem 0;
    font-size: 0.92rem;
  }
  .hl-modal-footer {
    border-top: 1px solid var(--border, #d4d8d3);
    padding-top: 0.8rem;
    margin-top: 1rem;
    display: flex;
    justify-content: flex-end;
  }
  .hl-clear-all-btn {
    background-color: transparent;
    border: 1px solid var(--error, #b22323);
    color: var(--error, #b22323);
    border-radius: 6px;
    padding: 0.35rem 0.85rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .hl-clear-all-btn:hover {
    background-color: var(--error, #b22323);
    color: #ffffff;
  }
</style>
