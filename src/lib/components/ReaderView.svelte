<script lang="ts">
  import {
    viewMode,
    morphEnabled,
    fontSize,
    searchQuery
  } from '$lib/stores/readerStore';
  import GreekWord from './GreekWord.svelte';
  import SectionNavPill from './SectionNavPill.svelte';

  let {
    bookData = null,
    morphMap = {},
    dict = {}
  } = $props<{
    bookData?: any;
    morphMap?: Record<string, { lemma: string; parse: string; desc: string }>;
    dict?: Record<string, { key?: string; def: string }>;
  }>();

  let sections = $derived(bookData?.sections || []);

  let filteredSections = $derived(
    $searchQuery.trim()
      ? sections.filter((sec: any) => {
          const q = $searchQuery.toLowerCase();
          return (
            sec.niese.includes(q) ||
            sec.grc.toLowerCase().includes(q) ||
            sec.eng.toLowerCase().includes(q)
          );
        })
      : sections
  );

  function tokenizeGreek(text: string): { type: 'word' | 'section_num' | 'text'; val: string }[] {
    if (!text) return [];
    // Tokenize into section markers [123], words, and punctuation
    const tokens: { type: 'word' | 'section_num' | 'text'; val: string }[] = [];
    const parts = text.split(/(\[\d+\]|[\w\u0370-\u03FF\u1F00-\u1FFF]+)/g);
    
    for (const p of parts) {
      if (!p) continue;
      if (/^\[\d+\]$/.test(p)) {
        tokens.push({ type: 'section_num', val: p.slice(1, -1) });
      } else if (/^[\w\u0370-\u03FF\u1F00-\u1FFF]+$/.test(p)) {
        tokens.push({ type: 'word', val: p });
      } else {
        tokens.push({ type: 'text', val: p });
      }
    }
    return tokens;
  }
</script>

<div class="reader-container" style="--reader-font-size: {$fontSize}px;">
  {#if !bookData}
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading text data...</p>
    </div>
  {:else if filteredSections.length === 0}
    <div class="empty-state">
      <p>No matching sections found for "{$searchQuery}".</p>
    </div>
  {:else}
    <div class="sections-wrapper mode-{$viewMode}">
      {#each filteredSections as sec (sec.niese)}
        <div class="section-row" id="sec-{sec.niese}">
          <!-- Section Range Badge Marker -->
          <div class="section-anchor">
            <span class="sec-badge">§ {sec.niese}</span>
          </div>

          <!-- Parallel View: Side by Side Aligned -->
          {#if $viewMode === 'parallel'}
            <div class="columns-grid">
              <!-- Left Column: Greek -->
              <div class="col greek-col">
                <div class="text-body greek-body">
                  {#each tokenizeGreek(sec.grc) as token}
                    {#if token.type === 'section_num'}
                      <span class="inline-sec-tag" title="Niese Section {token.val}">§ {token.val}</span>
                    {:else if token.type === 'word'}
                      <GreekWord word={token.val} {morphMap} {dict} />
                    {:else}
                      {token.val}
                    {/if}
                  {/each}
                </div>
              </div>

              <!-- Right Column: English -->
              <div class="col english-col">
                <div class="text-body english-body">
                  {sec.eng}
                </div>
              </div>
            </div>

          <!-- Greek Only View -->
          {:else if $viewMode === 'greek'}
            <div class="single-col greek-only">
              <div class="text-body greek-body">
                {#each tokenizeGreek(sec.grc) as token}
                  {#if token.type === 'section_num'}
                    <span class="inline-sec-tag">§ {token.val}</span>
                  {:else if token.type === 'word'}
                    <GreekWord word={token.val} {morphMap} {dict} />
                  {:else}
                    {token.val}
                  {/if}
                {/each}
              </div>
            </div>

          <!-- English Only View -->
          {:else if $viewMode === 'english'}
            <div class="single-col english-only">
              <div class="text-body english-body">
                {sec.eng}
              </div>
            </div>

          <!-- Stacked Verse-by-Verse View -->
          {:else if $viewMode === 'stacked'}
            <div class="stacked-block">
              <div class="text-body greek-body stacked-grc">
                {#each tokenizeGreek(sec.grc) as token}
                  {#if token.type === 'section_num'}
                    <span class="inline-sec-tag">§ {token.val}</span>
                  {:else if token.type === 'word'}
                    <GreekWord word={token.val} {morphMap} {dict} />
                  {:else}
                    {token.val}
                  {/if}
                {/each}
              </div>
              <div class="text-body english-body stacked-eng">
                {sec.eng}
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
    <SectionNavPill sections={filteredSections} />
  {/if}
</div>

<style>
  .reader-container {
    max-width: 1300px;
    margin: 0 auto;
    padding: 1.5rem;
    min-height: 80vh;
  }

  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem;
    color: var(--text-muted);
    gap: 1rem;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-color);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .sections-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .section-row {
    position: relative;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 1.25rem;
  }

  .section-anchor {
    margin-bottom: 0.5rem;
  }

  .sec-badge {
    font-family: var(--font-sans);
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--accent-color);
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
  }

  .inline-sec-tag {
    font-family: var(--font-sans);
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--accent-color);
    background-color: var(--accent-light);
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
    margin: 0 0.25rem;
    vertical-align: middle;
  }

  /* Parallel 2-Column Grid */
  .columns-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    align-items: start;
  }

  .col {
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow-sm);
  }

  .single-col {
    max-width: 800px;
    margin: 0 auto;
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem 2rem;
    box-shadow: var(--shadow-sm);
  }

  .stacked-block {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
  }

  .stacked-eng {
    border-top: 1px dashed var(--border-color);
    padding-top: 0.75rem;
    color: var(--text-secondary);
    font-style: italic;
  }

  .greek-body {
    font-family: var(--font-greek);
    font-size: calc(var(--reader-font-size, 19px) * 1.05);
    line-height: 1.8;
  }

  .english-body {
    font-family: var(--font-english);
    font-size: var(--reader-font-size, 19px);
    line-height: 1.75;
  }

  /* Responsive Adjustments for Mobile */
  @media (max-width: 900px) {
    .columns-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }
  }
</style>
