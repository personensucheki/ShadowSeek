const FALLBACK_SUGGESTIONS = [
    "facebook",
    "facebook login",
    "instagram",
    "tiktok",
    "youtube",
    "twitch",
    "reddit",
    "telegram",
    "reverse image search",
    "profile monitoring",
];

const CATEGORIES = [
    { label: "Social Media", value: "social" },
    { label: "Dating", value: "dating" },
    { label: "Adult", value: "adult" },
    { label: "Porn", value: "porn" },
];

const MODIFIERS = [
    { label: "Oeffentliche Signale", value: "public_sources" },
    { label: "Sicherer Suchmodus", value: "secure_mode" },
    { label: "KI-gestuetzte Bewertung", value: "ai_rerank" },
    { label: "DeepSearch bereit", value: "deepsearch" },
    { label: "Praezise Treffer", value: "precision_mode" },
];

function debounce(fn, waitMs) {
    let timer = null;
    return (...args) => {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => fn(...args), waitMs);
    };
}

function renderAutocompleteList(container, input, suggestions, query) {
    container.innerHTML = "";

    if (!suggestions.length) {
        container.style.display = "none";
        return;
    }

    container.style.display = "block";

    const iconSvg = (type) => {
        if (type === "external") {
            return `
<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3z"></path>
  <path d="M5 5h6v2H7v10h10v-4h2v6H5V5z"></path>
</svg>`.trim();
        }
        return `
<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M10 4a6 6 0 104.47 10.03l4.25 4.24 1.41-1.41-4.24-4.25A6 6 0 0010 4zm0 2a4 4 0 110 8 4 4 0 010-8z"></path>
</svg>`.trim();
    };

    const looksLikeUrl = (text) => {
        const value = (text || "").trim().toLowerCase();
        return (
            value.startsWith("http://") ||
            value.startsWith("https://") ||
            value.includes("site:") ||
            /^[a-z0-9.-]+\.[a-z]{2,}($|\/|\s)/.test(value)
        );
    };

    suggestions.forEach((text) => {
        const item = document.createElement("div");
        item.className = "autocomplete-item";
        item.setAttribute("role", "option");

        const icon = document.createElement("span");
        icon.className = "autocomplete-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.innerHTML = iconSvg(looksLikeUrl(text) ? "external" : "search");

        const label = document.createElement("span");
        label.className = "autocomplete-label";

        const safeQuery = (query || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        if (safeQuery) {
            label.innerHTML = text.replace(new RegExp(safeQuery, "gi"), (found) => `<strong>${found}</strong>`);
        } else {
            label.textContent = text;
        }

        item.append(icon, label);
        item.addEventListener("click", () => {
            input.value = item.textContent;
            container.style.display = "none";
            input.focus();
        });
        container.appendChild(item);
    });
}

async function fetchSuggestions(query, engine) {
    const url = `/api/suggest?${new URLSearchParams({ q: query, engine: engine || "shadowseek" }).toString()}`;
    const response = await fetch(url, { method: "GET", headers: { Accept: "application/json" } });
    const payload = await response.json().catch(() => ({}));
    const suggestions = Array.isArray(payload.suggestions) ? payload.suggestions : [];
    return suggestions.slice(0, 10);
}

function autocomplete(input, engineSelect, listContainer) {
    let currentFocus = -1;
    let lastSuggestions = [];

    const closeAllLists = () => {
        if (listContainer) {
            listContainer.style.display = "none";
            listContainer.innerHTML = "";
        }
        currentFocus = -1;
    };

    const requestAndRender = debounce(async () => {
        const value = input.value.trim();
        if (!value) {
            closeAllLists();
            return;
        }

        const engine = engineSelect?.value || "shadowseek";

        try {
            lastSuggestions = await fetchSuggestions(value, engine);
        } catch {
            lastSuggestions = FALLBACK_SUGGESTIONS.filter((s) => s.toLowerCase().includes(value.toLowerCase())).slice(0, 10);
        }

        renderAutocompleteList(listContainer, input, lastSuggestions, value);
    }, 120);

    input.addEventListener("input", requestAndRender);
    engineSelect?.addEventListener("change", requestAndRender);

    input.addEventListener("keydown", function (event) {
        const items = listContainer ? Array.from(listContainer.getElementsByTagName("div")) : [];

        if (event.keyCode === 40) {
            currentFocus += 1;
            addActive(items);
        } else if (event.keyCode === 38) {
            currentFocus -= 1;
            addActive(items);
        } else if (event.keyCode === 13) {
            if (listContainer && listContainer.style.display !== "none" && currentFocus > -1 && items[currentFocus]) {
                event.preventDefault();
                items[currentFocus].click();
            }
        }
    });

    function addActive(items) {
        if (!items) {
            return;
        }
        removeActive(items);
        if (currentFocus >= items.length) {
            currentFocus = 0;
        }
        if (currentFocus < 0) {
            currentFocus = items.length - 1;
        }
        items[currentFocus].classList.add("autocomplete-active");
    }

    function removeActive(items) {
        for (let index = 0; index < items.length; index += 1) {
            items[index].classList.remove("autocomplete-active");
        }
    }

    document.addEventListener("click", function(event) {
        if (!listContainer) {
            return;
        }
        if (event.target === input || listContainer.contains(event.target)) {
            return;
        }
        closeAllLists();
    });

    input.addEventListener("blur", () => {
        window.setTimeout(closeAllLists, 120);
    });
}

function getSelectedCategories() {
    try {
        const raw = localStorage.getItem("shadowseek_categories");
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

function setSelectedCategories(values) {
    localStorage.setItem("shadowseek_categories", JSON.stringify(values));
}

function getSelectedModifiers() {
    try {
        const raw = localStorage.getItem("shadowseek_modifiers");
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

function setSelectedModifiers(values) {
    localStorage.setItem("shadowseek_modifiers", JSON.stringify(values));
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("landing-search-form");
    const input = document.getElementById("search-autocomplete");
    const engineSelect = document.getElementById("engine-select");
    const listContainer = document.getElementById("autocomplete-list") || document.querySelector(".autocomplete-items");
    const resultsSection = document.getElementById("home-results");
    const resultsQuery = document.getElementById("home-results-query");
    const resultsMeta = document.getElementById("home-results-meta");
    const resultsList = document.getElementById("home-results-list");
    const categoryBar = document.getElementById("category-bar");
    const modifierBar = document.getElementById("modifier-bar");
    let selectedCategories = getSelectedCategories();
    let selectedModifiers = getSelectedModifiers();

    if (input) {
        autocomplete(input, engineSelect, listContainer);
    }

    const renderChips = () => {
        if (!categoryBar) {
            return;
        }

        categoryBar.innerHTML = "";
        CATEGORIES.forEach((category) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = `category-chip${selectedCategories.includes(category.value) ? " active" : ""}`;
            button.textContent = category.label;
            button.addEventListener("click", () => {
                if (selectedCategories.includes(category.value)) {
                    selectedCategories = selectedCategories.filter((value) => value !== category.value);
                } else {
                    selectedCategories = [...selectedCategories, category.value];
                }
                setSelectedCategories(selectedCategories);
                renderChips();
            });
            categoryBar.appendChild(button);
        });
    };

    const renderModifiers = () => {
        if (!modifierBar) {
            return;
        }

        Array.from(modifierBar.children).forEach((button, index) => {
            const value = MODIFIERS[index]?.value;
            if (!value) {
                return;
            }

            button.classList.toggle("active", selectedModifiers.includes(value));
            button.onclick = () => {
                if (selectedModifiers.includes(value)) {
                    selectedModifiers = selectedModifiers.filter((item) => item !== value);
                } else {
                    selectedModifiers = [...selectedModifiers, value];
                }
                setSelectedModifiers(selectedModifiers);
                renderModifiers();
            };
        });
    };

    renderChips();
    renderModifiers();

    if (input && !input.value) {
        setSelectedCategories([]);
        setSelectedModifiers([]);
        selectedCategories = [];
        selectedModifiers = [];
        renderChips();
        renderModifiers();
    }

    if (!form || !input) {
        return;
    }

    const renderResults = (payload) => {
        if (!resultsSection || !resultsList || !resultsQuery || !resultsMeta) {
            return;
        }

        resultsList.innerHTML = "";
        resultsSection.hidden = false;

        const q = payload?.query || input.value.trim();
        const items = Array.isArray(payload?.results) ? payload.results : [];
        resultsQuery.textContent = q ? `Ergebnisse fuer: ${q}` : "Ergebnisse";
        resultsMeta.textContent = items.length ? `${items.length} Ergebnisse` : "";

        if (!items.length) {
            const empty = document.createElement("div");
            empty.className = "empty-state";
            empty.textContent = "Keine Ergebnisse gefunden. Versuche einen anderen Begriff.";
            resultsList.appendChild(empty);
            return;
        }

        items.forEach((item) => {
            const url = (item?.url || "").trim();
            const title = (item?.title || "").trim();
            const snippet = (item?.snippet || "").trim();
            if (!url || !title) {
                return;
            }

            const card = document.createElement("article");
            card.className = "home-result";

            const urlLink = document.createElement("a");
            urlLink.className = "home-result-url";
            urlLink.href = url;
            urlLink.target = "_blank";
            urlLink.rel = "noopener noreferrer";
            urlLink.textContent = url;

            const h3 = document.createElement("h3");
            h3.className = "home-result-title";
            const titleLink = document.createElement("a");
            titleLink.href = url;
            titleLink.target = "_blank";
            titleLink.rel = "noopener noreferrer";
            titleLink.textContent = title;
            h3.appendChild(titleLink);

            const p = document.createElement("p");
            p.className = "home-result-snippet";
            p.textContent = snippet || "";

            card.append(urlLink, h3, p);
            resultsList.appendChild(card);
        });
    };

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const query = input.value.trim();
        if (!query) {
            input.focus();
            return;
        }

        const engine = engineSelect?.value || "shadowseek";
        input.value = query;

        if (resultsSection) {
            resultsSection.hidden = false;
        }
        if (resultsList) {
            resultsList.innerHTML = "";
        }
        if (resultsQuery) {
            resultsQuery.textContent = `Suche laeuft: ${query}`;
        }
        if (resultsMeta) {
            resultsMeta.textContent = "";
        }

        fetch(`/api/websearch?${new URLSearchParams({ q: query, engine }).toString()}`, {
            method: "GET",
            headers: { Accept: "application/json" },
        })
            .then((r) => r.json().catch(() => ({})))
            .then((payload) => renderResults(payload))
            .catch(() => renderResults({ query, results: [] }))
            .finally(() => {
                resultsSection?.scrollIntoView({ behavior: "smooth", block: "start" });
            });
    });
});
