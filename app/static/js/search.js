// === Scan Overlay Animation ===
const SCAN_STATUS_TEXTS = [
    "Plattformen werden geprüft...",
    "Username wird normalisiert...",
    "Varianten werden erzeugt...",
    "Öffentliche Quellen werden geprüft...",
    "Ergebnisse werden bewertet...",
    "Scoring wird berechnet..."
];
const SCAN_STATUS_TEXTS_DEEP = [
    // === Scan Overlay Animation (Feinschliff) ===
    const SCAN_STATUS_TEXTS = [
        "Query wird vorbereitet...",
        "Eingaben werden normalisiert...",
        "Plattformen werden geprüft...",
        "Signale werden zusammengeführt...",
        "Ergebnisse werden bewertet..."
    ];
    const SCAN_STATUS_TEXTS_DEEP = [
        "DeepSearch aktiv...",
        "Erweiterte Analyse läuft..."
    ];

    function showScanOverlay(platforms, deepSearch) {
        const overlay = document.getElementById('scan-overlay');
        const statusText = document.getElementById('scan-status-text');
        const platformList = document.getElementById('scan-platform-list');
        const progressInner = document.getElementById('scan-progress-inner');
        const deepBadge = document.getElementById('scan-deep-badge');
        const cancelBtn = document.getElementById('scan-cancel-btn');
        if (!overlay || !statusText || !platformList || !progressInner) return;
        overlay.style.display = '';
        overlay.classList.remove('hide', 'error');
        // Reset
        platformList.innerHTML = '';
        progressInner.style.width = '0%';
        statusText.textContent = '';
        if (deepBadge) deepBadge.style.display = deepSearch ? '' : 'none';
        if (cancelBtn) cancelBtn.style.display = 'none'; // vorbereitet

        // prefers-reduced-motion
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Plattformen rendern
        let platformStates = platforms.map(() => 'waiting'); // waiting, scanning, done, error, skipped
        function renderPlatforms(activeIdx = -1, doneIdxs = [], failIdxs = [], skipIdxs = []) {
            platformList.innerHTML = '';
            platforms.forEach((name, i) => {
                const chip = document.createElement('div');
                chip.className = 'scan-platform-chip';
                if (doneIdxs.includes(i) || platformStates[i] === 'done') chip.classList.add('done');
                else if (failIdxs.includes(i) || platformStates[i] === 'error') chip.classList.add('fail');
                else if (skipIdxs.includes(i) || platformStates[i] === 'skipped') chip.classList.add('skip');
                else if (i === activeIdx || platformStates[i] === 'scanning') chip.classList.add('active');
                const dot = document.createElement('span');
                dot.className = 'scan-platform-dot';
                chip.appendChild(dot);
                chip.appendChild(document.createTextNode(name));
                platformList.appendChild(chip);
            });
        }

        // Status-Text-Rotation
        let statusIdx = 0;
        let statusTimer = null;
        let statusTexts = [...SCAN_STATUS_TEXTS];
        if (deepSearch) statusTexts = SCAN_STATUS_TEXTS_DEEP.concat(statusTexts);
        function rotateStatus() {
            statusText.textContent = statusTexts[statusIdx % statusTexts.length];
            statusIdx++;
            statusTimer = setTimeout(rotateStatus, reducedMotion ? 2600 : 1400);
        }
        rotateStatus();

        // Plattformen nacheinander animieren
        let idx = 0;
        let doneIdxs = [];
        let failIdxs = [];
        let skipIdxs = [];
        let stepTimer = null;
        function step() {
            if (idx > 0) doneIdxs.push(idx - 1);
            renderPlatforms(idx, doneIdxs, failIdxs, skipIdxs);
            progressInner.style.width = ((idx) / platforms.length * 100) + '%';
            if (idx < platforms.length && !reducedMotion) {
                stepTimer = setTimeout(step, 600);
                idx++;
            } else if (idx < platforms.length && reducedMotion) {
                stepTimer = setTimeout(step, 1200);
                idx++;
            }
        }
        if (!reducedMotion) step();
        else renderPlatforms();

        // Mindest-Sichtbarkeitsdauer
        const minVisible = 800;
        const startTime = Date.now();
        let hideRequested = false;
        let hideTimeout = null;
        let errorTimeout = null;

        // Fehlerstatus
        function showError(msg) {
            overlay.classList.add('error');
            statusText.textContent = msg || 'Suche fehlgeschlagen';
            if (deepBadge) deepBadge.style.display = 'none';
            clearTimeout(statusTimer);
            clearTimeout(stepTimer);
            // Plattformen auf error
            platformStates = platformStates.map(() => 'error');
            renderPlatforms();
            // Nach 1.2s ausblenden
            errorTimeout = setTimeout(() => {
                hideScanOverlay(true);
            }, 1200);
        }

        // Hide-Funktion
        function hideScanOverlay(force) {
            if (hideRequested) return;
            hideRequested = true;
            clearTimeout(statusTimer);
            clearTimeout(stepTimer);
            clearTimeout(errorTimeout);
            const elapsed = Date.now() - startTime;
            const doHide = () => {
                overlay.classList.add('hide');
                setTimeout(() => { overlay.style.display = 'none'; }, 400);
            };
            if (force || elapsed >= minVisible) {
                doHide();
            } else {
                hideTimeout = setTimeout(doHide, minVisible - elapsed);
            }
        }

        // Für späteren Cancel-Button vorbereitet
        if (cancelBtn) {
            cancelBtn.onclick = () => {
                // Noch nicht implementiert
            };
        }

        // Rückgabe: Funktionen
        return {
            hide: hideScanOverlay,
            error: showError
        };
    }
function getSelectedCategories() {
    try {
        const raw = localStorage.getItem("shadowseek_categories");
        if (!raw) return [];
        return JSON.parse(raw);
    } catch {
        return [];
    }
}
function setSelectedCategories(arr) {
    localStorage.setItem("shadowseek_categories", JSON.stringify(arr));
}
function clearSelectedCategories() {
    localStorage.removeItem("shadowseek_categories");
}

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('search-form');
    const resetBtn = document.getElementById('reset-btn');
    const catBar = document.getElementById('category-bar-search');
    const fields = [
        'query', 'real_name', 'clan_name', 'age', 'postal_code'
    ];
    const platformCheckboxes = () => Array.from(document.querySelectorAll('input[name="platforms"]'));
    const deepSearch = document.querySelector('input[name="deep_search"]');
    const storageKey = 'shadowseek_search_inputs';

    // Kategorien aus URL übernehmen
    function getCategoriesFromURL() {
        const params = new URLSearchParams(window.location.search);
        const cats = params.get('categories');
        if (!cats) return [];
        return cats.split(',').map(s => s.trim()).filter(Boolean);
    }

    // Render Kategorie-Chips
    let selected = getSelectedCategories();
    const urlCats = getCategoriesFromURL();
    if (urlCats.length > 0) {
        selected = urlCats;
        setSelectedCategories(selected);
    }
    if (catBar) {
        catBar.innerHTML = "";
        CATEGORIES.forEach(cat => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "category-chip-search" + (selected.includes(cat.value) ? " active" : "");
            btn.textContent = cat.label;
            btn.onclick = () => {
                if (selected.includes(cat.value)) {
                    selected = selected.filter(v => v !== cat.value);
                } else {
                    selected.push(cat.value);
                }
                setSelectedCategories(selected);
                renderChips();
            };
            catBar.appendChild(btn);
        });
    }
    function renderChips() {
        Array.from(catBar.children).forEach((btn, i) => {
            const val = CATEGORIES[i].value;
            btn.classList.toggle("active", selected.includes(val));
        });
    }
    renderChips();

    // Restore
    function restoreInputs() {
        const data = JSON.parse(localStorage.getItem(storageKey) || '{}');
        fields.forEach(f => {
            if (data[f] !== undefined && form.elements[f]) {
                form.elements[f].value = data[f];
            }
        });
        if (Array.isArray(data.platforms)) {
            platformCheckboxes().forEach(cb => {
                cb.checked = data.platforms.includes(cb.value);
            });
        }
        if (typeof data.deep_search === 'boolean') {
            deepSearch.checked = data.deep_search;
        }
    }

    // Save
    function saveInputs() {
        const data = {};
        fields.forEach(f => {
            data[f] = form.elements[f]?.value || '';
        });
        data.platforms = platformCheckboxes().filter(cb => cb.checked).map(cb => cb.value);
        data.deep_search = deepSearch.checked;
        localStorage.setItem(storageKey, JSON.stringify(data));
    }

    // Clear
    function clearInputs() {
        localStorage.removeItem(storageKey);
        fields.forEach(f => {
            if (form.elements[f]) form.elements[f].value = '';
        });
        platformCheckboxes().forEach(cb => { cb.checked = true; });
        deepSearch.checked = false;
    }

    // Save on change
    form.addEventListener('input', function (e) {
        if (e.target.name !== 'image') saveInputs();
    });
    form.addEventListener('change', function (e) {
        if (e.target.name !== 'image') saveInputs();
    });

    // Restore on load
    restoreInputs();

    // === Scan Overlay Integration (robust) ===
    let scanOverlayCtrl = null;
    form.addEventListener('submit', function (e) {
        // Plattformen auslesen
        const platformEls = platformCheckboxes();
        const platforms = platformEls.filter(cb => cb.checked).map(cb => cb.parentElement?.innerText.trim() || cb.value);
        const deepSearchActive = deepSearch && deepSearch.checked;
        scanOverlayCtrl = showScanOverlay(platforms, deepSearchActive);
        // Nach 14s Timeout (Fallback)
        setTimeout(() => { if (scanOverlayCtrl) scanOverlayCtrl.error('Zeitüberschreitung – keine Antwort'); }, 14000);
    });

    // Reset-Button
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            clearInputs();
            clearSelectedCategories();
            selected = [];
            renderChips();
            // Query-Parameter bereinigen
            const url = new URL(window.location.href);
            url.searchParams.delete('categories');
            window.history.replaceState({}, '', url.pathname + url.search);
            // Overlay ausblenden
            const overlay = document.getElementById('scan-overlay');
            if (overlay) { overlay.classList.add('hide'); setTimeout(() => { overlay.style.display = 'none'; }, 400); }
        });
    }

    // Ergebnisse/Fehler: Overlay ausblenden
    function hideScanOverlayIfVisible() {
        if (scanOverlayCtrl) { scanOverlayCtrl.hide(); scanOverlayCtrl = null; }
    }
    function showScanOverlayError(msg) {
        if (scanOverlayCtrl) { scanOverlayCtrl.error(msg); scanOverlayCtrl = null; }
    }
    // MutationObserver auf Ergebnisse
    const resultsCard = document.querySelector('.recon-card--results');
    if (resultsCard) {
        const observer = new MutationObserver(() => {
            hideScanOverlayIfVisible();
        });
        observer.observe(resultsCard, { childList: true, subtree: true });
    }
    // Fehlerfall: globales Error-Event
    window.addEventListener('error', () => showScanOverlayError('Suche fehlgeschlagen'));
    window.addEventListener('unhandledrejection', () => showScanOverlayError('Suche fehlgeschlagen'));
});
