<script lang="ts">
  import { onMount } from 'svelte';
  import WordPopup from './WordPopup.svelte';
  import { fetchBook, type BookData, type Section } from '../lib/data';
  import { getWork, bookLabel } from '../lib/works';

  export let work: string = 'Antiquities';
  export let bookNum: number = 1;
  export let bookData: BookData | null = null;

  let sections: Section[] = [];
  let loading = false;
  let viewMode: 'parallel' | 'greek' | 'english' | 'stacked' = 'parallel';
  let fontSize = 18;
  let morphEnabled = true;
  let selectedWord: string | null = null;

  $: workMeta = getWork(work);

  $: if (bookData && bookData.sections) {
    sections = bookData.sections;
    loading = false;
  } else {
    loadBookData(work, bookNum);
  }

  function loadBookData(w: string, b: number) {
    loading = true;
    fetchBook(w, b)
      .then(data => {
        sections = data.sections || [];
        loading = false;
      })
      .catch(err => {
        console.error('Failed to load book data:', err);
        loading = false;
      });
  }

  function handleWordClick(w: string) {
    if (!morphEnabled) return;
    const cleanWord = w.replace(/[.,·;:!?"'»«]+$/, '').replace(/^[«»"']/, '');
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
</script>

<div class="reader-container" style={`--reader-font-size: ${fontSize}px`}>
  <!-- Sticky Reader Controls Strip -->
  <div class="controls-strip">
    <div class="controls-group view-modes">
      <button
        class="ctrl-btn"
        class:active={viewMode === 'parallel'}
        on:click={() => (viewMode = 'parallel')}
        title="Side-by-side Greek & English"
      >
        Side-by-Side
      </button>
      <button
        class="ctrl-btn"
        class:active={viewMode === 'greek'}
        on:click={() => (viewMode = 'greek')}
        title="Greek text only"
      >
        Greek
      </button>
      <button
        class="ctrl-btn"
        class:active={viewMode === 'english'}
        on:click={() => (viewMode = 'english')}
        title="English text only"
      >
        English
      </button>
      <button
        class="ctrl-btn"
        class:active={viewMode === 'stacked'}
        on:click={() => (viewMode = 'stacked')}
        title="Stacked section text"
      >
        Stacked
      </button>
    </div>

    <div class="controls-group font-controls">
      <button class="ctrl-btn font-btn" on:click={decreaseFontSize} disabled={fontSize <= 14} title="Decrease text size">
        A<sup>-</sup>
      </button>

      <button class="ctrl-btn font-btn" on:click={increaseFontSize} disabled={fontSize >= 28} title="Increase text size">
        A<sup>+</sup>
      </button>
    </div>

    <button
      class="ctrl-btn morph-toggle"
      class:active={morphEnabled}
      on:click={() => (morphEnabled = !morphEnabled)}
      title="Toggle word lookup popups"
    >
      Morph {morphEnabled ? 'On' : 'Off'}
    </button>
  </div>

  <main class="reader-content">
    {#if loading}
      <div class="loading-state">Loading text data...</div>
    {:else if sections.length === 0}
      <div class="empty-state">No section data available for {work} Book {bookNum}.</div>
    {:else}
      <div class={`text-grid view-${viewMode}`}>
        {#each sections as sec}
          <div class="section-row" id={`niese-${sec.section_num || sec.niese}`}>
            <div class="section-badge" title={`Niese Section ${sec.niese}`}>
              § {sec.niese}
            </div>

            <div class="columns-wrapper">
              {#if viewMode === 'parallel' || viewMode === 'greek' || viewMode === 'stacked'}
                <div class="greek-col">
                  {#each sec.grc.split(/\s+/) as word}
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_static_element_interactions -->
                    <span
                      class="greek-word"
                      class:interactive={morphEnabled}
                      on:click={() => handleWordClick(word)}
                    >
                      {word}{' '}
                    </span>
                  {/each}
                </div>
              {/if}

              {#if viewMode === 'parallel' || viewMode === 'english' || viewMode === 'stacked'}
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
    flex-wrap: wrap;
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
  .view-greek .columns-wrapper, .view-english .columns-wrapper, .view-stacked .columns-wrapper {
    grid-template-columns: 1fr;
  }
  .greek-col {
    font-family: var(--font-greek, "Cardo", Georgia, serif);
    line-height: var(--lh-greek, 1.7);
  }
  .english-col {
    font-family: var(--font-english, "EB Garamond", Georgia, serif);
    line-height: var(--lh-english, 1.72);
    color: var(--text-mid, #545b5c);
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
  .loading-state, .empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-mid, #545b5c);
  }

  @media (max-width: 768px) {
    .view-parallel .columns-wrapper {
      grid-template-columns: 1fr;
    }
    .controls-strip {
      flex-direction: column;
      align-items: stretch;
    }
  }
</style>
