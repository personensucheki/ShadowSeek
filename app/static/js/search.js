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

// --- Modifier/Modus-Logik ---
const MODIFIERS = [
    { label: "Öffentliche Quellen", value: "public_sources" },
    { label: "Geschützte Suche", value: "secure_mode" },
    { label: "KI-gestützte Bewertung", value: "ai_rerank" },
    { label: "DeepSearch bereit", value: "deepsearch" },
    { label: "Präzise Treffer", value: "precision_mode" },
];
function getSelectedModifiers() {
    try {
        const raw = localStorage.getItem("shadowseek_modifiers");
        if (!raw) return [];
        return JSON.parse(raw);
    } catch {
        return [];
    }
}
function setSelectedModifiers(arr) {
    localStorage.setItem("shadowseek_modifiers", JSON.stringify(arr));
}

document.addEventListener('DOMContentLoaded', function () {
        // === Ergebnis-Tabs: Filter-Logik ===
        const tabs = document.querySelectorAll('.tab-btn');
        const resultsList = document.getElementById('results-list');
        let allResults = [];
        // Ergebnisse initial aus DOM extrahieren (vereinfachte Demo, Backend sollte nach Kategorien liefern)
        if (resultsList) {
            allResults = Array.from(resultsList.children).filter(el => el.classList.contains('result-card'));
        }
        // Mapping: Kategorie → Plattform-Slug oder Typ
        const TAB_CATEGORIES = {
            social: ['instagram','tiktok','x','twitter','facebook','linkedin','snapchat','clapper'],
            dating: ['lovoo','badoo','knuddels'],
            adult: ['stripchat','onlyfans','dirtyhobby'],
            porn: ['xhamster','pornhub','xnxx'],
            web: ['web','website','domain'],
            forum: ['forum','board','reddit'],
            image: ['image','imgur','flickr','pic','photo'],
            video: ['youtube','twitch','video','vimeo'],
            news: ['news','zeitung','magazine'],
            community: ['community','discord','telegram'],
        };
        function getResultCategory(resultEl) {
            // Versucht, die Kategorie aus dem Plattformnamen zu bestimmen
            const platform = resultEl.querySelector('.result-platform')?.textContent?.toLowerCase() || '';
            for (const [tab, keys] of Object.entries(TAB_CATEGORIES)) {
                if (keys.some(k => platform.includes(k))) return tab;
            }
            return 'social'; // fallback
        }
        function filterResults(tab) {
            let found = 0;
            allResults.forEach(el => {
                const cat = getResultCategory(el);
                if (cat === tab) {
                    el.style.display = '';
                    found++;
                } else {
                    el.style.display = 'none';
                }
            });
            // Leere-Zustände
            const empty = resultsList.querySelector('.empty-state');
            if (empty) empty.style.display = found === 0 ? '' : 'none';
        }
        function setActiveTab(tab) {
            tabs.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tab));
        }
        tabs.forEach(btn => {
            btn.addEventListener('click', function() {
                setActiveTab(btn.dataset.tab);
                filterResults(btn.dataset.tab);
            });
        });
        // Standard: Social Media Tab aktiv
        if (tabs.length) {
            setActiveTab('social');
            filterResults('social');
        }
    const form = document.getElementById('search-form');
    const resetBtn = document.getElementById('reset-btn');
    const catBar = document.getElementById('category-bar-search');
    const fields = [
        'query', 'real_name', 'clan_name', 'age', 'postal_code'
    ];
    const platformCheckboxes = () => Array.from(document.querySelectorAll('input[name="platforms"]'));
    const deepSearch = document.querySelector('input[name="deep_search"]');
    const storageKey = 'shadowseek_search_inputs';

    // --- Kategorien aus URL/Storage übernehmen ---
    function getCategoriesFromURL() {
        const params = new URLSearchParams(window.location.search);
        const cats = params.get('categories');
        if (!cats) return [];
        return cats.split(',').map(s => s.trim()).filter(Boolean);
    }
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

    // --- Modifier/Modus-State aus Query/Storage übernehmen ---
    function getModifiersFromURL() {
        const params = new URLSearchParams(window.location.search);
        return MODIFIERS.map(m => m.value).filter(val => params.get(val) === 'true');
    }
    let selectedMods = getSelectedModifiers();
    const urlMods = getModifiersFromURL();
    if (urlMods.length > 0) {
        selectedMods = urlMods;
        setSelectedModifiers(selectedMods);
    }
    // DeepSearch-Checkbox synchronisieren
    if (deepSearch) {
        deepSearch.checked = selectedMods.includes('deepsearch');
    }

    // --- Modifier/Modus-Chips auf Suchseite rendern (optional, falls UI) ---
    // (Hier: nur State, UI kann in search.html ergänzt werden)

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

    // Restore on load (inkl. State-Übernahme von Home)
    // Query, Kategorien, Modus-Chips aus localStorage/URL übernehmen
    function restoreStateFromHome() {
        // Query
        const params = new URLSearchParams(window.location.search);
        if (params.has('query') && form.elements['query']) {
            form.elements['query'].value = params.get('query');
        }
        // Kategorien
        if (params.has('categories')) {
            const cats = params.get('categories').split(',').map(s => s.trim()).filter(Boolean);
            setSelectedCategories(cats);
            selected = cats;
            renderChips();
        }
        // Modus-Chips
        MODIFIERS.forEach(m => {
            if (params.get(m.value) === 'true') {
                if (!selectedMods.includes(m.value)) selectedMods.push(m.value);
            }
        });
        setSelectedModifiers(selectedMods);
        if (deepSearch) deepSearch.checked = selectedMods.includes('deepsearch');
    }
    restoreInputs();
    restoreStateFromHome();

    // === Scan Overlay Integration (robust) ===
    let scanOverlayCtrl = null;
    form.addEventListener('submit', function (e) {
        // Plattformen auslesen
        const platformEls = platformCheckboxes();
        const platforms = platformEls.filter(cb => cb.checked).map(cb => cb.parentElement?.innerText.trim() || cb.value);
        const deepSearchActive = deepSearch && deepSearch.checked;
        // Modifier-Flags als Query-Parameter übergeben
        let url = new URL(form.action, window.location.origin);
        const params = new URLSearchParams(new FormData(form));
        // Kategorien
        if (selected.length > 0) {
            params.set('categories', selected.join(','));
        }
        // Modifier
        if (selectedMods && selectedMods.length > 0) {
            selectedMods.forEach(mod => {
                params.set(mod, 'true');
            });
        }
        // DeepSearch synchronisieren
        if (deepSearchActive && !selectedMods.includes('deepsearch')) {
            params.set('deepsearch', 'true');
        }
        url.search = params.toString();
        form.action = url.pathname + url.search;
        // DeepSearch-Badge immer sichtbar, wenn aktiv
        const deepBadge = document.getElementById('scan-deep-badge');
        if (deepBadge) deepBadge.style.display = deepSearchActive ? '' : 'none';
        // Scan-Overlay an aktive Tabs koppeln
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab) {
            const scanStatus = document.getElementById('scan-status-text');
            if (scanStatus) scanStatus.textContent = 'Scan: ' + activeTab.textContent + (deepSearchActive ? ' (DeepSearch aktiv)' : '');
        }
        scanOverlayCtrl = showScanOverlay(platforms, deepSearchActive);
        // Nach 14s Timeout (Fallback)
        setTimeout(() => { if (scanOverlayCtrl) scanOverlayCtrl.error('Zeitüberschreitung – keine Antwort'); }, 14000);
    });

    // Reset-Button
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            // Suchfeld und Inputs zurücksetzen
            clearInputs();
            // Kategorien zurücksetzen
            clearSelectedCategories();
            selected = [];
            renderChips();
            // Modus-Chips zurücksetzen
            setSelectedModifiers([]);
            selectedMods = [];
            // DeepSearch-Checkbox zurücksetzen
            if (deepSearch) deepSearch.checked = false;
            // Query-Parameter bereinigen
            const url = new URL(window.location.href);
            url.searchParams.delete('categories');
            MODIFIERS.forEach(m => url.searchParams.delete(m.value));
            window.history.replaceState({}, '', url.pathname + url.search);
            // localStorage komplett leeren (nur ShadowSeek-relevante Keys)
            localStorage.removeItem('shadowseek_categories');
            localStorage.removeItem('shadowseek_modifiers');
            localStorage.removeItem('shadowseek_search_inputs');
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
