<script lang="ts">
  import { onMount } from "svelte";
  import WordPopup from "./WordPopup.svelte";
  import SectionNavPill from "./SectionNavPill.svelte";
  import { fetchBook, type BookData, type Section } from "../lib/data";
  import { getWork, bookLabel } from "../lib/works";

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

  let workMeta = $derived(getWork(work));

  $effect(() => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("reader-state-changed", {
          detail: { viewMode, fontSize, morphEnabled },
        })
      );
    }
  });

  onMount(() => {
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

    window.addEventListener("reader-set-viewmode", handleSetViewMode);
    window.addEventListener("reader-set-fontsize", handleSetFontSize);
    window.addEventListener("reader-toggle-morph", handleToggleMorph);

    return () => {
      window.removeEventListener("reader-set-viewmode", handleSetViewMode);
      window.removeEventListener("reader-set-fontsize", handleSetFontSize);
      window.removeEventListener("reader-toggle-morph", handleToggleMorph);
    };
  });

  $effect(() => {
    if (bookData && bookData.sections) {
      sections = bookData.sections;
      loading = false;
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
          <div class="section-row" id={`niese-${sec.section_num || sec.niese}`}>
            <div class="section-badge" title={`Niese Section ${sec.niese}`}>
              § {sec.niese}
            </div>

            <div class="columns-wrapper">
              {#if viewMode === "parallel" || viewMode === "greek" || viewMode === "stacked"}
                <div class="greek-col">
                  {#each getWords(sec.grc) as word, wIdx (wIdx)}
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_static_element_interactions -->
                    <span
                      class="greek-word"
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
  </main>

  <SectionNavPill {sections} {viewMode} />

  {#if selectedWord}
    <WordPopup word={selectedWord} onClose={() => (selectedWord = null)} />
  {/if}
</div>

<style>
  .reader-container {
    max-width: 1300px;
    margin: 0 auto;
    padding: 1rem 1.5rem;
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
</style>
