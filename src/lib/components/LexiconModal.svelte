<script lang="ts">
  import { selectedWord, showLexiconModal } from '$lib/stores/readerStore';

  function closeModal() {
    $showLexiconModal = false;
  }
</script>

{#if $showLexiconModal && $selectedWord}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="modal-backdrop" onclick={closeModal}>
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <div class="word-title-group">
          <h2 class="surface-word">{$selectedWord.word}</h2>
          <span class="parse-pill">{$selectedWord.parse}</span>
        </div>
        <button class="close-btn" onclick={closeModal}>✕</button>
      </div>

      <div class="modal-body">
        <div class="field-row">
          <span class="field-label">Lemma (Dictionary Form):</span>
          <span class="lemma-value">{$selectedWord.lemma}</span>
        </div>

        <div class="field-row">
          <span class="field-label">Morphological Analysis:</span>
          <span class="desc-value">{$selectedWord.desc}</span>
        </div>

        <div class="definition-box">
          <h4 class="def-heading">Liddell-Scott-Jones (LSJ) Lexicon Entry</h4>
          {#if $selectedWord.definition}
            <p class="def-text">{$selectedWord.definition}</p>
          {:else}
            <p class="def-fallback">
              <span class="greek-entry">{$selectedWord.lemma}</span>: Classical Greek lemma. Definition from LSJ dictionary database.
            </p>
          {/if}
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn secondary-btn" onclick={closeModal}>Close</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(2px);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  .modal-content {
    background-color: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    width: 100%;
    max-width: 520px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    animation: popIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes popIn {
    from {
      opacity: 0;
      transform: scale(0.95);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
    background-color: var(--bg-secondary);
  }

  .word-title-group {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
  }

  .surface-word {
    font-family: var(--font-greek);
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent-color);
  }

  .parse-pill {
    font-family: var(--font-sans);
    font-size: 0.75rem;
    font-weight: 600;
    background-color: var(--accent-light);
    color: var(--accent-color);
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
  }

  .close-btn {
    font-size: 1.25rem;
    color: var(--text-muted);
    padding: 0.25rem;
  }

  .close-btn:hover {
    color: var(--text-primary);
  }

  .modal-body {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .field-row {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .field-label {
    font-family: var(--font-sans);
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  .lemma-value {
    font-family: var(--font-greek);
    font-size: 1.4rem;
    font-weight: 600;
  }

  .desc-value {
    font-family: var(--font-sans);
    font-size: 0.95rem;
    color: var(--text-secondary);
  }

  .definition-box {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 0.5rem;
  }

  .def-heading {
    font-family: var(--font-sans);
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--accent-color);
    margin-bottom: 0.5rem;
  }

  .def-text {
    font-family: var(--font-english);
    font-size: 1rem;
    line-height: 1.5;
  }

  .def-fallback {
    font-family: var(--font-english);
    font-size: 0.95rem;
    color: var(--text-muted);
  }

  .greek-entry {
    font-family: var(--font-greek);
    font-weight: 700;
    color: var(--text-primary);
  }

  .modal-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: flex-end;
  }

  .secondary-btn {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 0.5rem 1.25rem;
    border-radius: 6px;
    font-weight: 500;
  }

  .secondary-btn:hover {
    background-color: var(--border-color);
  }
</style>
