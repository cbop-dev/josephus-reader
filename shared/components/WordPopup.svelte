<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchMorphForWord, fetchDictionaryForWord, getBase, type MorphEntry, type LsjEntry } from '../lib/data';

  export let word: string = '';
  export let onClose: () => void = () => {};

  let info: MorphEntry | null = null;
  let dictEntry: LsjEntry | null = null;
  let loading = true;
  const base = getBase();

  let currentWord = '';

  onMount(() => {
    if (word && word !== currentWord) {
      currentWord = word;
      fetchInfo(word);
    }
  });

  $: if (word && word !== currentWord) {
    currentWord = word;
    fetchInfo(word);
  }

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

<svelte:window on:keydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="word-popup-backdrop" on:click={onClose} role="presentation">
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div class="word-popup-card" on:click={(e) => e.stopPropagation()} role="dialog" aria-label="Word Morph & Definition">
    <div class="word-popup-header">
      <span class="popup-word">{word}</span>
      <button class="close-btn" on:click={onClose} aria-label="Close">×</button>
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
            <div class="parse-line">
              <span class="parse-tag">{info.parse}</span>
              <span class="parse-desc">{info.desc}</span>
            </div>
          </div>
        {:else}
          <div class="popup-status">No morphological parse found for "{word}".</div>
        {/if}

        {#if dictEntry}
          <div class="dict-section">
            <div class="dict-title">LSJ Definition:</div>
            <div class="dict-def">{dictEntry.def}</div>
          </div>
        {/if}

        {#if info?.lemma_norm}
          <a class="concordance-link" href={`${base}/lemma/${encodeURIComponent(info.lemma_norm)}`}>
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
    width: 100%;
    max-width: 500px;
    padding: 1.25rem;
    box-shadow: var(--popup-shadow, 0 10px 30px rgba(0, 0, 0, 0.2));
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
  }

  .popup-word {
    font-family: var(--font-greek, serif);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent, #1f6f7a);
  }

  .close-btn {
    background: transparent;
    border: none;
    color: var(--text-mid, #545b5c);
    font-size: 1.5rem;
    cursor: pointer;
  }

  .close-btn:hover {
    color: var(--text, #171a1c);
  }

  .morph-section {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-bottom: 1rem;
  }

  .lemma-line {
    display: flex;
    gap: 0.5rem;
    align-items: baseline;
  }

  .label {
    font-size: 0.85rem;
    color: var(--text-mid, #545b5c);
    text-transform: uppercase;
  }

  .lemma-value {
    font-family: var(--font-greek, serif);
    font-size: 1.2rem;
    font-weight: 600;
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
    margin-right: 0.5rem;
  }

  .parse-desc {
    font-size: 0.88rem;
    color: var(--text-mid, #545b5c);
  }

  .dict-section {
    margin-top: 0.8rem;
    padding-top: 0.8rem;
    border-top: 1px solid var(--border, #d4d8d3);
  }

  .dict-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text-mid, #545b5c);
    margin-bottom: 0.4rem;
  }

  .dict-def {
    font-size: 0.92rem;
    line-height: 1.5;
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
</style>
