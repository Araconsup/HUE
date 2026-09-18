/**
 * HUE Beauty Intelligence — Frontend Client Application
 * Handles PWA lifecycle, image uploads, AI analysis pipeline, product matching, and routines.
 */

(function () {
  'use strict';

  // --- State ---
  const state = {
    mode: 'face', // 'face', 'outfit', 'combined'
    faceFile: null,
    outfitFile: null,
    faceDataUri: null,
    outfitDataUri: null,
    analysisResult: null,
    currentRoutine: null,
    useMyProducts: false,
    activeTab: 'categories',
    bagCount: 0,
    bagProducts: []
  };

  // --- DOM Elements ---
  const el = {
    viewInput: document.getElementById('viewInput'),
    viewLoading: document.getElementById('viewLoading'),
    viewResults: document.getElementById('viewResults'),

    modePills: document.querySelectorAll('.mode-pill'),
    faceUploadCard: document.getElementById('faceUploadCard'),
    outfitUploadCard: document.getElementById('outfitUploadCard'),

    dropzoneFace: document.getElementById('dropzoneFace'),
    dropzoneOutfit: document.getElementById('dropzoneOutfit'),
    inputFace: document.getElementById('inputFace'),
    cameraFace: document.getElementById('cameraFace'),
    inputOutfit: document.getElementById('inputOutfit'),
    cameraOutfit: document.getElementById('cameraOutfit'),

    faceEmptyState: document.getElementById('faceEmptyState'),
    facePreviewState: document.getElementById('facePreviewState'),
    imgFacePreview: document.getElementById('imgFacePreview'),
    btnRemoveFace: document.getElementById('btnRemoveFace'),

    outfitEmptyState: document.getElementById('outfitEmptyState'),
    outfitPreviewState: document.getElementById('outfitPreviewState'),
    imgOutfitPreview: document.getElementById('imgOutfitPreview'),
    btnRemoveOutfit: document.getElementById('btnRemoveOutfit'),

    btnRunAnalysis: document.getElementById('btnRunAnalysis'),
    btnResetAnalysis: document.getElementById('btnResetAnalysis'),
    btnSaveCurrentLook: document.getElementById('btnSaveCurrentLook'),

    // Stages
    stageQuality: document.getElementById('stageQuality'),
    stageDetection: document.getElementById('stageDetection'),
    stageHarmony: document.getElementById('stageHarmony'),
    stageBuilding: document.getElementById('stageBuilding'),

    // Results
    resultsThumbnailsRow: document.getElementById('resultsThumbnailsRow'),
    resLookTitle: document.getElementById('resLookTitle'),
    resLookSummary: document.getElementById('resLookSummary'),
    resConfidence: document.getElementById('resConfidence'),
    toggleUseMyProducts: document.getElementById('toggleUseMyProducts'),

    btnToggleObservations: document.getElementById('btnToggleObservations'),
    obsDetailsBox: document.getElementById('obsDetailsBox'),
    obsGrid: document.getElementById('obsGrid'),

    resTabs: document.querySelectorAll('.res-tab'),
    tabCategories: document.getElementById('tabCategories'),
    tabRoutine: document.getElementById('tabRoutine'),
    categoriesGrid: document.getElementById('categoriesGrid'),
    routineStepsContainer: document.getElementById('routineStepsContainer'),

    // Drawers
    btnOpenBag: document.getElementById('btnOpenBag'),
    btnSavedLooks: document.getElementById('btnSavedLooks'),
    btnFindProducts: document.getElementById('btnFindProducts'),

    drawerSearch: document.getElementById('drawerSearch'),
    btnCloseSearch: document.getElementById('btnCloseSearch'),
    inputProductSearch: document.getElementById('inputProductSearch'),
    categoryFilterChips: document.getElementById('categoryFilterChips'),
    searchResultsList: document.getElementById('searchResultsList'),

    drawerBag: document.getElementById('drawerBag'),
    btnCloseBag: document.getElementById('btnCloseBag'),
    bagItemsList: document.getElementById('bagItemsList'),
    bagCounter: document.getElementById('bagCounter'),

    drawerSavedLooks: document.getElementById('drawerSavedLooks'),
    btnCloseSaved: document.getElementById('btnCloseSaved'),
    savedLooksList: document.getElementById('savedLooksList'),

    toast: document.getElementById('toastNotification'),
    toastMsg: document.getElementById('toastMessage')
  };

  // --- Initializer ---
  function init() {
    registerServiceWorker();
    setupModeSelector();
    setupUploadHandlers();
    setupResultsControls();
    setupDrawers();
    loadBagItems(false);
  }

  // --- Service Worker Registration ---
  function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(err => {
        console.warn('SW registration bypassed:', err);
      });
    }
  }

  // --- Mode Selector ---
  function setupModeSelector() {
    el.modePills.forEach(pill => {
      pill.addEventListener('click', () => {
        el.modePills.forEach(p => {
          p.classList.remove('active');
          p.setAttribute('aria-selected', 'false');
        });
        pill.classList.add('active');
        pill.setAttribute('aria-selected', 'true');

        state.mode = pill.dataset.mode;
        updateDropzoneVisibility();
        validateInputsReady();
      });
    });
  }

  function updateDropzoneVisibility() {
    if (state.mode === 'face') {
      el.faceUploadCard.classList.remove('hidden');
      el.outfitUploadCard.classList.add('hidden');
    } else if (state.mode === 'outfit') {
      el.faceUploadCard.classList.add('hidden');
      el.outfitUploadCard.classList.remove('hidden');
    } else if (state.mode === 'combined') {
      el.faceUploadCard.classList.remove('hidden');
      el.outfitUploadCard.classList.remove('hidden');
    }
  }

  // --- File Upload & Preview Handlers ---
  function setupUploadHandlers() {
    // Face Inputs
    el.inputFace.addEventListener('change', (e) => handleFileSelect(e.target.files[0], 'face'));
    el.cameraFace.addEventListener('change', (e) => handleFileSelect(e.target.files[0], 'face'));

    // Outfit Inputs
    el.inputOutfit.addEventListener('change', (e) => handleFileSelect(e.target.files[0], 'outfit'));
    el.cameraOutfit.addEventListener('change', (e) => handleFileSelect(e.target.files[0], 'outfit'));

    // Drag & drop for Face
    setupDragDrop(el.dropzoneFace, (file) => handleFileSelect(file, 'face'));
    // Drag & drop for Outfit
    setupDragDrop(el.dropzoneOutfit, (file) => handleFileSelect(file, 'outfit'));

    // Remove buttons
    el.btnRemoveFace.addEventListener('click', (e) => {
      e.stopPropagation();
      clearImage('face');
    });

    el.btnRemoveOutfit.addEventListener('click', (e) => {
      e.stopPropagation();
      clearImage('outfit');
    });

    // Run Analysis Button
    el.btnRunAnalysis.addEventListener('click', startAnalysisPipeline);
  }

  function setupDragDrop(zone, onFile) {
    ['dragenter', 'dragover'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
      });
    });

    zone.addEventListener('drop', (e) => {
      if (e.dataTransfer && e.dataTransfer.files.length) {
        onFile(e.dataTransfer.files[0]);
      }
    });
  }

  /**
   * Client-side downscaling & compression before sending to server.
   * Caps high-res camera captures (e.g. 12MP/48MP) to max 1536px, saving bandwidth & upload time.
   */
  function compressAndDownscaleImage(file, maxDimension = 1536, quality = 0.85) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      const reader = new FileReader();

      reader.onerror = reject;
      reader.onload = (e) => {
        img.onerror = reject;
        img.onload = () => {
          let { width, height } = img;
          if (width > maxDimension || height > maxDimension) {
            if (width > height) {
              height = Math.round((height * maxDimension) / width);
              width = maxDimension;
            } else {
              width = Math.round((width * maxDimension) / height);
              height = maxDimension;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          const dataUri = canvas.toDataURL('image/jpeg', quality);
          canvas.toBlob((blob) => {
            const cleanName = (file.name || 'photo').replace(/\.[^/.]+$/, "") + ".jpg";
            const optimizedFile = new File([blob], cleanName, {
              type: 'image/jpeg',
              lastModified: Date.now()
            });
            resolve({ file: optimizedFile, dataUri, width, height });
          }, 'image/jpeg', quality);
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  async function handleFileSelect(file, type) {
    if (!file || !file.type.startsWith('image/')) {
      showToast('Please select a valid image file');
      return;
    }

    try {
      const { file: optimizedFile, dataUri } = await compressAndDownscaleImage(file, 1536, 0.85);

      if (type === 'face') {
        state.faceFile = optimizedFile;
        state.faceDataUri = dataUri;
        el.imgFacePreview.src = dataUri;
        el.faceEmptyState.classList.add('hidden');
        el.facePreviewState.classList.remove('hidden');
      } else {
        state.outfitFile = optimizedFile;
        state.outfitDataUri = dataUri;
        el.imgOutfitPreview.src = dataUri;
        el.outfitEmptyState.classList.add('hidden');
        el.outfitPreviewState.classList.remove('hidden');
      }
      validateInputsReady();
    } catch (err) {
      console.error('Image compression error:', err);
      showToast('Failed to process image.');
    }
  }

  function clearImage(type) {
    if (type === 'face') {
      state.faceFile = null;
      state.faceDataUri = null;
      el.inputFace.value = '';
      el.cameraFace.value = '';
      el.imgFacePreview.src = '';
      el.facePreviewState.classList.add('hidden');
      el.faceEmptyState.classList.remove('hidden');
    } else {
      state.outfitFile = null;
      state.outfitDataUri = null;
      el.inputOutfit.value = '';
      el.cameraOutfit.value = '';
      el.imgOutfitPreview.src = '';
      el.outfitPreviewState.classList.add('hidden');
      el.outfitEmptyState.classList.remove('hidden');
    }
    validateInputsReady();
  }

  function validateInputsReady() {
    let ready = false;
    if (state.mode === 'face' && state.faceFile) {
      ready = true;
    } else if (state.mode === 'outfit' && state.outfitFile) {
      ready = true;
    } else if (state.mode === 'combined' && state.faceFile && state.outfitFile) {
      ready = true;
    }
    el.btnRunAnalysis.disabled = !ready;
  }

  // --- Multi-Stage Analysis Pipeline ---
  async function startAnalysisPipeline() {
    switchView('loading');
    resetStages();

    // Stage 1: Quality
    advanceStage(el.stageQuality, 'active');

    try {
      let endpoint = '/api/ai/analyze/face/';
      const formData = new FormData();

      if (state.mode === 'face') {
        endpoint = '/api/ai/analyze/face/';
        formData.append('face_image', state.faceFile);
      } else if (state.mode === 'outfit') {
        endpoint = '/api/ai/analyze/outfit/';
        formData.append('outfit_image', state.outfitFile);
      } else if (state.mode === 'combined') {
        endpoint = '/api/ai/analyze/combined/';
        formData.append('face_image', state.faceFile);
        formData.append('outfit_image', state.outfitFile);
      }

      // Simulate stage transitions gracefully
      setTimeout(() => {
        advanceStage(el.stageQuality, 'completed');
        advanceStage(el.stageDetection, 'active');
      }, 700);

      setTimeout(() => {
        advanceStage(el.stageDetection, 'completed');
        advanceStage(el.stageHarmony, 'active');
      }, 1400);

      setTimeout(() => {
        advanceStage(el.stageHarmony, 'completed');
        advanceStage(el.stageBuilding, 'active');
      }, 2100);

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
      });

      const json = await response.json();

      if (!response.ok || !json.success) {
        throw new Error(json.message || json.error || 'Analysis failed');
      }

      advanceStage(el.stageBuilding, 'completed');

      setTimeout(() => {
        state.analysisResult = json.data;
        state.currentRoutine = json.data.application_steps;
        renderResults(json.data);
        switchView('results');
      }, 600);

    } catch (err) {
      console.error(err);
      showToast(err.message || 'Could not analyze photo. Please try again with better lighting.');
      switchView('input');
    }
  }

  function resetStages() {
    [el.stageQuality, el.stageDetection, el.stageHarmony, el.stageBuilding].forEach(s => {
      s.className = 'stage-item pending';
      s.querySelector('.stage-icon').innerHTML = '<span class="stage-spinner"></span>';
    });
  }

  function advanceStage(stageEl, status) {
    if (status === 'active') {
      stageEl.className = 'stage-item active';
      stageEl.querySelector('.stage-icon').innerHTML = '<span class="stage-spinner"></span>';
    } else if (status === 'completed') {
      stageEl.className = 'stage-item completed';
      stageEl.querySelector('.stage-icon').innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>`;
    }
  }

  function switchView(viewName) {
    el.viewInput.classList.toggle('hidden', viewName !== 'input');
    el.viewLoading.classList.toggle('hidden', viewName !== 'loading');
    el.viewResults.classList.toggle('hidden', viewName !== 'results');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // --- Render Results ---
  function renderResults(data) {
    el.resLookTitle.textContent = data.look_name || 'Bespoke Beauty Look';
    el.resLookSummary.textContent = data.summary || 'Engineered visual harmony.';

    const confScore = Math.round((data.confidence?.overall || 0.92) * 100);
    el.resConfidence.textContent = `${confScore}% Visual Harmony Match`;

    // Render uploaded thumbnails in Visual Summary
    if (el.resultsThumbnailsRow) {
      el.resultsThumbnailsRow.innerHTML = '';
      if (state.faceDataUri && (state.mode === 'face' || state.mode === 'combined')) {
        const faceBox = document.createElement('div');
        faceBox.className = 'result-thumb-box';
        faceBox.innerHTML = `<img src="${state.faceDataUri}" alt="Face"><span class="result-thumb-tag">Face</span>`;
        el.resultsThumbnailsRow.appendChild(faceBox);
      }
      if (state.outfitDataUri && (state.mode === 'outfit' || state.mode === 'combined')) {
        const outfitBox = document.createElement('div');
        outfitBox.className = 'result-thumb-box';
        outfitBox.innerHTML = `<img src="${state.outfitDataUri}" alt="Outfit"><span class="result-thumb-tag">Outfit</span>`;
        el.resultsThumbnailsRow.appendChild(outfitBox);
      }
    }

    renderObservations(data);
    renderCategoryCards(data.recommendations || {});
    renderRoutineSteps(state.currentRoutine || []);
  }

  function renderObservations(data) {
    el.obsGrid.innerHTML = '';
    const face = data.face_analysis;
    const outfit = data.outfit_analysis;

    const tiles = [];

    if (face?.visible_undertone_indicators?.apparent_undertone) {
      tiles.push({
        title: 'Undertone Harmony',
        value: `${face.visible_undertone_indicators.apparent_undertone.toUpperCase()} balance`
      });
    }

    if (face?.face_shape_estimate?.shape) {
      tiles.push({
        title: 'Structure Focus',
        value: face.face_shape_estimate.shape
      });
    }

    if (outfit?.dominant_colors?.length) {
      const colors = outfit.dominant_colors.map(c => c.color_name).slice(0, 2).join(', ');
      tiles.push({
        title: 'Palette Relationship',
        value: colors
      });
    }

    if (outfit?.overall_aesthetic) {
      tiles.push({
        title: 'Styling Aesthetic',
        value: outfit.overall_aesthetic
      });
    }

    if (!tiles.length) {
      tiles.push(
        { title: 'Natural Dimension', value: 'High points softly enhanced' },
        { title: 'Finish Direction', value: 'Radiant skin-like velvet' }
      );
    }

    tiles.forEach(t => {
      const tile = document.createElement('div');
      tile.className = 'obs-item-tile';
      tile.innerHTML = `
        <div class="obs-item-title">${escapeHtml(t.title)}</div>
        <div class="obs-item-value">${escapeHtml(t.value)}</div>
      `;
      el.obsGrid.appendChild(tile);
    });
  }

  function renderCategoryCards(recommendations) {
    el.categoriesGrid.innerHTML = '';
    const categories = Object.keys(recommendations);

    categories.forEach(catKey => {
      const rec = recommendations[catKey];
      const color = rec.color || { color_name: 'Tone Balance', hex: '#C48D7F' };

      // Check if user owns a matching product in their bag
      const ownedMatch = state.bagProducts.find(p => {
        const pCat = p.category_slug ? p.category_slug.toLowerCase() : '';
        const k = catKey.toLowerCase();
        return pCat.includes(k) || k.includes(pCat) || (k === 'base' && pCat.includes('foundation'));
      });

      const card = document.createElement('div');
      card.className = 'category-card';
      card.innerHTML = `
        <div>
          <div class="cat-header">
            <span class="cat-title">${escapeHtml(catKey)}</span>
            <div class="cat-color-chip">
              <span class="color-swatch" style="background-color: ${color.hex}"></span>
              <span>${escapeHtml(color.color_name)}</span>
            </div>
          </div>
          <div class="cat-direction">${escapeHtml(rec.product_direction)}</div>
          <div class="cat-tags-row">
            ${rec.finish ? `<span class="tag-badge">${escapeHtml(rec.finish)}</span>` : ''}
            ${rec.intensity ? `<span class="tag-badge">${escapeHtml(rec.intensity)}</span>` : ''}
          </div>
          ${ownedMatch ? `<div class="cat-owned-badge">💄 In Your Bag: ${escapeHtml(ownedMatch.brand)} ${escapeHtml(ownedMatch.name)}</div>` : ''}
        </div>
        <div class="cat-guidance">${escapeHtml(rec.placement || rec.reasoning)}</div>
      `;
      el.categoriesGrid.appendChild(card);
    });
  }

  function renderRoutineSteps(steps) {
    el.routineStepsContainer.innerHTML = '';

    steps.forEach((step, idx) => {
      const colorHex = step.color?.hex || '#C48D7F';
      const colorName = step.color?.color_name || '';
      const owned = step.owned_product;

      const card = document.createElement('div');
      card.className = 'routine-step-card';
      card.innerHTML = `
        <div class="step-num-badge">0${step.step_number || idx + 1}</div>
        <div class="step-main-content">
          <div class="step-header-row">
            <span class="step-category-name">${escapeHtml(step.category)}</span>
            ${colorName ? `<span class="cat-color-chip"><span class="color-swatch" style="background-color: ${colorHex}"></span>${escapeHtml(colorName)}</span>` : ''}
          </div>
          <h4 class="step-title">${escapeHtml(step.title)}</h4>
          <p class="step-guidance">${escapeHtml(step.guidance)}</p>
          ${step.reasoning ? `<p class="step-reasoning">Stylist note: ${escapeHtml(step.reasoning)}</p>` : ''}

          ${owned ? `
            <div class="step-owned-product-banner">
              <div class="owned-prod-left">
                <span class="owned-prod-icon">💄</span>
                <div>
                  <div class="owned-prod-name">Your Bag: ${escapeHtml(owned.brand)} ${escapeHtml(owned.name)}</div>
                  <div class="owned-prod-shade">${owned.shade ? escapeHtml(owned.shade) : ''} — ${escapeHtml(owned.usage_guidance || 'Ideal match')}</div>
                </div>
              </div>
              <span class="match-score-badge">${Math.round(owned.compatibility_score * 100)}% Match</span>
            </div>
          ` : ''}
        </div>
      `;
      el.routineStepsContainer.appendChild(card);
    });
  }

  // --- Results Controls ---
  function setupResultsControls() {
    // Reset / Start over
    el.btnResetAnalysis.addEventListener('click', () => {
      switchView('input');
    });

    // Toggle Stylist Observations
    el.btnToggleObservations.addEventListener('click', () => {
      const isHidden = el.obsDetailsBox.classList.contains('hidden');
      el.obsDetailsBox.classList.toggle('hidden');
      el.btnToggleObservations.textContent = isHidden ? 'Collapse' : 'Details';
    });

    // Tab switching (Categories vs 10-Step Routine)
    el.resTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        el.resTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        const tabKey = tab.dataset.tab;
        el.tabCategories.classList.toggle('hidden', tabKey !== 'categories');
        el.tabRoutine.classList.toggle('hidden', tabKey !== 'routine');
      });
    });

    // "Use What I Own" Toggle
    el.toggleUseMyProducts.addEventListener('change', async (e) => {
      state.useMyProducts = e.target.checked;
      if (!state.analysisResult) return;

      showToast(state.useMyProducts ? "Matching routine to your Makeup Bag..." : "Switched to standard look routine.");

      try {
        const resp = await fetch('/api/looks/generate/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            use_my_products: state.useMyProducts,
            recommendations: state.analysisResult.recommendations,
            application_steps: state.analysisResult.application_steps
          })
        });
        const res = await resp.json();
        if (res.success && res.customized_routine) {
          state.currentRoutine = res.customized_routine;
          renderRoutineSteps(res.customized_routine);

          if (state.useMyProducts && res.owned_products_matched > 0) {
            showToast(`Matched ${res.owned_products_matched} products from your bag!`);
          }
        }
      } catch (err) {
        console.error(err);
      }
    });

    // Save Look
    el.btnSaveCurrentLook.addEventListener('click', async () => {
      if (!state.analysisResult) return;

      try {
        const resp = await fetch('/api/looks/save/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: state.analysisResult.look_name || 'My HUE Look',
            look_name: state.analysisResult.look_name,
            description: state.analysisResult.summary,
            mode: state.mode,
            routine_data: state.currentRoutine || state.analysisResult.application_steps,
            visual_summary: state.analysisResult.confidence || {}
          })
        });
        const res = await resp.json();
        if (res.success) {
          showToast(`Saved '${state.analysisResult.look_name}' to your looks!`);
        }
      } catch (err) {
        showToast('Could not save look.');
      }
    });
  }

  // --- Drawers (Search, Bag, Saved Looks) ---
  function setupDrawers() {
    // Search Drawer
    el.btnFindProducts.addEventListener('click', () => {
      openDrawer(el.drawerSearch);
      searchProducts('');
    });
    el.btnCloseSearch.addEventListener('click', () => closeDrawer(el.drawerSearch));

    // Live search input
    let searchDebounce;
    el.inputProductSearch.addEventListener('input', (e) => {
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => {
        const activeChip = el.categoryFilterChips.querySelector('.chip.active');
        const cat = activeChip ? activeChip.dataset.cat : '';
        searchProducts(e.target.value, cat);
      }, 250);
    });

    // Category chips in Search
    el.categoryFilterChips.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', () => {
        el.categoryFilterChips.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        searchProducts(el.inputProductSearch.value, chip.dataset.cat);
      });
    });

    // Makeup Bag Drawer
    el.btnOpenBag.addEventListener('click', () => {
      openDrawer(el.drawerBag);
      loadBagItems(true);
    });
    el.btnCloseBag.addEventListener('click', () => closeDrawer(el.drawerBag));

    // Saved Looks Drawer
    el.btnSavedLooks.addEventListener('click', () => {
      openDrawer(el.drawerSavedLooks);
      loadSavedLooks();
    });
    el.btnCloseSaved.addEventListener('click', () => closeDrawer(el.drawerSavedLooks));

    // Click outside to close
    [el.drawerSearch, el.drawerBag, el.drawerSavedLooks].forEach(drawer => {
      drawer.addEventListener('click', (e) => {
        if (e.target === drawer) closeDrawer(drawer);
      });
    });
  }

  function openDrawer(drawer) {
    drawer.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer(drawer) {
    drawer.classList.add('hidden');
    document.body.style.overflow = '';
  }

  // --- Product Catalog Search ---
  async function searchProducts(query, category = '') {
    try {
      const resp = await fetch('/api/products/search/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, category, limit: 30 })
      });
      const data = await resp.json();
      if (data.success) {
        renderSearchResults(data.products);
      }
    } catch (err) {
      console.error(err);
    }
  }

  function renderSearchResults(products) {
    el.searchResultsList.innerHTML = '';
    if (!products.length) {
      el.searchResultsList.innerHTML = '<p class="dropzone-hint" style="text-align:center; padding: 20px;">No matching cosmetic products found.</p>';
      return;
    }

    const hasActiveLook = !!state.analysisResult;

    products.forEach(p => {
      const item = document.createElement('div');
      item.className = 'product-item-card';

      const shadeOptions = (p.shades || []).map(s => `
        <option value="${s.id}">${escapeHtml(s.name)}</option>
      `).join('');

      item.innerHTML = `
        <img class="prod-thumb" src="${p.image_url || '/static/icons/icon-192.png'}" onerror="this.onerror=null;this.src='/static/icons/icon-192.png';" alt="${escapeHtml(p.name)}">
        <div class="prod-info">
          <div class="prod-brand">${escapeHtml(p.brand)}</div>
          <div class="prod-title">${escapeHtml(p.name)}</div>
          <div class="prod-meta">${escapeHtml(p.category)} · ${p.finish ? escapeHtml(p.finish) : ''} · ${p.price ? '$' + p.price : ''}</div>
          ${shadeOptions ? `<select class="prod-shades-select">${shadeOptions}</select>` : ''}
          <div class="prod-match-result hidden"></div>
        </div>
        <div class="prod-card-actions">
          ${hasActiveLook ? `<button class="btn-check-match" data-prod-id="${p.id}">Match</button>` : ''}
          <button class="btn-add-bag" data-prod-id="${p.id}">+ Bag</button>
        </div>
      `;

      const addBtn = item.querySelector('.btn-add-bag');
      const matchBtn = item.querySelector('.btn-check-match');
      const shadeSelect = item.querySelector('.prod-shades-select');

      addBtn.addEventListener('click', () => {
        const shadeId = shadeSelect ? shadeSelect.value : null;
        addToMakeupBag(p.id, shadeId, p.name);
      });

      if (matchBtn) {
        matchBtn.addEventListener('click', async () => {
          const shadeId = shadeSelect ? shadeSelect.value : null;
          matchBtn.disabled = true;
          matchBtn.textContent = '...';
          const matchBox = item.querySelector('.prod-match-result');
          try {
            const catKey = (p.category_slug || p.category || 'Base').toLowerCase();
            const recDetails = state.analysisResult?.recommendations?.[catKey] || {};
            const resp = await fetch('/api/products/match/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                product_id: p.id,
                shade_id: shadeId,
                category: p.category,
                recommendation: recDetails
              })
            });
            const mData = await resp.json();
            if (mData.success && mData.match) {
              const comp = mData.match.compatibility;
              matchBox.className = 'prod-match-result';
              matchBox.innerHTML = `
                <div class="match-score-pill"><span>${Math.round(comp.score * 100)}% Match</span> — ${escapeHtml(comp.role)}</div>
                <div class="match-reason-text">${escapeHtml(comp.reason)}</div>
                <div class="match-usage-text">${escapeHtml(comp.usage)}</div>
              `;
            }
          } catch (err) {
            console.error(err);
          } finally {
            matchBtn.disabled = false;
            matchBtn.textContent = 'Match';
          }
        });
      }

      el.searchResultsList.appendChild(item);
    });
  }

  // --- Makeup Bag API ---
  async function addToMakeupBag(productId, shadeId, productName) {
    try {
      const resp = await fetch('/api/user/products/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, shade_id: shadeId })
      });
      const data = await resp.json();
      if (data.success) {
        showToast(`Added ${productName} to My Makeup Bag!`);
        loadBagItems(false);
      }
    } catch (err) {
      showToast('Could not add to bag.');
    }
  }

  async function loadBagItems(renderList = false) {
    try {
      const resp = await fetch('/api/user/products/');
      const data = await resp.json();
      if (data.success) {
        state.bagCount = data.count;
        state.bagProducts = data.products || [];
        el.bagCounter.textContent = data.count;

        if (renderList) {
          renderBagItems(data.products);
        }
        if (state.analysisResult && state.analysisResult.recommendations) {
          renderCategoryCards(state.analysisResult.recommendations);
        }
      }
    } catch (err) {
      console.error(err);
    }
  }

  function renderBagItems(items) {
    el.bagItemsList.innerHTML = '';
    if (!items.length) {
      el.bagItemsList.innerHTML = '<p class="dropzone-hint" style="text-align:center; padding: 30px;">Your makeup bag is currently empty. Use the search to add products you own!</p>';
      return;
    }

    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'bag-card';
      card.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
          <span class="color-swatch" style="background-color: ${item.shade_hex}"></span>
          <div>
            <div class="prod-brand">${escapeHtml(item.brand)}</div>
            <div class="prod-title">${escapeHtml(item.name)}</div>
            <div class="prod-meta">${item.shade ? escapeHtml(item.shade) : ''} · ${escapeHtml(item.category)}</div>
          </div>
        </div>
        <button class="btn-remove-item" data-id="${item.id}" title="Remove">✕</button>
      `;

      card.querySelector('.btn-remove-item').addEventListener('click', async () => {
        await removeBagItem(item.id);
      });

      el.bagItemsList.appendChild(card);
    });
  }

  async function removeBagItem(id) {
    try {
      const resp = await fetch(`/api/user/products/${id}/`, { method: 'DELETE' });
      const data = await resp.json();
      if (data.success) {
        showToast('Removed from bag.');
        loadBagItems(true);
      }
    } catch (err) {
      showToast('Could not remove item.');
    }
  }

  // --- Saved Looks ---
  async function loadSavedLooks() {
    try {
      const resp = await fetch('/api/looks/saved/');
      const data = await resp.json();
      if (data.success) {
        renderSavedLooks(data.looks);
      }
    } catch (err) {
      console.error(err);
    }
  }

  function renderSavedLooks(looks) {
    el.savedLooksList.innerHTML = '';
    if (!looks.length) {
      el.savedLooksList.innerHTML = '<p class="dropzone-hint" style="text-align:center; padding: 30px;">No saved looks yet. Complete an analysis and tap "Save Look"!</p>';
      return;
    }

    looks.forEach(look => {
      const item = document.createElement('div');
      item.className = 'product-item-card';
      item.innerHTML = `
        <div style="flex: 1;">
          <div class="prod-brand">${escapeHtml(look.created_at)} · ${escapeHtml(look.mode.toUpperCase())}</div>
          <div class="prod-title">${escapeHtml(look.title)}</div>
          <div class="prod-meta">${escapeHtml(look.look_name)} (${look.routine_steps_count} steps)</div>
        </div>
      `;
      el.savedLooksList.appendChild(item);
    });
  }

  // --- Helpers ---
  function showToast(msg) {
    el.toastMsg.textContent = msg;
    el.toast.classList.remove('hidden');
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => {
      el.toast.classList.add('hidden');
    }, 3200);
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // Start app
  document.addEventListener('DOMContentLoaded', init);
})();
