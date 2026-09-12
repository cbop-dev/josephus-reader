<script lang="ts">
  import { showPdfModal, currentWork, currentBook } from '$lib/stores/readerStore';
  import { jsPDF } from 'jspdf';
  import html2canvas from 'html2canvas';

  let { manifest = [], currentBookData = null } = $props<{ manifest?: any[]; currentBookData?: any }>();

  let pageSize = $state<'a4' | 'letter' | 'a5' | 'b5' | '6x9'>('a4');
  let printLayout = $state<'facing' | 'twocol'>('facing');
  let activeSectionIdx = $state(0);
  let isGenerating = $state(false);

  let sections = $derived(currentBookData?.sections || []);
  let activeWorkMeta = $derived(manifest.find(w => w.id === $currentWork) || { title: 'Josephus' });
  let currentSection = $derived(sections[activeSectionIdx] || sections[0] || { niese: '1', grc: '', eng: '' });

  function closeModal() {
    $showPdfModal = false;
  }

  async function downloadPDF() {
    isGenerating = true;

    try {
      // Ensure web fonts (Gentium Book Plus, etc.) are 100% loaded before canvas capture
      if (typeof document !== 'undefined' && document.fonts) {
        await document.fonts.ready;
      }

      const formatMap: Record<string, [number, number]> = {
        a4: [210, 297],
        letter: [215.9, 279.4],
        a5: [148, 210],
        b5: [176, 250],
        '6x9': [152.4, 228.6]
      };

      const [width, height] = formatMap[pageSize] || [210, 297];

      const workTitle = activeWorkMeta.title || 'Josephus';
      const secLabel = currentSection.niese || '1';

      if (printLayout === 'facing') {
        // FACING PAGES: Capture Left (Greek) and Right (English) pages separately
        const leftPageEl = document.getElementById('render-page-left');
        const rightPageEl = document.getElementById('render-page-right');

        if (!leftPageEl || !rightPageEl) throw new Error('Render elements missing');

        // Render Left Page (Greek) to Canvas
        const canvasLeft = await html2canvas(leftPageEl, {
          scale: 2.5,
          useCORS: true,
          backgroundColor: '#ffffff'
        });

        // Render Right Page (English) to Canvas
        const canvasRight = await html2canvas(rightPageEl, {
          scale: 2.5,
          useCORS: true,
          backgroundColor: '#ffffff'
        });

        const doc = new jsPDF({
          orientation: 'portrait',
          unit: 'mm',
          format: [width, height]
        });

        // Add Left Page Image
        const imgLeftData = canvasLeft.toDataURL('image/jpeg', 0.95);
        doc.addImage(imgLeftData, 'JPEG', 0, 0, width, height);

        // Add Right Page Image
        doc.addPage([width, height], 'portrait');
        const imgRightData = canvasRight.toDataURL('image/jpeg', 0.95);
        doc.addImage(imgRightData, 'JPEG', 0, 0, width, height);

        const safeWork = workTitle.replace(/[^\w]/g, '_');
        const safeSec = secLabel.replace(/[^\w]/g, '_');
        doc.save(`Josephus_${safeWork}_Sec_${safeSec}_Facing.pdf`);

      } else {
        // 2-COLUMN PARALLEL: Capture Single 2-Column Page
        const twocolEl = document.getElementById('render-page-twocol');
        if (!twocolEl) throw new Error('Render element missing');

        const canvasTwocol = await html2canvas(twocolEl, {
          scale: 2.5,
          useCORS: true,
          backgroundColor: '#ffffff'
        });

        const doc = new jsPDF({
          orientation: 'portrait',
          unit: 'mm',
          format: [width, height]
        });

        const imgData = canvasTwocol.toDataURL('image/jpeg', 0.95);
        doc.addImage(imgData, 'JPEG', 0, 0, width, height);

        const safeWork = workTitle.replace(/[^\w]/g, '_');
        const safeSec = secLabel.replace(/[^\w]/g, '_');
        doc.save(`Josephus_${safeWork}_Sec_${safeSec}_TwoColumn.pdf`);
      }

      $showPdfModal = false;
    } catch (err) {
      console.error('Error generating PDF:', err);
    } finally {
      isGenerating = false;
    }
  }
</script>

