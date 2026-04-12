const CATEGORIES = [
    { label: "Social Media", value: "social" },
    { label: "Gaming", value: "gaming" },
    { label: "Dating", value: "dating" },
    { label: "Adult", value: "adult" },
    { label: "Cam", value: "cam" },
    { label: "Porn", value: "porn" },
    { label: "Forums", value: "forums" },
];

const MODIFIERS = [
    { label: "Oeffentliche Quellen", value: "public_sources" },
    { label: "Sicherer Suchmodus", value: "secure_mode" },
    { label: "KI-gestuetzte Bewertung", value: "ai_rerank" },
    { label: "DeepSearch bereit", value: "deepsearch" },
    { label: "Praezise Treffer", value: "precision_mode" },
];

const TAB_CATEGORIES = {
    social: ["social", "instagram", "tiktok", "x", "twitter", "facebook", "linkedin", "snapchat", "clapper"],
    dating: ["dating", "lovoo", "badoo", "knuddels", "bumble", "okcupid", "hinge", "jaumo", "tinder"],
    adult: ["adult", "stripchat", "onlyfans", "dirtyhobby", "subscription", "fansly", "manyvids", "patreon"],
    porn: ["porn", "xhamster", "pornhub", "xnxx"],
    web: ["web", "website", "domain", "developer", "github", "steam", "epic_games", "xbox", "playstation", "twitch", "kick"],
    forum: ["forum", "board", "reddit", "discord", "vk", "weibo", "tumblr"],
    image: ["image", "imgur", "flickr", "photo"],
    video: ["video", "youtube", "twitch", "vimeo", "streaming", "cam", "chaturbate", "livejasmin", "camsoda", "bongacams"],
    news: ["news", "zeitung", "magazine"],
    community: ["community", "discord", "telegram", "messaging"],
};

const SCAN_STATUS_TEXTS = [
    "Query wird vorbereitet...",
    "DeepSearch scannt Plattformen...",
    "Plattformen werden geprueft...",
    "Signale werden zusammengefuehrt...",
    "Ergebnisse werden bewertet...",
];

const SCAN_STATUS_TEXTS_DEEP = [
    "DeepSearch aktiv...",
    "Erweiterte Analyse laeuft...",
];

function readJsonStorage(key, fallback = []) {
    try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch {
        return fallback;
    }
}

