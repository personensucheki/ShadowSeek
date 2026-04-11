const SUGGESTIONS = [
    "tiktok username finden",
    "instagram email lookup",
    "snapchat user suchen",
    "twitch live einnahmen",
    "youtube superchat analyse",
    "osint tools",
    "personen finden",
    "reverse image search",
    "deep web suche",
    "telegram nutzer identifizieren",
];

const CATEGORIES = [
    { label: "Social Media", value: "social" },
    { label: "Dating", value: "dating" },
    { label: "Adult", value: "adult" },
    { label: "Porn", value: "porn" },
];

const MODIFIERS = [
    { label: "Oeffentliche Quellen", value: "public_sources" },
    { label: "Sicherer Suchmodus", value: "secure_mode" },
    { label: "KI-gestuetzte Bewertung", value: "ai_rerank" },
    { label: "DeepSearch bereit", value: "deepsearch" },
    { label: "Praezise Treffer", value: "precision_mode" },
];

function autocomplete(input, suggestions) {
    let currentFocus = -1;

    input.addEventListener("input", function () {
        let item;
        let match;
        let index;
        const value = this.value;

        closeAllLists();
        if (!value) {
            return false;
        }

        currentFocus = -1;
        item = document.createElement("div");
        item.setAttribute("id", `${this.id}-autocomplete-list`);
        item.setAttribute("class", "autocomplete-items");
        this.parentNode.appendChild(item);

        for (index = 0; index < suggestions.length; index += 1) {
            if (!suggestions[index].toLowerCase().includes(value.toLowerCase())) {
                continue;
            }

            match = document.createElement("div");
            match.innerHTML = suggestions[index].replace(
                new RegExp(value, "gi"),
                (found) => `<strong>${found}</strong>`,
            );
            match.addEventListener("click", function () {
                input.value = this.textContent;
                closeAllLists();
            });
            item.appendChild(match);
        }
        return true;
    });

    input.addEventListener("keydown", function (event) {
        let items = document.getElementById(`${this.id}-autocomplete-list`);
        if (items) {
            items = items.getElementsByTagName("div");
        }

        if (event.keyCode === 40) {
            currentFocus += 1;
            addActive(items);
        } else if (event.keyCode === 38) {
            currentFocus -= 1;
            addActive(items);
        } else if (event.keyCode === 13) {
            event.preventDefault();
            if (currentFocus > -1 && items) {
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

    function closeAllLists(element) {
        const items = document.getElementsByClassName("autocomplete-items");
        for (let index = 0; index < items.length; index += 1) {
            if (element !== items[index] && element !== input) {
                items[index].parentNode.removeChild(items[index]);
            }
        }
    }

    document.addEventListener("click", function (event) {
        closeAllLists(event.target);
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
    const categoryBar = document.getElementById("category-bar");
    const modifierBar = document.getElementById("modifier-bar");
    let selectedCategories = getSelectedCategories();
    let selectedModifiers = getSelectedModifiers();

    if (input) {
        autocomplete(input, SUGGESTIONS);
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

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const query = input.value.trim();
        if (!query) {
            input.focus();
            return;
        }

        input.value = query;
        input.focus();
    });
});
