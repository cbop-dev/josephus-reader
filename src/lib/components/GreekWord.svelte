<script lang="ts">
  import {
    morphEnabled,
    selectedWord,
    showLexiconModal,
    type SelectedWordInfo
  } from '$lib/stores/readerStore';

  let {
    word = '',
    morphMap = {},
    dict = {}
  } = $props<{
    word?: string;
    morphMap?: Record<string, { lemma: string; parse: string; desc: string }>;
    dict?: Record<string, { key?: string; def: string }>;
  }>();

  function stripAccents(text: string): string {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/ς/g, 'σ');
  }

  let morphInfo = $derived(morphMap[word] || { lemma: word, parse: 'Form', desc: 'Greek word form' });
  
  let lemmaDef = $derived(
    dict[morphInfo.lemma]?.def ||
    dict[stripAccents(morphInfo.lemma)]?.def ||
    dict[word]?.def ||
    dict[stripAccents(word)]?.def ||
    ''
  );

  let showTooltip = $state(false);

  function handleClick(e: MouseEvent) {
    if (!$morphEnabled) return;
    e.stopPropagation();

    const info: SelectedWordInfo = {
      word,
      lemma: morphInfo.lemma,
      parse: morphInfo.parse,
      desc: morphInfo.desc,
      definition: lemmaDef
    };

    $selectedWord = info;
    $showLexiconModal = true;
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<span
  class="greek-word"
  class:interactive={$morphEnabled}
  onclick={handleClick}
  onmouseenter={() => (showTooltip = true)}
  onmouseleave={() => (showTooltip = false)}
>
  {word}
  {#if $morphEnabled && showTooltip}
    <span class="morph-badge">
      <span class="badge-lemma">{morphInfo.lemma}</span>
      <span class="badge-parse">{morphInfo.parse}</span>
    </span>
  {/if}
</span>

<style>
  .greek-word {
    font-family: var(--font-greek);
    position: relative;
    display: inline-block;
    cursor: default;
    border-bottom: 1px transparent solid;
    transition: all 0.15s ease;
  }

  .greek-word.interactive {
    cursor: pointer;
    border-bottom: 1px dotted var(--accent-color);
  }

  .greek-word.interactive:hover {
    color: var(--accent-color);
    background-color: var(--accent-light);
    border-radius: 2px;
  }

  .morph-badge {
    position: absolute;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    background-color: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-md);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-family: var(--font-sans);
    font-size: 0.75rem;
    white-space: nowrap;
    z-index: 50;
    pointer-events: none;
    display: flex;
    gap: 0.4rem;
    align-items: center;
  }

  .badge-lemma {
    font-weight: 700;
    color: var(--accent-color);
    font-family: var(--font-greek);
  }

  .badge-parse {
    color: var(--text-muted);
    font-size: 0.7rem;
    background-color: var(--bg-secondary);
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
  }
</style>