function writeJsonStorage(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function normalizeTabValue(result) {
    const slug = String(result.platform_slug || "").toLowerCase();
    const category = String(result.category || "").toLowerCase();

    for (const [tab, values] of Object.entries(TAB_CATEGORIES)) {
        if (values.includes(slug) || values.includes(category)) {
            return tab;
        }
    }

    return "social";
}

function renderPlatforms(platforms, container) {
    if (!container) {
        return;
    }

    container.innerHTML = "";
    platforms.forEach((platform) => {
        const chip = document.createElement("div");
        chip.className = "scan-platform-chip";
        chip.innerHTML = `<span class="scan-platform-dot"></span>${escapeHtml(platform)}`;
        container.appendChild(chip);
    });
}

function showScanOverlay(platforms, deepSearch) {
    const overlay = document.getElementById("scan-overlay");
    const statusText = document.getElementById("scan-status-text");
    const progressInner = document.getElementById("scan-progress-inner");
    const deepBadge = document.getElementById("scan-deep-badge");
    const platformList = document.getElementById("scan-platform-list");

    if (!overlay || !statusText || !progressInner || !platformList) {
        return { hide() {}, error() {} };
    }

    const statusTexts = deepSearch
        ? [...SCAN_STATUS_TEXTS_DEEP, ...SCAN_STATUS_TEXTS]
        : [...SCAN_STATUS_TEXTS];
    let timerId = null;
    let progressId = null;
    let index = 0;
    let active = 0;

    overlay.style.display = "";
    overlay.classList.remove("hide", "error");
    progressInner.style.width = "0%";
    if (deepBadge) {
        deepBadge.style.display = deepSearch ? "" : "none";
    }

    renderPlatforms(platforms, platformList);

    const rotateStatus = () => {
        statusText.textContent = statusTexts[index % statusTexts.length];
        index += 1;
        timerId = window.setTimeout(rotateStatus, 1200);
    };

    const animateProgress = () => {
        const children = Array.from(platformList.children);
        children.forEach((child, childIndex) => {
            child.classList.toggle("active", childIndex === active);
            child.classList.toggle("done", childIndex < active);
        });
        if (children.length > 0) {
            progressInner.style.width = `${Math.min((active / children.length) * 100, 95)}%`;
        }
        active = Math.min(active + 1, Math.max(children.length, 1));
        progressId = window.setTimeout(animateProgress, 500);
    };

    rotateStatus();
    animateProgress();

    return {
        hide() {
            window.clearTimeout(timerId);
            window.clearTimeout(progressId);
            progressInner.style.width = "100%";
            overlay.classList.add("hide");
            window.setTimeout(() => {
                overlay.style.display = "none";
            }, 300);
        },
        error(message) {
            window.clearTimeout(timerId);
            window.clearTimeout(progressId);
            overlay.classList.add("error");
            statusText.textContent = message || "Suche fehlgeschlagen";
            window.setTimeout(() => {
                overlay.style.display = "none";
            }, 1200);
        },
    };
}

function createMessage(type, text) {
    const message = document.createElement("div");
    message.className = `chip chip--${type}`;
    message.textContent = text;
    return message;
}

function renderMessages(payload, container) {
    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (payload?.meta?.profile_count !== undefined && payload.meta.profile_count !== null) {
        container.appendChild(
            createMessage("green", `${payload.meta.profile_count} Link-Kandidaten erzeugt`)
        );
    }

    if (payload?.meta?.ai_reranking_applied) {
        container.appendChild(createMessage("cyan", "KI-Reranking aktiv"));
    }

    if (payload?.meta?.safe_mode) {
        container.appendChild(createMessage("cyan", "Safe Mode aktiv"));
    }

    if (payload?.meta?.serper_used) {
        container.appendChild(
            createMessage("pink", `Serper genutzt (${payload.meta.serper_queries} Queries)`)
        );
    }
}

function appendMessage(container, type, text) {
    if (!container || !text) {
        return;
    }
    container.appendChild(createMessage(type, text));
}

function renderReverseImageLinks(links, container) {
    if (!container) {
        return;
    }

    if (!links || !links.asset_url) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = `
        <div class="result-card">
            <div class="result-info">
                <div class="result-platform">Reverse Image Search</div>
                <div class="result-title">Direkte Bild-Checks</div>
                <div class="result-meta-row">
                    <a href="${escapeHtml(links.google_lens)}" target="_blank" rel="noopener" class="result-link">Google Lens</a>
                    <a href="${escapeHtml(links.tineye)}" target="_blank" rel="noopener" class="result-link">TinEye</a>
                    <a href="${escapeHtml(links.yandex)}" target="_blank" rel="noopener" class="result-link">Yandex</a>
                </div>
            </div>
        </div>
    `;
}

function renderProfiles(profiles, container) {
    if (!container) {
        return;
    }

    if (!Array.isArray(profiles) || profiles.length === 0) {
        container.innerHTML = '<div class="empty-state">Keine Ergebnisse gefunden. Bitte verfeinere deine Suche.</div>';
        return;
    }

    container.innerHTML = profiles
        .map((result, idx) => {
            const tab = normalizeTabValue(result);
            const confidenceChip = result.confidence
                ? `<span class="chip chip--${result.confidence === "high" ? "green" : result.confidence === "medium" ? "cyan" : "pink"}">Confidence: ${escapeHtml(result.confidence)}</span>`
                : "";
            const scoreChip = result.match_score !== undefined && result.match_score !== null
                ? `<span class="chip chip--variation">Score: ${escapeHtml(result.match_score)}</span>`
                : "";
            const reason = result.match_reason || result.match_reasons?.join(", ") || "";
            const title = result.title || result.bio || result.snippet || "";

            // Nur einmal das Badge oben rechts im Ergebnisbereich
            const aiBadge = result.confidence === "high"
                ? `<div class="ai-badge">AI Ranked</div>`
                : "";

            return `
                <div class="result-card" data-tab="${escapeHtml(tab)}" data-platform="${escapeHtml(result.platform_slug || "")}">
                    ${aiBadge}
                    <div class="result-info">
                        <div class="result-platform">${escapeHtml(result.platform || "Unbekannt")}</div>
                        <div class="result-title">${escapeHtml(result.category || "profile")}</div>
                        ${title ? `<div class="result-bio">${escapeHtml(title)}</div>` : ""}
                        <div class="result-meta-row">
                            ${confidenceChip}
                            ${scoreChip}
                            ${reason ? `<span class="chip chip--green">${escapeHtml(reason)}</span>` : ""}
                        </div>
                        <a href="${escapeHtml(result.url || result.profile_url || "#")}" target="_blank" rel="noopener" class="result-link">Profil oeffnen</a>
                    </div>
                </div>
            `;
        })
        .join("");
}

function renderSimilarityResults(data) {
    const list = document.getElementById("similarity-list");
    if (!list) {
        return;
    }

    if (!data || !Array.isArray(data.matches) || data.matches.length === 0) {
        list.innerHTML = '<div class="empty-state">No data available</div>';
        return;
    }

    list.innerHTML = data.matches
        .map((item) => {
            let badge = "weak";
            if (item.score >= 90) {
                badge = "very-close";
            } else if (item.score >= 75) {
                badge = "close";
            } else if (item.score >= 60) {
                badge = "possible";
            }
            return `
                <div class="similarity-item">
                    <span class="sim-candidate">${escapeHtml(item.candidate)}</span>
                    <span class="sim-score">${escapeHtml(item.score)}</span>
                    <span class="sim-badge sim-badge--${badge}">${badge.replace("-", " ")}</span>
                </div>
            `;
        })
        .join("");
}

function renderScreenshotResults(data) {
    const list = document.getElementById("screenshot-list");
    if (!list) {
        return;
    }

    if (!Array.isArray(data) || data.length === 0) {
        list.innerHTML = '<div class="empty-state">No data available</div>';
        return;
    }

    list.innerHTML = data
        .map(
            (item) => `
                <div class="screenshot-item">
                    <div class="screenshot-url">${escapeHtml(item.url)}</div>
                    <img src="${escapeHtml(item.path)}" alt="Screenshot" style="max-width:320px;border-radius:8px;box-shadow:0 0 12px #00FF9F55,0 0 8px #FF00FF33;">
                </div>
            `
        )
        .join("");
}

function renderImageSimilarity(data) {
    const list = document.getElementById("image-similarity-list");
    if (!list) {
        return;
    }

    if (!data || !Array.isArray(data.matches) || data.matches.length === 0) {
        list.innerHTML = '<div class="empty-state">No data available</div>';
        return;
    }

    list.innerHTML = data.matches
        .map(
            (item) => `
                <div class="image-match-item">
                    <img src="${escapeHtml(item.file)}" alt="Match" style="max-width:80px;border-radius:6px;margin-right:10px;vertical-align:middle;">
                    <span class="img-score">${escapeHtml(item.score)}</span>
                </div>
            `
        )
        .join("");
}

function renderRiskScore(data) {
    const box = document.getElementById("risk-score-box");
    if (!box) {
        return;
    }

    if (!data || typeof data.score !== "number") {
        box.innerHTML = '<div class="empty-state">No data available</div>';
        return;
    }

    let color = "#00FF9F";
    if (data.level === "critical") {
        color = "#FF00FF";
    } else if (data.level === "high") {
        color = "#FF6B6B";
    } else if (data.level === "moderate") {
        color = "#FFD600";
    }

    box.innerHTML = `
        <div class="risk-score-main" style="font-size:2.2em;font-weight:700;color:${color};margin-bottom:0.3em;">
            ${escapeHtml(data.score)} <span style="font-size:0.5em;">/ 100</span>
        </div>
        <div class="risk-score-level" style="font-weight:600;color:${color};margin-bottom:0.7em;">
            ${escapeHtml(String(data.level || "").toUpperCase())}
        </div>
        ${
            Array.isArray(data.factors) && data.factors.length > 0
                ? `<ul class="risk-factors">${data.factors.map((factor) => `<li>${escapeHtml(factor)}</li>`).join("")}</ul>`
                : ""
        }
    `;
}

function renderDeepSearchResponse(response) {
    if (!response || !response.data) {
        renderScreenshotResults([]);
        renderSimilarityResults({ matches: [] });
        renderImageSimilarity({ matches: [] });
        renderRiskScore(null);
        return;
    }

    renderScreenshotResults(response.data.screenshots);
    renderSimilarityResults(response.data.similarity);
    renderImageSimilarity(response.data.image_similarity);
    renderRiskScore(response.data.risk_score);
}

function resetAnalysisWidgets() {
    renderDeepSearchResponse(null);
}

function buildDeepSearchPayload(searchPayload) {
    const profiles = Array.isArray(searchPayload?.profiles) ? searchPayload.profiles : [];
    const profileUrls = profiles
        .map((profile) => profile?.url || profile?.profile_url)
        .filter(Boolean);

    const maxImageScore = Array.isArray(searchPayload?.image_similarity?.matches)
        ? Math.max(...searchPayload.image_similarity.matches.map((item) => Number(item?.score) || 0), 0)
        : 0;

    return {
        base_username: "",
        candidates: [],
        profile_urls: profileUrls,
        reference_image: searchPayload?.reverse_image_search?.asset_url || null,
        gallery: [],
        riskdata: {
            has_real_name: false,
            has_age: false,
            username_count: 0,
            platform_count: profiles.length,
            has_reverse_image: Boolean(searchPayload?.reverse_image_search?.asset_url),
            image_reuse_score: maxImageScore,
        },
        usernames: [],
        profiles,
        reverse_image: searchPayload?.reverse_image_search || {},
    };
}

async function requestDeepSearchAnalysis(searchPayload, csrfToken) {
    const response = await fetch("/search/deepsearch", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        credentials: "same-origin",
        body: JSON.stringify(buildDeepSearchPayload(searchPayload)),
    });

    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
        ? await response.json()
        : { error: "Unexpected server response." };

    if (!response.ok) {
        throw new Error(payload.error || "DeepSearch fehlgeschlagen.");
    }

    return payload;
}

