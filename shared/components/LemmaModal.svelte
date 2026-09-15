<script lang="ts">
  import { onMount } from 'svelte';
  import { getBase } from '../lib/data';

  export interface LemmaOccurrence {
    work: string;
    book: number;
    sec: string;
    word: string;
  }

  export interface LemmaEntry {
    lemma: string;
    count: number;
    occurrences: LemmaOccurrence[];
  }

  let {
    lemmaNorm = '',
    lemmaDisplay = '',
    onClose = () => {}
  }: {
    lemmaNorm?: string;
    lemmaDisplay?: string;
    onClose?: () => void;
  } = $props();

  let loading = $state(true);
  let errorMsg = $state<string | null>(null);
  let lemmaEntry = $state<LemmaEntry | null>(null);
  let allExpanded = $state(true);

  const WORK_META: Record<string, { title: string; abbrev: string }> = {
    'Antiquities': { title: 'Antiquities of the Jews', abbrev: 'Ant.' },
    'War': { title: 'The Jewish War', abbrev: 'War' },
    'Life': { title: 'The Life of Josephus', abbrev: 'Life' },
    'Apion': { title: 'Against Apion', abbrev: 'C. Ap.' }
  };

  function getGreekBucket(text: string): string {
    if (!text) return 'other';
    const norm = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
    if (!norm) return 'other';
    const ch = norm[0].toLowerCase();
    const map: Record<string, string> = {
      'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
      'ε': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta',
      'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu',
      'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron', 'π': 'pi',
      'ρ': 'rho', 'σ': 'sigma', 'ς': 'sigma', 'τ': 'tau',
      'υ': 'upsilon', 'φ': 'phi', 'χ': 'chi', 'ψ': 'psi',
      'ω': 'omega'
    };
    return map[ch] || 'other';
  }

  function normalizeKey(str: string): string {
    if (!str) return '';
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/ς/g, 'σ');
  }

  onMount(() => {
    loadLemmaData();
  });

  async function loadLemmaData() {
    loading = true;
    errorMsg = null;
    lemmaEntry = null;

    if (!lemmaNorm) {
      errorMsg = 'No lemma specified.';
      loading = false;
      return;
    }

    const base = getBase();
    const bucket = getGreekBucket(lemmaNorm);
    const url = `${base}/data/lemmata/${bucket}.json`;

    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error('Failed to fetch concordance dataset');
      const data = await resp.json();

      const keyNorm = normalizeKey(lemmaNorm);
      const match = data[lemmaNorm] || data[keyNorm] || Object.values(data).find((e: any) => normalizeKey(e.lemma) === keyNorm);

      if (match) {
        lemmaEntry = match;
      } else {
        errorMsg = `No occurrences recorded for "${lemmaDisplay || lemmaNorm}".`;
      }
    } catch (err: any) {
      console.error('Error fetching lemma concordance:', err);
      errorMsg = 'Failed to load concordance data.';
    } finally {
      loading = false;
    }
  }

  let groupedOccurrences = $derived.by(() => {
    if (!lemmaEntry || !lemmaEntry.occurrences) return {};
    const groups: Record<string, Record<number, LemmaOccurrence[]>> = {};
    for (const occ of lemmaEntry.occurrences) {
      const w = occ.work || 'Other';
      const b = occ.book || 1;
      if (!groups[w]) groups[w] = {};
      if (!groups[w][b]) groups[w][b] = [];
      groups[w][b].push(occ);
    }
    return groups;
  });

  let totalCount = $derived(
    lemmaEntry?.count || lemmaEntry?.occurrences?.length || 0
  );

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  function toggleAll() {
    allExpanded = !allExpanded;
    const detailsElements = document.querySelectorAll('.lemma-modal-body details');
    detailsElements.forEach((el) => {
      (el as HTMLDetailsElement).open = allExpanded;
    });
  }

  function handleOccClick(e: MouseEvent, url: string) {
    e.preventDefault();
    onClose();
    if (typeof window !== 'undefined') {
      window.location.href = url;
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="lemma-modal-backdrop" onclick={onClose} role="presentation">
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    class="lemma-modal-card"
    onclick={(e) => e.stopPropagation()}
    role="dialog"
    aria-label="Lemma Concordance Modal"
    tabindex="-1"
  >
    <div class="lemma-modal-header">
      <div class="header-left">
        <h2 class="lemma-title">{lemmaEntry?.lemma || lemmaDisplay || lemmaNorm}</h2>
        <span class="count-badge">{totalCount} {totalCount === 1 ? 'occurrence' : 'occurrences'}</span>
      </div>
      <div class="header-actions">
        {#if !loading && lemmaEntry}
          <button class="toggle-all-btn" onclick={toggleAll}>
            {allExpanded ? 'Collapse All' : 'Expand All'}
          </button>
        {/if}
        <button class="close-btn" onclick={onClose} aria-label="Close modal">×</button>
      </div>
    </div>

    <div class="lemma-modal-body">
      {#if loading}
        <div class="status-card">Loading occurrences across Josephus...</div>
      {:else if errorMsg}
        <div class="status-card error-card">{errorMsg}</div>
      {:else if lemmaEntry}
        {#each Object.entries(groupedOccurrences) as [workKey, booksMap] (workKey)}
          {@const meta = WORK_META[workKey] || { title: workKey, abbrev: workKey }}
          {@const workCount = Object.values(booksMap).reduce((acc, arr) => acc + arr.length, 0)}
          
          <details class="work-group" open={allExpanded}>
            <summary class="work-summary">
              <span class="work-title">{meta.title} <span class="work-abbrev">({meta.abbrev})</span></span>
              <span class="work-count-tag">{workCount} {workCount === 1 ? 'occ' : 'occs'}</span>
            </summary>
            <div class="work-content">
              {#each Object.entries(booksMap).sort(([a], [b]) => Number(a) - Number(b)) as [bookNumStr, occs] (bookNumStr)}
                {@const bNum = Number(bookNumStr)}
                <details class="book-group" open={allExpanded}>
                  <summary class="book-summary">
                    <span class="book-title">Book {bNum}</span>
                    <span class="book-count-tag">({occs.length})</span>
                  </summary>
                  <div class="pills-grid">
                    {#each occs as occ}
                      {@const base = getBase()}
                      {@const secRef = occ.sec ? `§ ${occ.sec}` : `Bk ${occ.book}`}
                      {@const anchor = occ.sec ? `#niese-${occ.sec}` : ''}
                      {@const normK = normalizeKey(lemmaNorm)}
                      {@const targetUrl = `${base}/${occ.work}/book/${occ.book}/?hl=${encodeURIComponent(occ.word)}&lemma=${encodeURIComponent(normK)}${anchor}`}

                      <a
                        class="occ-link"
                        href={targetUrl}
                        onclick={(e) => handleOccClick(e, targetUrl)}
                      >
                        <span class="occ-ref">{secRef}</span>
                        <span class="occ-form">{occ.word}</span>
                      </a>
                    {/each}
                  </div>
                </details>
              {/each}
            </div>
          </details>
        {/each}
      {/if}
    </div>
  </div>
</div>

<style>
  .lemma-modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 2600;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    box-sizing: border-box;
  }

  .lemma-modal-card {
    background-color: var(--popup-bg, #ffffff);
    color: var(--text, #171a1c);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 12px;
    width: 100%;
    max-width: 760px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    padding: 1.25rem;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.25);
    box-sizing: border-box;
  }

  .lemma-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border, #d4d8d3);
    padding-bottom: 0.75rem;
    margin-bottom: 1rem;
    gap: 1rem;
  }

  .header-left {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .lemma-title {
    font-family: var(--font-greek, "Cardo", serif);
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent, #1f6f7a);
    margin: 0;
  }

  .count-badge {
    background-color: var(--accent, #1f6f7a);
    color: #ffffff;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 0.2rem 0.65rem;
    border-radius: 12px;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .toggle-all-btn {
    background: transparent;
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 6px;
    padding: 0.25rem 0.65rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent, #1f6f7a);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .toggle-all-btn:hover {
    background-color: var(--page-bg, #eceee7);
  }

  .close-btn {
    background: transparent;
    border: none;
    color: var(--text-mid, #545b5c);
    font-size: 1.5rem;
    cursor: pointer;
    line-height: 1;
    padding: 0.2rem 0.4rem;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  .close-btn:hover {
    background-color: var(--page-bg, #eceee7);
    color: var(--text, #171a1c);
  }

  .lemma-modal-body {
    overflow-y: auto;
    flex: 1;
    padding-right: 0.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .status-card {
    background-color: var(--col-bg, #f8f9f6);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    color: var(--text-mid, #545b5c);
    font-size: 0.95rem;
  }

  .error-card {
    color: #c53030;
    border-color: #feb2b2;
    background-color: #fff5f5;
  }

  .work-group {
    background: var(--col-bg, #f8f9f6);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 10px;
    overflow: hidden;
  }

  .work-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background-color: var(--page-bg, #eceee7);
    font-weight: 700;
    cursor: pointer;
    user-select: none;
    transition: background-color 0.15s ease;
  }

  .work-summary:hover {
    background-color: var(--border, #d4d8d3);
  }

  .work-title {
    font-size: 1rem;
    color: var(--accent, #1f6f7a);
  }

  .work-abbrev {
    font-weight: 400;
    color: var(--text-mid, #545b5c);
    font-size: 0.88rem;
  }

  .work-count-tag {
    font-size: 0.75rem;
    font-weight: 700;
    background: var(--accent, #1f6f7a);
    color: #ffffff;
    padding: 0.15rem 0.5rem;
    border-radius: 10px;
  }

  .work-content {
    padding: 0.85rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .book-group {
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    background-color: var(--popup-bg, #ffffff);
  }

  .book-summary {
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text-mid, #545b5c);
    cursor: pointer;
    user-select: none;
    padding: 0.25rem 0;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .book-summary:hover {
    color: var(--accent, #1f6f7a);
  }

  .book-count-tag {
    font-size: 0.75rem;
    color: var(--text-mid, #545b5c);
    font-weight: 500;
  }

  .pills-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem 0.55rem;
    padding-top: 0.5rem;
    padding-bottom: 0.25rem;
  }

  .occ-link {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.3rem 0.75rem;
    border-radius: 9999px;
    background-color: var(--page-bg, #eceee7);
    border: 1px solid var(--border, #d4d8d3);
    text-decoration: none;
    color: var(--text, #171a1c);
    font-size: 0.82rem;
    line-height: 1.2;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    transition: all 0.18s ease-in-out;
  }

  .occ-link:hover {
    background-color: var(--accent, #1f6f7a) !important;
    border-color: var(--accent, #1f6f7a) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(31, 111, 122, 0.3);
  }

  .occ-ref {
    font-weight: 700;
    color: var(--accent, #1f6f7a);
    font-size: 0.8rem;
    transition: color 0.18s ease-in-out;
  }

  .occ-link:hover .occ-ref {
    color: rgba(255, 255, 255, 0.92) !important;
  }

  .occ-form {
    font-family: var(--font-greek, "Cardo", "Gentium Plus", "Noto Serif", Georgia, serif);
    font-size: 0.98rem;
    font-weight: 600;
    color: var(--text, #171a1c);
    transition: color 0.18s ease-in-out;
  }

  .occ-link:hover .occ-form {
    color: #ffffff !important;
  }
</style>
