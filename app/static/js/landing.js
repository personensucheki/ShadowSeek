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

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("landing-search-form");
    const input = form?.querySelector("input[name='query']");
    const catBar = document.getElementById("category-bar");
    let selected = getSelectedCategories();

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

    // Reset bei Seitenaufruf
    if (!input.value) {
        setSelectedCategories([]);
        selected = [];
        renderChips();
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
            // Kategorien an /search übergeben
            let url = `/search?query=${encodeURIComponent(query)}`;
            if (selected.length > 0) {
                url += `&categories=${encodeURIComponent(selected.join(","))}`;
            }
            window.location.href = url;
        });
    }
});