function applyResultFilter(tab) {
    const resultsList = document.getElementById("results-list");
    if (!resultsList) {
        return;
    }

    Array.from(resultsList.querySelectorAll(".empty-state")).forEach((node, index) => {
        if (index > 0) {
            node.remove();
        }
    });

    const cards = Array.from(resultsList.querySelectorAll(".result-card"));
    let visible = 0;

    cards.forEach((card) => {
        const shouldShow = card.dataset.tab === tab;
        card.style.display = shouldShow ? "" : "none";
        if (shouldShow) {
            visible += 1;
        }
    });

    const emptyState = resultsList.querySelector(".empty-state");
    if (emptyState) {
        emptyState.style.display = visible === 0 ? "" : "none";
    } else if (visible === 0) {
        resultsList.insertAdjacentHTML(
            "beforeend",
            '<div class="empty-state">Keine Ergebnisse in dieser Kategorie.</div>'
        );
    }
}

function setActiveTab(tab) {
    document.querySelectorAll(".tab-btn").forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tab);
    });
    applyResultFilter(tab);
}

function findPreferredTab(profiles) {
    if (!Array.isArray(profiles) || profiles.length === 0) {
        return "social";
    }

    const availableTabs = new Set(profiles.map((profile) => normalizeTabValue(profile)));
    return availableTabs.has("social") ? "social" : profiles.map((profile) => normalizeTabValue(profile))[0];
}