<!-- Screen Modal UI -->
{#if $showPdfModal}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="modal-backdrop" onclick={closeModal}>
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <div class="header-title">
          <h2>Direct PDF Document Exporter</h2>
          <span class="sub-label">High-Resolution Polytonic Greek & English PDF</span>
        </div>
        <button class="close-btn" onclick={closeModal}>✕</button>
      </div>

      <div class="modal-body">
        <!-- Target Section Info Badge -->
        <div class="section-target-box">
          <span class="target-label">Export Target:</span>
          <span class="target-badge">Section § {currentSection.niese}</span>
        </div>

        <!-- Layout Option Selector -->
        <div class="form-group">
          <label for="print-layout">Select PDF Document Layout:</label>
          <select id="print-layout" bind:value={printLayout} class="form-select">
            <option value="facing">Facing Pages (Page 1: Greek, Page 2: English)</option>
            <option value="twocol">2-Column Parallel (Greek & English on same page)</option>
          </select>
        </div>

        <!-- Page Format Selector -->
        <div class="form-group">
          <label for="page-size">Select Target Page Size:</label>
          <select id="page-size" bind:value={pageSize} class="form-select">
            <option value="a4">A4 (210 x 297 mm) - Standard</option>
            <option value="letter">US Letter (8.5 x 11 in) - North American Standard</option>
            <option value="a5">A5 (148 x 210 mm) - Compact Handbook</option>
            <option value="b5">B5 (176 x 250 mm) - Academic Monograph</option>
            <option value="6x9">6 x 9 in (152 x 229 mm) - Trade Paperback</option>
          </select>
        </div>

        <!-- Visual Layout Diagram -->
        <div class="facing-diagram">
          {#if printLayout === 'facing'}
            <div class="page-preview left-page">
              <div class="page-header">GREEK (PAGE 1)</div>
              <div class="page-content-preview">
                <span class="preview-sec-badge">§ {currentSection.niese}</span>
                <p class="preview-grc">{currentSection.grc?.slice(0, 90) || ''}...</p>
              </div>
              <div class="page-num">Left Page</div>
            </div>

            <div class="page-preview right-page">
              <div class="page-header">ENGLISH (PAGE 2)</div>
              <div class="page-content-preview">
                <span class="preview-sec-badge">§ {currentSection.niese}</span>
                <p class="preview-eng">{currentSection.eng?.slice(0, 90) || ''}...</p>
              </div>
              <div class="page-num">Right Page</div>
            </div>
          {:else}
            <div class="page-preview single-page-preview">
              <div class="page-header">2-COLUMN PARALLEL (PAGE 1)</div>
              <div class="page-twocol-preview">
                <div class="preview-col">
                  <span class="preview-sec-badge">GRK § {currentSection.niese}</span>
                  <p class="preview-grc">{currentSection.grc?.slice(0, 70) || ''}...</p>
                </div>
                <div class="preview-col">
                  <span class="preview-sec-badge">ENG § {currentSection.niese}</span>
                  <p class="preview-eng">{currentSection.eng?.slice(0, 70) || ''}...</p>
                </div>
              </div>
              <div class="page-num">Same Page</div>
            </div>
          {/if}
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn secondary-btn" onclick={closeModal}>Cancel</button>
        <button class="btn primary-btn" onclick={downloadPDF} disabled={isGenerating}>
          {#if isGenerating}
            <span class="btn-spinner"></span>
            <span>Generating High-Res PDF...</span>
          {:else}
            <span>📥 Download PDF File (.pdf)</span>
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- OFF-SCREEN RENDERING CONTAINER FOR POLYTONIC GREEK PDF GENERATION -->
<div class="pdf-render-offscreen">
  <!-- Facing Page 1: Left (Greek) -->
  <div id="render-page-left" class="pdf-render-page">
    <div class="pdf-render-header">
      <span>FLAVIUS JOSEPHUS</span>
      <span>{activeWorkMeta.title.toUpperCase()}</span>
    </div>
    <div class="pdf-render-body">
      <h3 class="pdf-sec-heading">§ {currentSection.niese}</h3>
      <p class="pdf-greek-text">{currentSection.grc.replace(/\[\d+\]/g, '')}</p>
    </div>
    <div class="pdf-render-footer">
      <span>Page 2 (Greek Facing Page)</span>
    </div>
  </div>

  <!-- Facing Page 2: Right (English) -->
  <div id="render-page-right" class="pdf-render-page">
    <div class="pdf-render-header">
      <span>{activeWorkMeta.title.toUpperCase()}</span>
      <span>{currentBookData?.title?.toUpperCase() || ''}</span>
    </div>
    <div class="pdf-render-body">
      <h3 class="pdf-sec-heading">§ {currentSection.niese}</h3>
      <p class="pdf-english-text">{currentSection.eng}</p>
    </div>
    <div class="pdf-render-footer">
      <span>Page 3 (English Facing Page)</span>
    </div>
  </div>

  <!-- 2-Column Single Page -->
  <div id="render-page-twocol" class="pdf-render-page">
    <div class="pdf-render-header">
      <span>FLAVIUS JOSEPHUS</span>
      <span>{activeWorkMeta.title.toUpperCase()} — {currentBookData?.title?.toUpperCase() || ''}</span>
    </div>
    <div class="pdf-render-body">
      <h3 class="pdf-sec-heading">§ {currentSection.niese}</h3>
      <div class="pdf-twocol-grid">
        <div class="pdf-col">
          <h4 class="pdf-col-title">GREEK TEXT</h4>
          <p class="pdf-greek-text">{currentSection.grc.replace(/\[\d+\]/g, '')}</p>
        </div>
        <div class="pdf-col">
          <h4 class="pdf-col-title">ENGLISH TRANSLATION</h4>
          <p class="pdf-english-text">{currentSection.eng}</p>
        </div>
      </div>
    </div>
    <div class="pdf-render-footer">
      <span>Page 1 (2-Column Parallel Layout)</span>
    </div>
  </div>
</div>

<style>
  /* Screen UI Styles */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(2px);
    z-index: 200;
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
    max-width: 580px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
    background-color: var(--bg-secondary);
  }

  .header-title h2 {
    font-family: var(--font-sans);
    font-size: 1.15rem;
    font-weight: 700;
  }

  .sub-label {
    font-size: 0.8rem;
    color: var(--text-muted);
  }

  .close-btn {
    font-size: 1.25rem;
    color: var(--text-muted);
  }

  .modal-body {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .section-target-box {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    padding: 0.75rem 1rem;
    border-radius: 8px;
  }

  .target-label {
    font-family: var(--font-sans);
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .target-badge {
    font-family: var(--font-sans);
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--accent-color);
    background-color: var(--accent-light);
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  label {
    font-family: var(--font-sans);
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .form-select {
    padding: 0.5rem;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: 0.9rem;
  }

  .facing-diagram {
    display: flex;
    gap: 0.75rem;
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    justify-content: center;
  }

  .page-preview {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #ccc;
    border-radius: 4px;
    width: 210px;
    height: 170px;
    padding: 0.65rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  }

  .single-page-preview {
    width: 320px;
  }

  .page-header {
    font-size: 0.65rem;
    font-weight: 700;
    text-align: center;
    color: #666;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.2rem;
  }

  .page-content-preview {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .page-twocol-preview {
    display: flex;
    gap: 0.5rem;
  }

  .preview-col {
    flex: 1;
  }

  .preview-sec-badge {
    font-size: 0.6rem;
    font-weight: 700;
    color: #8C3A2B;
  }

  .preview-grc {
    font-family: var(--font-greek);
    font-size: 0.62rem;
    line-height: 1.2;

  }

  .preview-eng {
    font-family: var(--font-english);
    font-size: 0.62rem;
    line-height: 1.2;

  }

  .page-num {
    font-size: 0.65rem;
    text-align: center;
    color: #999;
  }

  .modal-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
  }

  .primary-btn {
    background-color: var(--accent-color);
    color: #ffffff;
    padding: 0.5rem 1.25rem;
    border-radius: 6px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
  }

  .secondary-btn {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 0.5rem 1rem;
    border-radius: 6px;
  }

  .btn-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255, 255, 255, 0.4);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* OFF-SCREEN HIGH-RES RENDER STYLES FOR GREEK & ENGLISH PDF */
  .pdf-render-offscreen {
    position: absolute;
    left: -9999px;
    top: -9999px;
    width: 800px;
  }

  .pdf-render-page {
    width: 794px;
    height: 1123px;
    background-color: #ffffff;
    color: #111111;
    padding: 48px 56px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    font-family: var(--font-english);
  }

  .pdf-render-header {
    display: flex;
    justify-content: space-between;
    font-family: var(--font-sans);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #555555;
    border-bottom: 1.5px solid #dddddd;
    padding-bottom: 8px;
  }

  .pdf-render-body {
    flex: 1;
    padding-top: 24px;
  }

  .pdf-sec-heading {
    font-family: var(--font-sans);
    font-size: 14px;
    font-weight: 700;
    color: #8C3A2B;
    margin-bottom: 16px;
  }

  .pdf-greek-text {
    font-family: var(--font-greek);
    font-size: 18px;
    line-height: 1.8;
    text-align: justify;
    color: #111111;
  }

  .pdf-english-text {
    font-family: var(--font-english);
    font-size: 15px;
    line-height: 1.7;
    text-align: justify;
    color: #222222;
  }

  .pdf-twocol-grid {
    display: flex;
    gap: 32px;
  }

  .pdf-col {
    flex: 1;
  }

  .pdf-col-title {
    font-family: var(--font-sans);
    font-size: 11px;
    font-weight: 700;
    color: #666666;
    border-bottom: 1px solid #eeeeee;
    padding-bottom: 4px;
    margin-bottom: 12px;
  }

  .pdf-render-footer {
    font-family: var(--font-sans);
    font-size: 11px;
    color: #888888;
    text-align: center;
    border-top: 1px solid #eeeeee;
    padding-top: 8px;
  }
</style>
