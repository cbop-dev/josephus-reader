<script lang="ts">
  import { onMount } from 'svelte';
  import { transliterateLatinToGreek, normalizeGreekSearch, getKwicSnippet } from '../lib/transliterate';
  import { getWork } from '../lib/works';
  import { getBase, fetchLemmaData, type LemmaEntryData, type LemmaOccurrence } from '../lib/data';
  import {
    getHighlights,
    togglePhraseHighlight,
    isPhraseHighlighted,
    toggleLemmaHighlight,
    isLemmaHighlighted,
    toggleFormHighlight,
    isFormHighlighted,
    removeLemmaHighlight,
    removeFormHighlight,
    removePhraseHighlight,
    clearAllHighlights,
    normalizeKey,
    normalizeLemmaAccents,
    getCanonicalAttestedForms,
    type HighlightStore
  } from '../lib/highlights';

  import LemmaInfoCard from './LemmaInfoCard.svelte';
  import AttestedFormsGrid from './AttestedFormsGrid.svelte';
  import OccurrenceTree from './OccurrenceTree.svelte';

  export interface SearchSectionItem {
    w: string;
    b: number;
    s: string;
    g: string;
    n: string;
    e: string;
  }

  export interface LemmaIndexItem {
    l: string;
    n: string;
    c: number;
    g: string;
  }

  let {
    work = 'Antiquities',
    bookNum = 1,
    initialTab = 'lemma',
    initialQuery = '',
    initialLemmaNorm = '',
    initialLemmaDisplay = '',
    onClose = () => {}
  }: {
    work?: string;
    bookNum?: number;
    initialTab?: 'lemma' | 'custom' | 'highlights';
    initialQuery?: string;
    initialLemmaNorm?: string;
    initialLemmaDisplay?: string;
    onClose?: () => void;
  } = $props();

  let activeTab = $state<'lemma' | 'custom' | 'highlights'>(initialTab);
  let lemmaInputText = $state(initialTab === 'lemma' && initialQuery ? transliterateLatinToGreek(initialQuery) : '');
  let customInputText = $state(initialTab === 'custom' && initialQuery ? transliterateLatinToGreek(initialQuery) : '');
  let caseSensitive = $state(false);
  let loadingData = $state(true);

  let searchIndex = $state<SearchSectionItem[]>([]);
  let lemmataIndex = $state<LemmaIndexItem[]>([]);

  let selectedLemma = $state<LemmaIndexItem | null>(null);
  let lemmaData = $state<LemmaEntryData | null>(null);
  let loadingLemmaData = $state(false);
  let selectedFormFilter = $state<string | null>(null);

  let highlightsStore = $state<HighlightStore>({ lemmas: [], forms: [], phrases: [] });

  let totalActiveHighlights = $derived(
    highlightsStore.lemmas.length +
      highlightsStore.forms.length +
      (highlightsStore.phrases?.length || 0)
  );

  function notifyHighlightsChanged() {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('reader-highlights-changed', { detail: highlightsStore }));
    }
  }

  function handleRemoveLemmaHighlight(lemma: string) {
    removeLemmaHighlight(lemma);
    highlightsStore = getHighlights();
    notifyHighlightsChanged();
  }

  function handleRemoveFormHighlight(word: string) {
    removeFormHighlight(word);
    highlightsStore = getHighlights();
    notifyHighlightsChanged();
  }

  function handleRemovePhraseHighlight(phrase: string) {
    removePhraseHighlight(phrase);
    highlightsStore = getHighlights();
    notifyHighlightsChanged();
  }

  function handleClearAllHighlights() {
    clearAllHighlights();
    highlightsStore = getHighlights();
    notifyHighlightsChanged();
  }

  let rawInput = $derived(activeTab === 'lemma' ? lemmaInputText : customInputText);
  let normQuery = $derived(normalizeGreekSearch(rawInput));

  function handleInput(e: Event) {
    const target = e.target as HTMLInputElement;
    const val = target.value;
    const transformed = transliterateLatinToGreek(val);
    if (activeTab === 'lemma') {
      lemmaInputText = transformed;
    } else {
      customInputText = transformed;
    }
    target.value = transformed;
  }

  function clearInput() {
    if (activeTab === 'lemma') {
      lemmaInputText = '';
    } else {
      customInputText = '';
    }
  }

  function toggleFormFilter(fWord: string) {
    if (selectedFormFilter === fWord) {
      selectedFormFilter = null;
    } else {
      selectedFormFilter = fWord;
    }
  }

  onMount(() => {
    highlightsStore = getHighlights();
    loadIndexes();
  });

  async function loadIndexes() {
    loadingData = true;
    const base = getBase();
    try {
      const [searchRes, lemmataRes] = await Promise.all([
        fetch(`${base}/data/search_index.json`).then(r => r.ok ? r.json() : []),
        fetch(`${base}/data/lemmata_index.json`).then(r => r.ok ? r.json() : [])
      ]);
      searchIndex = Array.isArray(searchRes) ? searchRes : [];
      lemmataIndex = Array.isArray(lemmataRes) ? lemmataRes : [];
    } catch (err) {
      console.error('Failed to load search indexes:', err);
    } finally {
      loadingData = false;
    }
  }

  async function selectLemma(item: LemmaIndexItem) {
    selectedLemma = { ...item, l: normalizeLemmaAccents(item.l) };
    selectedFormFilter = null;
    loadingLemmaData = true;
    lemmaData = null;
    try {
      const data = await fetchLemmaData(item.n);
      lemmaData = data;
      if (data) {
        if (data.lemma && (!selectedLemma.l || selectedLemma.l === selectedLemma.n)) {
          selectedLemma.l = normalizeLemmaAccents(data.lemma);
        }
        if (data.count) {
          selectedLemma.c = data.count;
        }
      }
    } catch (err) {
      console.error('Failed to fetch lemma occurrence data:', err);
    } finally {
      loadingLemmaData = false;
    }
  }

  $effect(() => {
    if (initialLemmaNorm || initialLemmaDisplay) {
      const norm = normalizeKey(initialLemmaNorm || initialLemmaDisplay);
      if (norm && (!selectedLemma || selectedLemma.n !== norm)) {
        const display = initialLemmaDisplay || initialLemmaNorm;
        selectLemma({ l: display, n: norm, c: 0, g: '' });
      }
    }
  });

  function clearSelectedLemma() {
    selectedLemma = null;
    lemmaData = null;
    selectedFormFilter = null;
  }

  let filteredLemmata = $derived.by(() => {
    if (!normQuery) return lemmataIndex.slice(0, 150);
    return lemmataIndex.filter(item => {
      if (caseSensitive) {
        return item.l.includes(rawInput);
      }
      return item.n.includes(normQuery) || item.l.includes(rawInput);
    }).slice(0, 200);
  });

  let filteredCustomResults = $derived.by(() => {
    if (!normQuery || normQuery.length < 2) return [];
    
    return searchIndex.filter(item => {
      if (caseSensitive) {
        return item.g.includes(rawInput) || item.e.includes(rawInput);
      }
      return item.n.includes(normQuery) || item.e.toLowerCase().includes(rawInput.toLowerCase());
    });
  });

  let groupedResults = $derived.by(() => {
    const groups: Record<string, Record<number, SearchSectionItem[]>> = {};
    for (const item of filteredCustomResults) {
      if (!groups[item.w]) groups[item.w] = {};
      if (!groups[item.w][item.b]) groups[item.w][item.b] = [];
      groups[item.w][item.b].push(item);
    }
    return groups;
  });

  let filteredOccurrences = $derived.by(() => {
    if (!lemmaData || !lemmaData.occurrences) return [];
    if (!selectedFormFilter) return lemmaData.occurrences;
    const filterNorm = normalizeGreekSearch(selectedFormFilter);
    return lemmaData.occurrences.filter(occ => {
      const wNorm = normalizeGreekSearch(occ.word);
      return wNorm === filterNorm || occ.word.trim() === selectedFormFilter.trim();
    });
  });

  let lemmaOccurrencesGrouped = $derived.by(() => {
    const list = filteredOccurrences;
    if (!list || list.length === 0) return {};
    const groups: Record<string, Record<number, LemmaOccurrence[]>> = {};
    for (const occ of list) {
      const w = occ.work || 'Antiquities';
      const b = occ.book || 1;
      if (!groups[w]) groups[w] = {};
      if (!groups[w][b]) groups[w][b] = [];
      groups[w][b].push(occ);
    }
    return groups;
  });

  let selectedLemmaAttestedForms = $derived.by(() => {
    if (!lemmaData || !Array.isArray(lemmaData.occurrences)) return [];
    return getCanonicalAttestedForms(lemmaData.occurrences);
  });

  let sectionGrcMap = $derived.by(() => {
    const map = new Map<string, string>();
    if (!searchIndex || !Array.isArray(searchIndex)) return map;
    for (const item of searchIndex) {
      const key = `${item.w}-${item.b}-${item.s}`;
      map.set(key, item.g);
    }
    return map;
  });

  let isPhraseHl = $derived.by(() => {
    if (!rawInput) return false;
    const norm = normalizeKey(rawInput);
    return highlightsStore.phrases?.some(p => p.phrase === norm) || false;
  });

  function getLemmaOccKwic(occ: LemmaOccurrence): { before: string; match: string; after: string } {
    const key = `${occ.work}-${occ.book}-${occ.sec}`;
    const fullText = sectionGrcMap.get(key) || '';
    if (fullText) {
      const normQ = normalizeGreekSearch(occ.word);
      return getKwicSnippet(fullText, occ.word, normQ);
    }
    return { before: '', match: occ.word, after: '' };
  }

  let isLemmaHl = $derived.by(() => {
    if (!selectedLemma) return false;
    const norm = normalizeGreekSearch(selectedLemma.n || selectedLemma.l);
    return highlightsStore.lemmas.some(l => normalizeGreekSearch(l.lemma) === norm || l.lemma === norm);
  });

  let areLemmaGroupsExpanded = $state(true);
  let areCustomGroupsExpanded = $state(true);

  function toggleCollapseLemmaGroups(e?: Event) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    areLemmaGroupsExpanded = !areLemmaGroupsExpanded;
    if (typeof document !== 'undefined') {
      const tree = document.querySelector('.occurrences-tree');
      if (tree) {
        const detailsList = tree.querySelectorAll<HTMLDetailsElement>('details');
        detailsList.forEach(d => {
          d.open = areLemmaGroupsExpanded;
        });
      }
    }
  }

  function toggleCollapseCustomGroups(e?: Event) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    areCustomGroupsExpanded = !areCustomGroupsExpanded;
    if (typeof document !== 'undefined') {
      const tree = document.querySelector('.custom-results-tree');
      if (tree) {
        const detailsList = tree.querySelectorAll<HTMLDetailsElement>('details');
        detailsList.forEach(d => {
          d.open = areCustomGroupsExpanded;
        });
      }
    }
  }

  function handleTogglePhraseHighlight(phrase: string) {
    togglePhraseHighlight(phrase);
    highlightsStore = getHighlights();
  }

  function handleToggleLemmaHighlight(displayLemma: string, normLemma: string) {
    toggleLemmaHighlight(displayLemma, normLemma);
    highlightsStore = getHighlights();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      if (selectedLemma) {
        clearSelectedLemma();
      } else {
        onClose();
      }
    }
  }

  function navigateToSection(w: string, b: number, s: string) {
    onClose();
    const base = getBase();
    const workMeta = getWork(w);
    const targetUrl = `${base}/${workMeta?.id || w}/book/${b}/#niese-${s}`;
    if (typeof window !== 'undefined') {
      const currentPath = window.location.pathname;
      const targetPath = `${base}/${workMeta?.id || w}/book/${b}/`;
      const isSamePage = currentPath.replace(/\/$/, '') === targetPath.replace(/\/$/, '');

      if (isSamePage) {
        window.location.hash = `niese-${s}`;
        const cleanSec = String(s).trim();
        const numMatch = cleanSec.match(/^\d+/);
        const secNum = numMatch ? numMatch[0] : cleanSec;
        setTimeout(() => {
          const el = document.getElementById(`niese-${secNum}`) ||
                     document.querySelector(`[data-section="${secNum}"]`) ||
                     document.querySelector(`[data-niese="${cleanSec}"]`);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 60);
      } else {
        window.location.href = targetUrl;
      }
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="search-backdrop" onclick={onClose} role="presentation">
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div class="search-card" onclick={(e) => e.stopPropagation()} role="dialog" aria-label="Corpus Search / Highlight" tabindex="-1">
    <div class="search-header">
      <div class="search-header-title">
        <h2>Corpus Search / Highlight</h2>
        <span class="search-sub font-small">Search 30 books of Josephus or manage active highlights</span>
      </div>
      <button class="search-close-btn" onclick={onClose} aria-label="Close search">×</button>
    </div>

    <!-- Tabs strip -->
    <div class="search-tabs-strip">
      <button
        class="search-tab-btn"
        class:active={activeTab === 'lemma'}
        onclick={() => { activeTab = 'lemma'; clearSelectedLemma(); }}
      >
        🏛️ Lemma Search
      </button>
      <button
        class="search-tab-btn"
        class:active={activeTab === 'custom'}
        onclick={() => { activeTab = 'custom'; clearSelectedLemma(); }}
      >
        📖 Custom Text / Phrase Search
      </button>
      <button
        class="search-tab-btn"
        class:active={activeTab === 'highlights'}
        onclick={() => { activeTab = 'highlights'; clearSelectedLemma(); }}
      >
        🎨 Active Highlights {#if totalActiveHighlights > 0}<span class="tab-hl-badge">{totalActiveHighlights}</span>{/if}
      </button>
    </div>

    <!-- Live Transliteration Search Input -->
    {#if !selectedLemma && activeTab !== 'highlights'}
      <div class="search-input-wrapper">
        <div class="input-row">
          <input
            type="text"
            class="search-input"
            placeholder={activeTab === 'lemma' ? 'Type in Latin/Betacode (e.g. arche, iosephos) or Greek...' : 'Type custom word/phrase (e.g. ioudaion archontes)...'}
            value={rawInput}
            oninput={handleInput}
            autofocus
          />
          {#if rawInput}
            <button class="clear-input-btn" onclick={clearInput} aria-label="Clear input">✕</button>
          {/if}
        </div>

        <div class="search-options-row">
          <label class="case-sensitive-label">
            <input type="checkbox" bind:checked={caseSensitive} />
            <span>Case sensitive</span>
          </label>
        </div>
      </div>
    {/if}

    <!-- Body Content Area -->
    <div class="search-body">
      {#if loadingData}
        <div class="search-loading">Loading search index dataset...</div>
      {:else if activeTab === 'lemma'}
        <!-- Lemma Search Tab -->
        {#if selectedLemma}
          <!-- Lemma Detail & Textual Occurrences View -->
          <div class="lemma-detail-view">
            <div class="lemma-detail-nav">
              <button class="btn-back-lemma" onclick={clearSelectedLemma}>
                ← Back to Lemma Search
              </button>
            </div>

            <LemmaInfoCard
              lemmaNorm={selectedLemma.n}
              lemmaDisplay={selectedLemma.l}
              count={selectedLemma.c}
              gloss={selectedLemma.g}
            />

            <!-- Attested Word Forms Section -->
            {#if selectedLemmaAttestedForms.length > 0}
              <AttestedFormsGrid
                attestedForms={selectedLemmaAttestedForms}
                selectedFormFilter={selectedFormFilter}
                lemmaNorm={selectedLemma.n}
                lemmaDisplay={selectedLemma.l}
                onToggleFilter={toggleFormFilter}
              />
            {/if}

            <!-- Passages in Josephus Section -->
            <OccurrenceTree
              lemmaDisplay={selectedLemma.l}
              lemmaData={lemmaData}
              selectedFormFilter={selectedFormFilter}
              onClearFormFilter={() => (selectedFormFilter = null)}
              onNavigate={navigateToSection}
              loading={loadingLemmaData}
            />

          </div>
        {:else}
          <!-- Lemma Search List View -->
          <div class="lemma-results-list">
            {#if filteredLemmata.length === 0}
              <div class="search-empty-msg">No matching lemmata found.</div>
            {:else}
              {#each filteredLemmata as item (item.n)}
                <!-- svelte-ignore a11y_click_events_have_key_events -->
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div class="lemma-item-card" onclick={() => selectLemma(item)}>
                  <div class="lemma-item-left">
                    <span class="lemma-word-text">{normalizeLemmaAccents(item.l)}</span>
                    <span class="lemma-count-badge" title="Total occurrences in Josephus">{item.c} occ</span>
                  </div>
                  {#if item.g}
                    <div class="lemma-gloss-text">{item.g}</div>
                  {/if}
                  <div class="lemma-item-actions">
                    <button class="lemma-inspect-btn" onclick={(e) => { e.stopPropagation(); selectLemma(item); }}>
                      View Occurrences →
                    </button>
                  </div>
                </div>
              {/each}
            {/if}
          </div>
        {/if}
      {:else}
        <!-- Custom Phrase Search Tab -->
        {#if !normQuery || normQuery.length < 2}
          <div class="search-prompt-msg">
            Type at least 2 characters to search across all sections of Josephus.
          </div>
        {:else if filteredCustomResults.length === 0}
          <div class="search-empty-msg">
            No sections found matching "{rawInput}".
          </div>
        {:else}
          <div class="custom-results-summary">
            <span>Found <strong>{filteredCustomResults.length}</strong> matching section{filteredCustomResults.length === 1 ? '' : 's'}:</span>
            <div class="custom-results-actions">
              <button
                class="btn-collapse-all"
                onclick={toggleCollapseCustomGroups}
                title={areCustomGroupsExpanded ? "Collapse all work and book sections" : "Expand all work and book sections"}
              >
                {areCustomGroupsExpanded ? '⊟ Collapse All' : '⊞ Expand All'}
              </button>
              {#if rawInput}
                <button
                  class="phrase-hl-toggle-btn"
                  class:active={isPhraseHl}
                  onclick={() => handleTogglePhraseHighlight(rawInput)}
                >
                  {isPhraseHl ? '✓ Phrase Highlighted' : '+ Highlight Phrase Corpus-Wide'}
                </button>
              {/if}
            </div>
          </div>

          <div class="custom-results-tree">
            {#each Object.entries(groupedResults) as [workId, bookGroup] (workId)}
              {@const workMeta = getWork(workId)}
              <details open class="work-results-group">
                <summary class="work-results-title">{workMeta?.englishTitle || workId}</summary>
                {#each Object.entries(bookGroup) as [bNumStr, sections] (bNumStr)}
                  {@const bNum = Number(bNumStr)}
                  <details open class="book-results-group">
                    <summary class="book-results-title">Book {bNum} ({sections.length})</summary>
                    <div class="sections-results-list">
                      {#each sections as sec (sec.s)}
                        {@const kwic = getKwicSnippet(sec.g || sec.e, rawInput, normQuery)}
                        <!-- svelte-ignore a11y_click_events_have_key_events -->
                        <!-- svelte-ignore a11y_no_static_element_interactions -->
                        <div
                          class="sec-result-card"
                          onclick={() => navigateToSection(sec.w, sec.b, sec.s)}
                          title={`Jump to ${workMeta?.abbrev || sec.w} ${sec.b}.${sec.s}`}
                        >
                          <span class="sec-badge">{workMeta?.abbrev || sec.w} {sec.b}.{sec.s}</span>
                          <span class="sec-kwic-snippet">
                            {kwic.before}<mark class="kwic-mark">{kwic.match}</mark>{kwic.after}
                          </span>
                          <span class="sec-jump-hint">Jump →</span>
                        </div>
                      {/each}
                    </div>
                  </details>
                {/each}
              </details>
            {/each}
          </div>
        {/if}
      {:else if activeTab === 'highlights'}
        <!-- Active Highlights Tab -->
        <div class="active-highlights-panel">
          {#if totalActiveHighlights === 0}
            <div class="search-empty-msg">
              No active highlights. Click on any word in the reader text or search modal to highlight its lemma, exact form, or custom phrase.
            </div>
          {:else}
            {#if highlightsStore.lemmas.length > 0}
              <div class="hl-modal-section">
                <h3>(1) Lemma Highlights</h3>
                <div class="hl-chips-grid">
                  {#each highlightsStore.lemmas as l (l.lemma)}
                    <div class="hl-chip lemma-chip" style={`--chip-hue: ${l.hue}`}>
                      <span class="chip-color-dot"></span>
                      <span class="chip-text">{normalizeLemmaAccents(l.displayLemma)}</span>
                      <button
                        class="chip-remove-btn"
                        onclick={() => handleRemoveLemmaHighlight(l.lemma)}
                        aria-label={`Remove ${l.displayLemma} highlight`}
                      >×</button>
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
                      <button
                        class="chip-remove-btn"
                        onclick={() => handleRemoveFormHighlight(f.word)}
                        aria-label={`Remove ${f.displayWord} highlight`}
                      >×</button>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if highlightsStore.phrases && highlightsStore.phrases.length > 0}
              <div class="hl-modal-section">
                <h3>(3) Custom Phrase Highlights</h3>
                <div class="hl-chips-grid">
                  {#each highlightsStore.phrases as p (p.phrase)}
                    <div class="hl-chip phrase-chip" style={`--chip-hue: ${p.hue}`}>
                      <span class="chip-color-dot"></span>
                      <span class="chip-text">{p.displayPhrase}</span>
                      <button
                        class="chip-remove-btn"
                        onclick={() => handleRemovePhraseHighlight(p.displayPhrase)}
                        aria-label={`Remove ${p.displayPhrase} highlight`}
                      >×</button>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            <div class="hl-modal-footer">
              <button class="hl-clear-all-btn" onclick={handleClearAllHighlights}>
                Clear All Highlights
              </button>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  :global(.search-backdrop) {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(4px);
    z-index: 3000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
  }

  :global(.search-card) {
    background-color: var(--popup-bg, #ffffff);
    color: var(--text, #171a1c);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 12px;
    width: 100%;
    max-width: 760px;
    max-height: 88vh;
    display: flex;
    flex-direction: column;
    box-shadow: var(--popup-shadow, 0 15px 35px rgba(0, 0, 0, 0.25));
    overflow: hidden;
  }

  :global(.search-header) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border, #d4d8d3);
    background-color: var(--col-bg, #f5f6f2);
  }

  :global(.search-header-title h2) {
    margin: 0 0 0.15rem 0;
    font-size: 1.2rem;
    color: var(--accent, #1f6f7a);
    font-family: var(--font-english, "EB Garamond", serif);
  }

  :global(.search-sub) {
    font-size: 0.82rem;
    color: var(--text-mid, #545b5c);
  }

  :global(.search-close-btn) {
    background: transparent;
    border: none;
    font-size: 1.6rem;
    line-height: 1;
    color: var(--text-mid, #545b5c);
    cursor: pointer;
    padding: 0 0.4rem;
    border-radius: 4px;
  }

  :global(.search-close-btn:hover) {
    color: var(--text, #171a1c);
    background: var(--border, #d4d8d3);
  }

  :global(.search-tabs-strip) {
    display: flex;
    gap: 0.4rem;
    background: var(--page-bg, #eceee7);
    padding: 6px;
    border-bottom: 1px solid var(--border, #d4d8d3);
  }

  :global(.search-tab-btn) {
    flex: 1;
    background: transparent;
    border: none;
    padding: 0.5rem 0.75rem;
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-mid, #545b5c);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
  }

  :global(.search-tab-btn:hover) {
    color: var(--text, #171a1c);
    background: var(--col-bg, #ffffff);
  }

  :global(.search-tab-btn.active) {
    background: var(--accent, #1f6f7a);
    color: #ffffff;
    box-shadow: 0 2px 6px rgba(31, 111, 122, 0.25);
  }

  :global(.search-input-wrapper) {
    padding: 1rem 1.25rem 0.6rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    background: var(--col-bg, #f5f6f2);
    border-bottom: 1px solid var(--border, #d4d8d3);
  }

  :global(.input-row) {
    position: relative;
    display: flex;
    align-items: center;
  }

  :global(.search-input) {
    width: 100%;
    padding: 0.6rem 2.2rem 0.6rem 0.85rem;
    font-size: 1.15rem;
    font-family: var(--font-greek, "Cardo", "EB Garamond", serif);
    background: var(--popup-bg, #ffffff);
    color: var(--text, #171a1c);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 6px;
    outline: none;
    transition: border-color 0.15s ease;
  }

  :global(.search-input:focus) {
    border-color: var(--accent, #1f6f7a);
    box-shadow: 0 0 0 2px rgba(31, 111, 122, 0.2);
  }

  :global(.clear-input-btn) {
    position: absolute;
    right: 0.6rem;
    background: none;
    border: none;
    font-size: 0.9rem;
    color: var(--text-mid, #545b5c);
    cursor: pointer;
  }

  :global(.search-options-row) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.82rem;
    color: var(--text-mid, #545b5c);
  }

  :global(.case-sensitive-label) {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    cursor: pointer;
    user-select: none;
  }

  :global(.search-body) {
    padding: 1.25rem;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  :global(.search-loading),
  :global(.search-prompt-msg),
  :global(.search-empty-msg) {
    text-align: center;
    padding: 2.5rem 1rem;
    color: var(--text-mid, #545b5c);
    font-size: 0.95rem;
  }

  :global(.lemma-results-list) {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  :global(.lemma-item-card) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    background: var(--page-bg, #eceee7);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 8px;
    gap: 0.75rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global(.lemma-item-card:hover) {
    border-color: var(--accent, #1f6f7a);
    background: var(--col-bg, #ffffff);
  }

  :global(.lemma-item-left) {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

  :global(.lemma-word-text) {
    font-family: var(--font-greek, "Cardo", Georgia, serif);
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--accent, #1f6f7a);
  }

  :global(.lemma-count-badge) {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.18rem 0.5rem;
    border-radius: 10px;
    background: var(--accent, #1f6f7a);
    color: #ffffff;
  }

  :global(.lemma-gloss-text) {
    font-size: 0.88rem;
    color: var(--text-mid, #545b5c);
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  :global(.lemma-inspect-btn) {
    background: var(--col-bg, #ffffff);
    border: 1px solid var(--border, #d4d8d3);
    color: var(--accent, #1f6f7a);
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.3rem 0.65rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global(.lemma-inspect-btn:hover) {
    background: var(--accent, #1f6f7a);
    color: #ffffff;
  }

  :global(.lemma-detail-view) {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  :global(.lemma-detail-nav) {
    display: flex;
    align-items: center;
  }

  :global(.btn-back-lemma) {
    background: transparent;
    border: none;
    color: var(--accent, #1f6f7a);
    font-size: 0.88rem;
    font-weight: 600;
    cursor: pointer;
    padding: 0.2rem 0;
  }

  :global(.btn-back-lemma:hover) {
    text-decoration: underline;
  }

  :global(.lemma-detail-card) {
    background: var(--col-bg, #f5f6f2);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 8px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  :global(.lemma-detail-header) {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  :global(.lemma-title-group) {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  :global(.selected-lemma-word) {
    font-family: var(--font-greek, "Cardo", Georgia, serif);
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent, #1f6f7a);
  }

  :global(.selected-lemma-gloss) {
    font-size: 0.95rem;
    font-style: italic;
    color: var(--text-mid, #545b5c);
  }

  :global(.lemma-detail-actions) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  :global(.occurrences-title) {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    color: var(--accent, #1f6f7a);
    border-bottom: 1px solid var(--border, #d4d8d3);
    padding-bottom: 0.3rem;
  }

  :global(.occurrences-tree) {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  :global(.custom-results-summary) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.9rem;
    color: var(--text, #171a1c);
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border, #d4d8d3);
  }

  :global(.summary-title-group) {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

  :global(.custom-results-actions) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  :global(.btn-collapse-all) {
    background: rgba(31, 111, 122, 0.08);
    border: 1px solid var(--border, #d4d8d3);
    color: var(--accent, #1f6f7a);
    font-size: 0.76rem;
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
  }

  :global(.btn-collapse-all:hover) {
    background: var(--accent, #1f6f7a);
    color: #ffffff;
    border-color: var(--accent, #1f6f7a);
  }

  :global(.phrase-hl-toggle-btn) {
    background: var(--page-bg, #eceee7);
    border: 1px solid var(--border, #d4d8d3);
    color: var(--text-mid, #545b5c);
    font-size: 0.78rem;
    font-weight: 600;
    padding: 0.25rem 0.6rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global(.phrase-hl-toggle-btn.active) {
    background: var(--accent, #1f6f7a);
    color: #ffffff;
    border-color: var(--accent, #1f6f7a);
  }

  :global(.custom-results-tree) {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  :global(.work-results-title) {
    margin: 0 0 0.4rem 0;
    font-size: 1.05rem;
    color: var(--accent, #1f6f7a);
    border-bottom: 1px solid var(--border, #d4d8d3);
    padding-bottom: 0.2rem;
  }

  :global(.book-results-title) {
    margin: 0.4rem 0 0.3rem 0;
    font-size: 0.88rem;
    color: var(--text-mid, #545b5c);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  :global(.sections-results-list) {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    max-height: 420px;
    overflow-y: auto;
    padding-right: 0.2rem;
  }

  :global(.sec-result-card) {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: var(--page-bg, #eceee7);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 4px;
    padding: 0.25rem 0.55rem;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
    min-height: 30px;
  }

  :global(.sec-result-card:hover) {
    border-color: var(--accent, #1f6f7a);
    background: var(--col-bg, #ffffff);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  }

  :global(.sec-badge) {
    flex-shrink: 0;
    font-weight: 700;
    font-size: 0.78rem;
    color: var(--accent, #1f6f7a);
    background: rgba(31, 111, 122, 0.08);
    padding: 0.1rem 0.45rem;
    border-radius: 3px;
    white-space: nowrap;
  }

  :global(.sec-jump-hint) {
    flex-shrink: 0;
    font-size: 0.75rem;
    color: var(--text-mid, #545b5c);
    white-space: nowrap;
    opacity: 0.75;
    transition: opacity 0.15s ease;
  }

  :global(.sec-result-card:hover .sec-jump-hint) {
    opacity: 1;
    color: var(--accent, #1f6f7a);
  }

  :global(.sec-kwic-snippet) {
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-family: var(--font-greek, "Cardo", Georgia, serif);
    font-size: 0.92rem;
    color: var(--text, #171a1c);
  }

  :global(.kwic-mark) {
    background-color: #fef08a;
    color: #171a1c;
    font-weight: 700;
    padding: 0 0.15rem;
    border-radius: 2px;
  }

  :global(.lemma-details-section) {
    background: var(--col-bg, #ffffff);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 8px;
    margin-bottom: 0.9rem;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }

  :global(.lemma-section-summary) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.65rem 0.9rem;
    background: var(--page-bg, #f4f6f0);
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--accent, #1f6f7a);
    cursor: pointer;
    user-select: none;
    transition: background 0.15s ease;
  }

  :global(.lemma-section-summary:hover) {
    background: var(--border, #e2e6e0);
  }

  :global(.section-count-badge) {
    background: var(--accent, #1f6f7a);
    color: #ffffff;
    font-size: 0.75rem;
    padding: 0.15rem 0.55rem;
    border-radius: 12px;
    font-weight: 600;
  }

  :global(.forms-chips-wrapper) {
    padding: 0.75rem 0.9rem;
  }

  :global(.forms-chips-grid) {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    max-height: 130px;
    overflow-y: auto;
    padding: 0.2rem;
  }

  :global(.form-chip-pill) {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: var(--page-bg, #eceee7);
    border: 1px solid var(--border, #d4d8d3);
    color: var(--text, #171a1c);
    border-radius: 6px;
    padding: 0.2rem 0.45rem;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
  }

  :global(.form-chip-pill:hover) {
    border-color: var(--accent, #1f6f7a);
    background: var(--col-bg, #ffffff);
    transform: translateY(-1px);
  }

  :global(.form-chip-pill.filter-active) {
    border-color: var(--accent, #1f6f7a);
    background-color: var(--col-bg, #ffffff);
    box-shadow: 0 0 0 2px rgba(31, 111, 122, 0.25);
    font-weight: 700;
  }

  :global(.chip-word-text) {
    font-family: var(--font-greek, "Cardo", Georgia, serif);
    font-size: 0.95rem;
  }

  :global(.chip-hl-badge) {
    appearance: none;
    -webkit-appearance: none;
    outline: none;
    border: none;
    background: rgba(0, 0, 0, 0.08);
    color: var(--text-mid, #545b5c);
    width: 18px;
    height: 18px;
    border-radius: 50%;
    font-size: 0.68rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global(.chip-hl-badge:hover) {
    background: var(--accent, #1f6f7a);
    color: #ffffff;
    transform: scale(1.1);
  }

  :global(.chip-hl-badge.active) {
    background-color: var(--accent, #1f6f7a);
    color: #ffffff;
    font-weight: 700;
    box-shadow: 0 1px 3px rgba(31, 111, 122, 0.5);
  }

  :global(.form-filter-active-bar) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: #e0f2fe;
    border: 1px solid #7dd3fc;
    color: #0369a1;
    border-radius: 6px;
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.75rem;
    font-size: 0.88rem;
  }

  :global(.clear-form-filter-btn) {
    background: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 0.2rem 0.55rem;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  :global(.clear-form-filter-btn:hover) {
    background: #0369a1;
  }

  :global(.lemma-occurrences-body) {
    padding: 0.75rem 0.9rem;
  }

  :global(.tab-hl-badge) {
    background: #0284c7;
    color: #ffffff;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.05rem 0.4rem;
    border-radius: 10px;
    margin-left: 0.3rem;
  }

  :global(.active-highlights-panel) {
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  :global(.hl-modal-section) {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  :global(.hl-modal-section h3) {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-mid, #545b5c);
  }

  :global(.hl-chips-grid) {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  :global(.hl-chip) {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--page-bg, #eceee7);
    border: 1px solid var(--border, #d4d8d3);
    border-radius: 6px;
    padding: 0.25rem 0.6rem;
    font-size: 0.9rem;
  }

  :global(.chip-color-dot) {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: hsl(var(--chip-hue, 160), 85%, 45%);
    display: inline-block;
  }

  :global(.chip-text) {
    font-family: var(--font-greek, "Cardo", Georgia, serif);
    font-weight: 600;
  }

  :global(.chip-remove-btn) {
    background: transparent;
    border: none;
    color: var(--text-mid, #545b5c);
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    padding: 0 0.15rem;
    border-radius: 3px;
    transition: all 0.15s ease;
  }

  :global(.chip-remove-btn:hover) {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
  }

  :global(.hl-modal-footer) {
    display: flex;
    justify-content: flex-end;
    padding-top: 0.5rem;
    border-top: 1px solid var(--border, #d4d8d3);
  }

  :global(.hl-clear-all-btn) {
    background: #dc2626;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 0.4rem 0.85rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  :global(.hl-clear-all-btn:hover) {
    background: #b91c1c;
  }
</style>