document.addEventListener("DOMContentLoaded", async () => {
    const form = document.getElementById("search-form");
    const resultsList = document.getElementById("results-list");
    const reverseLinks = document.getElementById("reverse-links");
    const messageBox = document.getElementById("search-messages");
    const resetButton = document.getElementById("reset-btn");
    const categoryBar = document.getElementById("category-bar-search");
    const modifierBar = document.getElementById("modifier-bar-search");
    const deepSearchToggle = form?.querySelector('input[name="deep_search"]');
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
    const storageKey = "shadowseek_search_inputs";
    let selectedCategories = readJsonStorage("shadowseek_categories");
    let selectedModifiers = readJsonStorage("shadowseek_modifiers");
    let overlayController = null;
    let isSubmitting = false;

    if (!form) {
        return;
    }

    const fieldNames = ["username", "real_name", "clan_name", "age", "postal_code"];
    const platformGrid = form?.querySelector(".platform-grid");
    const platformCheckboxes = () => Array.from(form.querySelectorAll('input[name="platforms"]'));

    const ensureHiddenField = (name) => {
        let input = form.querySelector(`input[type="hidden"][name="${name}"]`);
        if (!input) {
            input = document.createElement("input");
            input.type = "hidden";
            input.name = name;
            form.appendChild(input);
        }
        return input;
    };

    const syncModifierFields = () => {
        // These fields are consumed by the backend to enable optional features.
        const modifierToField = {
            public_sources: "public_sources",
            ai_rerank: "ai_rerank",
            secure_mode: "secure_mode",
            precision_mode: "precision_mode",
        };

        Object.values(modifierToField).forEach((field) => ensureHiddenField(field));

        Object.entries(modifierToField).forEach(([modifier, field]) => {
            const input = ensureHiddenField(field);
            input.value = selectedModifiers.includes(modifier) ? "true" : "";
        });
    };

    const renderPlatformTiles = (platforms) => {
        if (!platformGrid) {
            return;
        }

        platformGrid.innerHTML = "";
        platforms.forEach((platform) => {
            const tile = document.createElement("label");
            tile.className = "platform-tile";
            tile.innerHTML = `
                <input type="checkbox" name="platforms" value="${escapeHtml(platform.slug)}" checked data-platform="${escapeHtml(platform.slug)}">
                <span>${escapeHtml(platform.name)}</span>
            `;
            platformGrid.appendChild(tile);
        });
    };

    const loadPlatforms = async () => {
        try {
            const response = await fetch("/platforms", { credentials: "same-origin" });
            if (!response.ok) {
                return;
            }
            const payload = await response.json();
            if (!Array.isArray(payload) || payload.length === 0) {
                return;
            }
            renderPlatformTiles(payload);
        } catch {
            // Keep server-rendered fallback tiles.
        }
    };

    const renderCategoryChips = () => {
        if (!categoryBar) {
            return;
        }

        categoryBar.innerHTML = "";
        CATEGORIES.forEach((category) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = `category-chip-search${selectedCategories.includes(category.value) ? " active" : ""}`;
            button.textContent = category.label;
            button.addEventListener("click", () => {
                if (selectedCategories.includes(category.value)) {
                    selectedCategories = selectedCategories.filter((value) => value !== category.value);
                } else {
                    selectedCategories = [...selectedCategories, category.value];
                }
                writeJsonStorage("shadowseek_categories", selectedCategories);
                renderCategoryChips();
            });
            categoryBar.appendChild(button);
        });
    };

    const renderModifierChips = () => {
        if (!modifierBar) {
            return;
        }

        Array.from(modifierBar.querySelectorAll("[data-mod]")).forEach((button) => {
            const value = button.dataset.mod;
            button.classList.toggle("active", selectedModifiers.includes(value));
            button.onclick = () => {
                if (selectedModifiers.includes(value)) {
                    selectedModifiers = selectedModifiers.filter((item) => item !== value);
                } else {
                    selectedModifiers = [...selectedModifiers, value];
                }
                if (value === "deepsearch" && deepSearchToggle) {
                    deepSearchToggle.checked = selectedModifiers.includes("deepsearch");
                }
                writeJsonStorage("shadowseek_modifiers", selectedModifiers);
                renderModifierChips();
                syncModifierFields();
            };
        });
    };

    const restoreInputs = () => {
        const stored = readJsonStorage(storageKey, {});
        const params = new URLSearchParams(window.location.search);

        if (params.get("categories")) {
            selectedCategories = params
                .get("categories")
                .split(",")
                .map((value) => value.trim())
                .filter(Boolean);
        }

        fieldNames.forEach((name) => {
            const element = form.elements[name];
            if (!element) {
                return;
            }
            const fromUrl = params.get(name) || (name === "username" ? params.get("query") : null);
            if (fromUrl) {
                element.value = fromUrl;
            } else if (stored[name] !== undefined) {
                element.value = stored[name];
            }
        });

        if (Array.isArray(stored.platforms)) {
            platformCheckboxes().forEach((checkbox) => {
                checkbox.checked = stored.platforms.includes(checkbox.value);
            });
        }

        if (typeof stored.deep_search === "boolean" && deepSearchToggle) {
            deepSearchToggle.checked = stored.deep_search;
        }

        MODIFIERS.forEach((modifier) => {
            if (params.get(modifier.value) === "true" && !selectedModifiers.includes(modifier.value)) {
                selectedModifiers = [...selectedModifiers, modifier.value];
            }
        });

        if (deepSearchToggle?.checked && !selectedModifiers.includes("deepsearch")) {
            selectedModifiers = [...selectedModifiers, "deepsearch"];
        }
    };

    // Ensure modifier fields exist before the first submit.
    syncModifierFields();

    const saveInputs = () => {
        const data = {};
        fieldNames.forEach((name) => {
            data[name] = form.elements[name]?.value || "";
        });
        data.platforms = platformCheckboxes().filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value);
        data.deep_search = Boolean(deepSearchToggle?.checked);
        writeJsonStorage(storageKey, data);
    };

    const resetState = () => {
        localStorage.removeItem(storageKey);
        localStorage.removeItem("shadowseek_categories");
        localStorage.removeItem("shadowseek_modifiers");

        form.reset();
        platformCheckboxes().forEach((checkbox) => {
            checkbox.checked = true;
        });

        selectedCategories = [];
        selectedModifiers = [];
        renderCategoryChips();
        renderModifierChips();

        if (messageBox) {
            messageBox.innerHTML = "";
        }
        if (reverseLinks) {
            reverseLinks.innerHTML = "";
        }
        if (resultsList) {
            resultsList.innerHTML = '<div class="empty-state">Noch keine Ergebnisse. Starte einen Scan.</div>';
        }
        resetAnalysisWidgets();
        window.history.replaceState({}, "", window.location.pathname);
    };

    await loadPlatforms();
    restoreInputs();
    renderCategoryChips();
    renderModifierChips();

    if (deepSearchToggle) {
        deepSearchToggle.addEventListener("change", () => {
            if (deepSearchToggle.checked && !selectedModifiers.includes("deepsearch")) {
                selectedModifiers = [...selectedModifiers, "deepsearch"];
            }
            if (!deepSearchToggle.checked) {
                selectedModifiers = selectedModifiers.filter((item) => item !== "deepsearch");
            }
            writeJsonStorage("shadowseek_modifiers", selectedModifiers);
            renderModifierChips();
            saveInputs();
        });
    }

    form.addEventListener("input", (event) => {
        if (event.target.name !== "image") {
            saveInputs();
        }
    });

    form.addEventListener("change", (event) => {
        if (event.target.name !== "image") {
            saveInputs();
        }
    });

    document.querySelectorAll(".tab-btn").forEach((button) => {
        button.addEventListener("click", () => {
            setActiveTab(button.dataset.tab);
        });
    });
    setActiveTab("social");

    if (resetButton) {
        resetButton.addEventListener("click", resetState);
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (isSubmitting) {
            return;
        }
        isSubmitting = true;

        const selectedPlatforms = platformCheckboxes()
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.parentElement?.innerText.trim() || checkbox.value);

        overlayController = showScanOverlay(selectedPlatforms, Boolean(deepSearchToggle?.checked));

        syncModifierFields();
        const formData = new FormData(form);
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), 15000);

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: formData,
                headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
                credentials: "same-origin",
                signal: controller.signal,
            });

            const contentType = response.headers.get("content-type") || "";
            const payload = contentType.includes("application/json")
                ? await response.json()
                : { error: "Unexpected server response." };

            if (!response.ok) {
                const errors = payload.errors
                    ? Object.values(payload.errors).join(" ")
                    : payload.error || "Suche fehlgeschlagen.";
                throw new Error(errors);
            }

            renderMessages(payload, messageBox);
            renderReverseImageLinks(payload.reverse_image_search, reverseLinks);
            renderProfiles(payload.profiles, resultsList);
            resetAnalysisWidgets();

            if (deepSearchToggle?.checked) {
                try {
                    const deepSearchPayload = await requestDeepSearchAnalysis(payload, csrfToken);
                    renderDeepSearchResponse(deepSearchPayload);
                } catch (deepSearchError) {
                    resetAnalysisWidgets();
                    appendMessage(
                        messageBox,
                        "pink",
                        deepSearchError.message || "DeepSearch fehlgeschlagen"
                    );
                }
            }

            const newUrl = new URL(window.location.href);
            selectedModifiers.forEach((modifier) => newUrl.searchParams.set(modifier, "true"));
            if (selectedCategories.length > 0) {
                newUrl.searchParams.set("categories", selectedCategories.join(","));
            }
            window.history.replaceState({}, "", newUrl.pathname + newUrl.search);

            setActiveTab(findPreferredTab(payload.profiles));
            saveInputs();
            overlayController.hide();
            overlayController = null;
        } catch (error) {
            resetAnalysisWidgets();
            if (messageBox) {
                messageBox.innerHTML = "";
                const message = error?.name === "AbortError"
                    ? "Zeitueberschreitung bei der Anfrage."
                    : error.message || "Suche fehlgeschlagen";
                messageBox.appendChild(createMessage("pink", message));
            }
            if (overlayController) {
                const overlayMessage = error?.name === "AbortError"
                    ? "Zeitueberschreitung bei der Anfrage."
                    : error.message || "Suche fehlgeschlagen"
                overlayController.error(overlayMessage);
                overlayController = null;
            }
        } finally {
            window.clearTimeout(timeoutId);
            isSubmitting = false;
        }
    });
});

window.renderScreenshotResults = renderScreenshotResults;
window.renderSimilarityResults = renderSimilarityResults;
window.renderImageSimilarity = renderImageSimilarity;
window.renderRiskScore = renderRiskScore;
window.renderDeepSearchResponse = renderDeepSearchResponse;

// Meta-Felder global speichern für renderProfiles
    window.lastSearchMeta = response?.meta || {};
    renderScreenshotResults(response.data.screenshots);
    renderSimilarityResults(response.data.similarity);
    renderImageSimilarity(response.data.image_similarity);
    renderRiskScore(response.data.risk_score);

// DeepSearch: AI-Ranking-Toggle Wert mitgeben
    const aiRerankToggle = document.getElementById('ai-rerank-toggle');
    if (aiRerankToggle && aiRerankToggle.checked) {
        searchPayload.ai_rerank = true;
    } else {
        delete searchPayload.ai_rerank;
    }
