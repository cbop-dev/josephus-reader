<script lang="ts">
  import { showAttributionModal } from '$lib/stores/readerStore';

  function closeModal() {
    $showAttributionModal = false;
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeModal();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if $showAttributionModal}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="modal-backdrop" onclick={closeModal}>
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <div class="modal-title-group">
          <span class="info-icon">🛈</span>
          <h2 class="modal-title">Source Data & Attribution Info</h2>
        </div>
        <button class="close-btn" onclick={closeModal} aria-label="Close modal">✕</button>
      </div>

      <div class="modal-body">
        <section class="info-section">
          <h3 class="section-heading">Perseus Digital Library</h3>
          <p class="section-text">
            The Greek and English texts in this application are derived from XML data provided by the 
            <a href="https://github.com/PerseusDL" target="_blank" rel="noopener noreferrer">Perseus Digital Library project</a>.
          </p>
        </section>

        <section class="info-section">
          <h3 class="section-heading">Editions & Translations</h3>
          <ul class="edition-list">
            <li>
              <strong>Greek Text:</strong> 
              <em>Flavii Iosephi Opera</em>, Vol. 1–4. Edited by Benedikt Niese. Berlin: Weidmann, 1885–1890. (Public Domain)
            </li>
            <li>
              <strong>English Translation:</strong> 
              <em>The Works of Flavius Josephus</em>. Translated by William Whiston. Auburn and Rochester, NY: Alden and Beardsley, 1856. (Public Domain)
            </li>
          </ul>
        </section>

        <section class="info-section">
          <h3 class="section-heading">License & Open Access</h3>
          <p class="section-text">
            The texts from Perseus are licensed under the 
            <a 
              href="https://creativecommons.org/licenses/by-sa/4.0/us/" 
              target="_blank" 
              rel="noopener noreferrer"
              class="license-link"
            >
              Creative Commons Attribution-ShareAlike 4.0 United States License (CC BY-SA 4.0 US)
            </a>.
          </p>
          <p class="section-subtext">
            In accordance with the ShareAlike terms of this license, any modifications or derivative works of these texts remain open and available under the same license terms.
          </p>
        </section>

        <section class="info-section">
          <h3 class="section-heading">External Reader</h3>
          <p class="section-text">
            You can also view these texts on Tufts University's 
            <a 
              href="https://scaife.perseus.org/library/urn:cts:greekLit:tlg0526/" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Scaife Viewer
            </a>.
          </p>
        </section>
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
    background-color: rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(3px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }

  .modal-content {
    background-color: var(--bg-card, #ffffff);
    color: var(--text-color, #222222);
    border: 1px solid var(--border-color, #e0e0e0);
    border-radius: 12px;
    width: 100%;
    max-width: 600px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    overflow: hidden;
  }

  .modal-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: var(--secondary-bg, #f8f9fa);
  }

  .modal-title-group {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

  .info-icon {
    font-size: 1.3rem;
    color: var(--accent-color, #4a6fa5);
  }

  .modal-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text-color, #222222);
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.25rem;
    color: var(--text-muted, #666666);
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  .close-btn:hover {
    background-color: rgba(0, 0, 0, 0.08);
    color: var(--text-color, #222222);
  }

  .modal-body {
    padding: 1.5rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .info-section {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .section-heading {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--accent-color, #4a6fa5);
  }

  .section-text, .section-subtext {
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.5;
  }

  .section-subtext {
    font-size: 0.88rem;
    opacity: 0.85;
    margin-top: 0.2rem;
  }

  .edition-list {
    margin: 0;
    padding-left: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    font-size: 0.93rem;
    line-height: 1.45;
  }

  a {
    color: var(--accent-color, #4a6fa5);
    text-decoration: underline;
    text-underline-offset: 2px;
  }

  a:hover {
    opacity: 0.85;
  }

  .license-link {
    font-weight: 600;
  }

  .modal-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border-color, #e0e0e0);
    display: flex;
    justify-content: flex-end;
    background-color: var(--secondary-bg, #f8f9fa);
  }

  .btn {
    padding: 0.5rem 1.25rem;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .secondary-btn {
    background-color: transparent;
    border: 1px solid var(--border-color, #cccccc);
    color: var(--text-color, #333333);
  }

  .secondary-btn:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
</style>
