<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchMorphForWord, fetchDictionaryForWord, getBase, type MorphEntry, type LsjEntry } from '../lib/data';
  import {
    getHighlights,
    toggleLemmaHighlight,
    toggleFormHighlight,
    clearAllHighlights,
    isLemmaHighlighted,
    isFormHighlighted,
    normalizeKey,
    type HighlightStore
  } from '../lib/highlights';

  let {
    word = '',
    onClose = () => {}
  }: {
    word?: string;
    onClose?: () => void;
  } = $props();

  let isMaximized = $state(false);
  let info = $state<MorphEntry | null>(null);
  let dictEntry = $state<LsjEntry | null>(null);
  let loading = $state(true);
  let currentWord = $state('');
  let highlightsStore = $state<HighlightStore>({ lemmas: [], forms: [] });
  const base = getBase();

  function refreshHighlights() {
    highlightsStore = getHighlights();
  }

  let currentLemmaNorm = $derived(normalizeKey(info?.lemma_norm || info?.lemma || word));
  let currentLemmaDisplay = $derived(info?.lemma || word);

  let activeLemmaObj = $derived(highlightsStore.lemmas.find(l => l.lemma === currentLemmaNorm));
  let activeFormObj = $derived(highlightsStore.forms.find(f => f.word === normalizeKey(word)));
  let lemmaIsActive = $derived(!!activeLemmaObj);
  let formIsActive = $derived(!!activeFormObj);
  let hasAnyHighlights = $derived(highlightsStore.lemmas.length > 0 || highlightsStore.forms.length > 0);

  function handleToggleLemma() {
    toggleLemmaHighlight(currentLemmaDisplay, currentLemmaNorm);
    refreshHighlights();
  }

  function handleToggleForm() {
    toggleFormHighlight(word, currentLemmaNorm);
    refreshHighlights();
  }

  function handleClearAll() {
    clearAllHighlights();
    refreshHighlights();
  }

  function toggleMaximize() {
    isMaximized = !isMaximized;
  }

  onMount(() => {
    refreshHighlights();
    if (word && word !== currentWord) {
      currentWord = word;
      fetchInfo(word);
    }
    const handleHighlightsChanged = () => refreshHighlights();
    if (typeof window !== 'undefined') {
      window.addEventListener('reader-highlights-changed', handleHighlightsChanged);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('reader-highlights-changed', handleHighlightsChanged);
      }
    };
  });

  $effect(() => {
    if (word && word !== currentWord) {
      currentWord = word;
      fetchInfo(word);
    }
  });

  function stripAccents(text: string): string {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/ς/g, 'σ');
  }

  function findMorph(map: Record<string, MorphEntry>, target: string): MorphEntry | null {
    if (!target || !map) return null;
    const clean = target.replace(/[.,·;:!?"'»«()\[\]]/g, '').trim();
    const nfc = clean.normalize('NFC');
    const lower = nfc.toLowerCase();
    const stripped = stripAccents(clean);
    return map[clean] || map[nfc] || map[lower] || map[stripped] || map[target] || null;
  }

  function findDict(map: Record<string, LsjEntry>, key: string): LsjEntry | null {
    if (!key || !map) return null;
    const clean = key.replace(/[.,·;:!?"'»«()\[\]]/g, '').trim();
    const nfc = clean.normalize('NFC');
    const lower = nfc.toLowerCase();
    const stripped = stripAccents(clean);
    return map[clean] || map[nfc] || map[lower] || map[stripped] || map[key] || null;
  }

  async function fetchInfo(w: string) {
    loading = true;
    info = null;
    dictEntry = null;
    try {
      const [morphMap, dictMap] = await Promise.all([fetchMorphForWord(w), fetchDictionaryForWord(w)]);
      info = findMorph(morphMap, w);
      const lemmaKey = info?.lemma_norm || info?.lemma || w.toLowerCase();
      dictEntry = findDict(dictMap, lemmaKey);
    } catch (err) {
      console.error('Error fetching word info:', err);
    } finally {
      loading = false;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="word-popup-backdrop" onclick={onClose} role="presentation">
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div class="word-popup-card" class:maximized={isMaximized} onclick={(e) => e.stopPropagation()} role="dialog" aria-label="Word Morph & Definition">
    <div class="word-popup-header">
      <div class="header-title-row">
        <span class="popup-word">{word}</span>
        {#if !loading && info}
          <div class="header-morph-info">
            {#if info.pos || dictEntry?.pos}
              <span class="pos-badge">{info.pos || dictEntry?.pos}</span>
            {/if}
            {#if info.parse && info.parse !== 'Form'}
              <span class="parse-tag" title={info.desc || info.parse}>{info.parse}</span>
            {/if}
          </div>
        {/if}
      </div>
      <div class="header-actions">
        <button class="action-btn max-btn" onclick={toggleMaximize} aria-label={isMaximized ? "Restore size" : "Maximize"}>
          {isMaximized ? '🗗' : '⤢'}
        </button>
        <button class="action-btn close-btn" onclick={onClose} aria-label="Close">×</button>
      </div>
    </div>

    <div class="word-popup-body">
      {#if loading}
        <div class="popup-status">Analyzing word form...</div>
      {:else}
        {#if info}
          <div class="morph-section">
            <div class="lemma-line">
              <span class="label">Lemma:</span>
              <span class="lemma-value">{info.lemma}</span>
            </div>
            {#if dictEntry?.gloss}
              <div class="gloss-line">
                <span class="label">Gloss:</span>
                <span class="gloss-value">{dictEntry.gloss.replace(/,\s*,+/g, ', ').replace(/^[\s,;:]+|[\s,;:]+$/g, '')}</span>
              </div>
            {/if}
          </div>
        {:else}
          <div class="popup-status">No morphological parse found for "{word}".</div>
        {/if}

        <div class="popup-hl-bar">
          <span class="hl-label">Highlight:</span>
          <button
            class={`hl-toggle-btn ${lemmaIsActive ? 'active' : ''}`}
            style={lemmaIsActive && activeLemmaObj ? `--btn-hue: ${activeLemmaObj.hue}` : ''}
            onclick={handleToggleLemma}
            aria-pressed={lemmaIsActive}
            title={`Toggle highlight for all forms of lemma "${currentLemmaDisplay}"`}
          >
            <span class="hl-btn-icon">{lemmaIsActive ? '✓' : '+'}</span>
            <span>Lemma</span>
          </button>

          <button
            class={`hl-toggle-btn form-btn ${formIsActive ? 'active' : ''}`}
            style={formIsActive ? `--btn-hue: ${activeFormObj?.hue ?? activeLemmaObj?.hue ?? 160}` : ''}
            onclick={handleToggleForm}
            aria-pressed={formIsActive}
            title={`Toggle highlight for exact form "${word}"`}
          >
            <span class="hl-btn-icon">{formIsActive ? '✓' : '+'}</span>
            <span>Form</span>
          </button>

          {#if hasAnyHighlights}
            <button
              class="hl-clear-btn"
              onclick={handleClearAll}
              title="Clear all active highlights"
            >
              Clear All
            </button>
          {/if}
        </div>

        {#if dictEntry?.def}
          <details class="dict-details">
            <summary class="dict-summary">LSJ Full Definition</summary>
            <div class="dict-def">{dictEntry.def}</div>
          </details>
        {/if}

        {#if info?.lemma_norm}
          <a class="concordance-link" href={`${base}/lemma/?w=${encodeURIComponent(info.lemma_norm)}`}>
            See occurrences across Josephus →
          </a>
        {/if}
      {/if}
    </div>
  </div>
</div>

<style>
  .word-popup-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(4px);
    z-index: 2500;
    display: flex;
    align-items: flex-end;
    justify-content: center;
  }

  @media (min-width: 640px) {
    .word-popup-backdrop {
      align-items: center;
    }
  }

  .word-popup-card {
    background-color: var(--popup-bg, #ffffff);
    color: var(--text, #171a1c);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 12px 12px 0 0;
    width: 92%;
    max-width: 540px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    padding: 1.25rem;
    box-shadow: var(--popup-shadow, 0 10px 30px rgba(0, 0, 0, 0.2));
    box-sizing: border-box;
  }

  .word-popup-card.maximized {
    width: 95vw !important;
    max-width: 900px !important;
    height: 90vh !important;
    max-height: 90vh !important;
  }

  .word-popup-card.maximized .word-popup-body {
    max-height: calc(90vh - 4.5rem) !important;
  }

  .word-popup-card.maximized .dict-def {
    max-height: calc(90vh - 12rem) !important;
  }

  .word-popup-body {
    overflow-y: auto;
    max-height: calc(80vh - 4.5rem);
    padding-right: 0.25rem;
  }

  @media (min-width: 640px) {
    .word-popup-card {
      border-radius: 12px;
    }
  }

  .word-popup-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border, #d4d8d3);
    padding-bottom: 0.6rem;
    margin-bottom: 1rem;
    gap: 0.75rem;
  }

  .header-title-row {
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
    flex-wrap: wrap;
    flex: 1;
    min-width: 0;
  }

  .header-morph-info {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    flex-wrap: wrap;
  }

  .popup-word {
    font-family: var(--font-greek, serif);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent, #1f6f7a);
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .action-btn {
    background: transparent;
    border: none;
    color: var(--text-mid, #545b5c);
    font-size: 1.4rem;
    cursor: pointer;
    line-height: 1;
    padding: 0.25rem 0.45rem;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  .action-btn:hover {
    background-color: var(--page-bg, #eceee7);
    color: var(--text, #171a1c);
  }

  .max-btn {
    font-size: 1.15rem;
  }

  .morph-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 0.8rem;
  }

  .lemma-line, .gloss-line {
    display: flex;
    gap: 0.5rem;
    align-items: baseline;
    flex-wrap: wrap;
  }

  .label {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text-mid, #545b5c);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    min-width: 3.5rem;
  }

  .lemma-value {
    font-family: var(--font-greek, serif);
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--accent, #1f6f7a);
  }

  .pos-badge {
    display: inline-block;
    background-color: var(--page-bg, #eceee7);
    color: var(--accent, #1f6f7a);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 0.15rem 0.5rem;
    border-radius: 12px;
    border: 1px solid var(--border, #d4d8d3);
    margin-left: 0.4rem;
  }

  .label {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text-mid, #545b5c);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    min-width: 3.5rem;
  }

  .lemma-value {
    font-family: var(--font-greek, serif);
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--accent, #1f6f7a);
  }

  .gloss-value {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text, #171a1c);
  }

  .parse-line {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .parse-tag {
    display: inline-block;
    background-color: var(--page-bg, #eceee7);
    border: 1px solid var(--border, #d4d8d3);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent, #1f6f7a);
    cursor: help;
  }

  .parse-desc {
    font-size: 0.88rem;
    color: var(--text-mid, #545b5c);
  }

  .dict-details {
    margin-top: 0.8rem;
    border-top: 1px solid var(--border, #d4d8d3);
    padding-top: 0.6rem;
  }

  .dict-summary {
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--accent, #1f6f7a);
    cursor: pointer;
    user-select: none;
    padding: 0.3rem 0;
  }

  .dict-summary:hover {
    opacity: 0.85;
  }

  .dict-def {
    margin-top: 0.5rem;
    font-size: 0.9rem;
    line-height: 1.55;
    background-color: var(--page-bg, #f8f9f6);
    padding: 0.75rem;
    border-radius: 6px;
    border: 1px solid var(--border, #d4d8d3);
    color: var(--text, #171a1c);
    max-height: 250px;
    overflow-y: auto;
    font-family: serif;
  }

  .concordance-link {
    display: inline-block;
    margin-top: 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--accent, #1f6f7a);
    text-decoration: underline;
  }

  .popup-status {
    font-size: 0.9rem;
    color: var(--text-mid, #545b5c);
    padding: 1rem 0;
  }

  .popup-hl-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.45rem 0.75rem;
    margin: 0.75rem 0;
    background-color: var(--page-bg, #f2f4ef);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 24px;
    flex-wrap: wrap;
  }

  .hl-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-mid, #545b5c);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-right: 0.2rem;
  }

  .hl-toggle-btn {
    appearance: none;
    -webkit-appearance: none;
    outline: none;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background-color: var(--col-bg, #f4f6f0);
    border: 1px solid var(--border, #c5cac0);
    border-radius: 16px;
    padding: 0.22rem 0.65rem;
    font-size: 0.8rem;
    font-weight: 600;
    font-family: var(--font-ui, system-ui, sans-serif);
    color: var(--text-mid, #545b5c);
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    transition: all 0.18s ease;
    user-select: none;
  }

  .hl-btn-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    font-size: 0.68rem;
    font-weight: 700;
    background: rgba(0, 0, 0, 0.08);
    color: var(--text-mid, #545b5c);
    transition: all 0.18s ease;
  }

  .hl-toggle-btn:hover {
    background-color: var(--popup-bg, #ffffff);
    border-color: var(--accent, #1f6f7a);
    color: var(--accent, #1f6f7a);
    transform: translateY(-1px);
  }

  .hl-toggle-btn.active {
    background-color: hsl(var(--btn-hue, 160), 65%, 42%) !important;
    border-color: hsl(var(--btn-hue, 160), 75%, 32%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 6px hsl(var(--btn-hue, 160), 50%, 35%, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.3) !important;
  }

  .hl-toggle-btn.active .hl-btn-icon {
    background-color: #ffffff !important;
    color: hsl(var(--btn-hue, 160), 80%, 25%) !important;
  }

  .hl-toggle-btn.form-btn.active {
    background-color: hsl(var(--btn-hue, 160), 85%, 48%) !important;
    border-color: hsl(var(--btn-hue, 160), 90%, 28%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 0 10px hsl(var(--btn-hue, 160), 80%, 50%, 0.65), inset 0 1px 1px rgba(255, 255, 255, 0.4) !important;
  }

  .hl-toggle-btn.form-btn.active .hl-btn-icon {
    background-color: #ffffff !important;
    color: hsl(var(--btn-hue, 160), 90%, 20%) !important;
  }

  .hl-clear-btn {
    background: transparent;
    border: 1px dashed var(--error, #b22323);
    color: var(--error, #b22323);
    border-radius: 16px;
    padding: 0.22rem 0.65rem;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    margin-left: auto;
  }

  .hl-clear-btn:hover {
    background-color: var(--error, #b22323);
    color: #ffffff;
    border-style: solid;
  }
</style>
