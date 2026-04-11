// --- Autocomplete Vorschläge (Dummy, kann durch API ersetzt werden) ---
const SUGGESTIONS = [
    "tiktok username finden", "instagram email lookup", "snapchat user suchen", "twitch live einnahmen", "youtube superchat analyse", "osint tools", "personen finden", "reverse image search", "deep web suche", "telegram nutzer identifizieren"
];

function autocomplete(inp, arr) {
    let currentFocus;
    inp.addEventListener("input", function(e) {
        let a, b, i, val = this.value;
        closeAllLists();
        if (!val) { return false; }
        currentFocus = -1;
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "-autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        this.parentNode.appendChild(a);
        for (i = 0; i < arr.length; i++) {
            if (arr[i].toLowerCase().includes(val.toLowerCase())) {
                b = document.createElement("DIV");
                b.innerHTML = arr[i].replace(new RegExp(val, "gi"), match => `<strong>${match}</strong>`);
                b.addEventListener("click", function(e) {
                    inp.value = this.textContent;
                    closeAllLists();
                });
                a.appendChild(b);
            }
        }
    });
    inp.addEventListener("keydown", function(e) {
        let x = document.getElementById(this.id + "-autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            currentFocus++;
            addActive(x);
        } else if (e.keyCode == 38) {
            currentFocus--;
            addActive(x);
        } else if (e.keyCode == 13) {
            e.preventDefault();
            if (currentFocus > -1 && x) {
                x[currentFocus].click();
            }
        }
    });
    function addActive(x) {
        if (!x) return false;
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
        for (let i = 0; i < x.length; i++) {
            x[i].classList.remove("autocomplete-active");
        }
    }
    function closeAllLists(elmnt) {
        const items = document.getElementsByClassName("autocomplete-items");
        for (let i = 0; i < items.length; i++) {
            if (elmnt != items[i] && elmnt != inp) {
                items[i].parentNode.removeChild(items[i]);
            }
        }
    }
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    // ...existing code...
    const acInput = document.getElementById("search-autocomplete");
    if (acInput) autocomplete(acInput, SUGGESTIONS);
    // ...existing code...
});
// Kategorie-Buttons: State und Übergabe an /search
const CATEGORIES = [
    { label: "Social Media", value: "social" },
    { label: "Dating", value: "dating" },
    { label: "Adult", value: "adult" },
    { label: "Porn", value: "porn" },
];

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

// --- Modifier/Modus-Logik ---
const MODIFIERS = [
    { label: "Öffentliche Quellen", value: "public_sources" },
    { label: "Sicherer Suchmodus", value: "secure_mode" },
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

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("landing-search-form");
    const input = form?.querySelector("input[name='query']");
    const catBar = document.getElementById("category-bar");
    const modBar = document.getElementById("modifier-bar");
    let selected = getSelectedCategories();
    let selectedMods = getSelectedModifiers();

    // Render Kategorie-Chips
    if (catBar) {
        catBar.innerHTML = "";
        CATEGORIES.forEach(cat => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "category-chip" + (selected.includes(cat.value) ? " active" : "");
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

    // --- Modifier/Modus-Chips ---
    function renderModifiers() {
        if (!modBar) return;
        Array.from(modBar.children).forEach((btn, i) => {
            const val = MODIFIERS[i].value;
            btn.classList.toggle("active", selectedMods.includes(val));
            btn.onclick = () => {
                if (selectedMods.includes(val)) {
                    selectedMods = selectedMods.filter(v => v !== val);
                } else {
                    selectedMods.push(val);
                }
                setSelectedModifiers(selectedMods);
                renderModifiers();
                // DeepSearch-Sync
                if (val === "deepsearch") {
                    // DeepSearch-Modus toggeln
                    // (kann später mit Checkbox auf /search synchronisiert werden)
                }
            };
        });
    }
    renderModifiers();

    // Reset bei Seitenaufruf
    if (!input.value) {
        setSelectedCategories([]);
        selected = [];
        renderChips();
        setSelectedModifiers([]);
        selectedMods = [];
        renderModifiers();
    }

    // Suche absenden
    if (form && input) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const query = input.value.trim();
            if (!query) {
                input.focus();
                return;
            }
            // Kategorien und Modifier an /search übergeben
            let url = `/search?query=${encodeURIComponent(query)}`;
            if (selected.length > 0) {
                url += `&categories=${encodeURIComponent(selected.join(","))}`;
            }
            if (selectedMods.length > 0) {
                selectedMods.forEach(mod => {
                    url += `&${encodeURIComponent(mod)}=true`;
                });
            }
            window.location.href = url;
        });
    }
});
