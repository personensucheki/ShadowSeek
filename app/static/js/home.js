document.addEventListener("DOMContentLoaded", () => {
    const csrfToken =
        document.querySelector("meta[name='csrf-token']")?.getAttribute("content") || "";
    const form = document.getElementById("search-form");
    const submitButton = document.getElementById("search-submit");
    const formErrors = document.getElementById("form-errors");
    const resultsPanel = document.getElementById("results-panel");
    const resultsStatus = document.getElementById("results-status");
    const resultsMeta = document.getElementById("results-meta");
    const variationList = document.getElementById("variation-list");
    const reverseImageCard = document.getElementById("reverse-image-card");
    const reverseImageLinks = document.getElementById("reverse-image-links");
    const profileResults = document.getElementById("profile-results");
    const platformTiles = Array.from(document.querySelectorAll(".platform-tile"));

    if (
        !form ||
        !submitButton ||
        !formErrors ||
        !resultsPanel ||
        !resultsStatus ||
        !resultsMeta ||
        !variationList ||
        !reverseImageCard ||
        !reverseImageLinks ||
        !profileResults
    ) {
        return;
    }

    const syncPlatformTiles = () => {
        platformTiles.forEach((tile) => {
            const checkbox = tile.querySelector("input[type='checkbox']");
            if (!checkbox) {
                return;
            }

            tile.classList.toggle("is-active", checkbox.checked);
        });
    };

    const setStatus = (message, state = "info") => {
        resultsStatus.textContent = message;
        resultsStatus.dataset.state = state;
    };

    const setLoadingState = (isLoading) => {
        submitButton.disabled = isLoading;
        submitButton.classList.toggle("is-loading", isLoading);
        submitButton.textContent = isLoading ? "Scan laeuft..." : "Scan starten";
        form.setAttribute("aria-busy", String(isLoading));

        if (isLoading) {
            setStatus("Plattformen werden geprueft...");
        }
    };

    const clearErrors = () => {
        formErrors.textContent = "";
    };

    const clearResults = () => {
        resultsMeta.innerHTML = "";
        variationList.innerHTML = "";
        reverseImageLinks.innerHTML = "";
        profileResults.innerHTML = "";
        reverseImageCard.hidden = true;
    };

    const renderErrors = (errors) => {
        const message = Object.values(errors || {}).join(" ");
        formErrors.textContent = message || "Die Anfrage konnte nicht verarbeitet werden.";
    };

    const renderMeta = (payload) => {
        resultsMeta.innerHTML = "";

        const badges = [
            `${payload.meta.profile_count} Treffer`,
            `${payload.meta.platform_count} Plattformen`,
            payload.query.deep_search ? "DeepSearch an" : "DeepSearch aus",
            payload.meta.ai_reranking_applied ? "AI reranked" : "AI aus",
            formatTimestamp(payload.meta.generated_at),
        ];

        badges.forEach((label) => {
            const badge = document.createElement("span");
            badge.className = "meta-badge";
            badge.textContent = label;
            resultsMeta.appendChild(badge);
        });
    };

    const renderVariations = (variations) => {
        variationList.innerHTML = "";

        variations.forEach((variation) => {
            const chip = document.createElement("span");
            chip.className = "variation-chip";
            chip.textContent = `${variation.username} | ${variation.score}`;
            chip.title = variation.reason;
            variationList.appendChild(chip);
        });
    };

    const renderReverseLinks = (links) => {
        reverseImageLinks.innerHTML = "";

        if (!links || !links.asset_url) {
            reverseImageCard.hidden = true;
            return;
        }

        reverseImageCard.hidden = false;

        [
            ["Google Lens", links.google_lens],
            ["TinEye", links.tineye],
            ["Yandex", links.yandex],
            ["Temporaere Bild-URL", links.asset_url],
        ].forEach(([label, href]) => {
            const anchor = document.createElement("a");
            anchor.href = href;
            anchor.target = "_blank";
            anchor.rel = "noopener noreferrer";
            anchor.textContent = label;
            reverseImageLinks.appendChild(anchor);
        });
    };

    const renderProfiles = (profiles) => {
        profileResults.innerHTML = "";

        if (!profiles.length) {
            const emptyState = document.createElement("div");
            emptyState.className = "empty-state";
            emptyState.textContent =
                "Keine bestaetigten Treffer gefunden. Versuche weitere Variationen oder aktiviere DeepSearch.";
            profileResults.appendChild(emptyState);
            return;
        }

        profiles.forEach((profile) => {
            const row = document.createElement("article");
            row.className = "profile-row";

            const content = document.createElement("div");
            const platform = document.createElement("p");
            platform.className = "profile-platform";
            platform.textContent = profile.platform;

            const title = document.createElement("h3");
            title.className = "profile-title";
            title.textContent = `${profile.username} | ${profile.verification}`;

            const subtitle = document.createElement("p");
            subtitle.className = "profile-subtitle";
            const statusLabel = profile.http_status === "SERP" ? "SERP" : `HTTP ${profile.http_status}`;
            subtitle.textContent = `${profile.match_reason} | Kategorie ${profile.category} | ${statusLabel}`;

            const detail = document.createElement("p");
            detail.className = "profile-subtitle";
            detail.textContent = profile.snippet || "Oeffentlicher Link-Kandidat";

            content.append(platform, title, subtitle, detail);

            const actions = document.createElement("div");
            actions.className = "profile-actions";

            const score = document.createElement("span");
            score.className = "profile-score";
            score.textContent = `${profile.match_score}%`;

            const link = document.createElement("a");
            link.className = "profile-link";
            link.href = profile.profile_url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = "Profil oeffnen";

            actions.append(score, link);
            row.append(content, actions);
            profileResults.appendChild(row);
        });
    };

    const renderResult = (payload) => {
        resultsPanel.hidden = false;
        setStatus(
            `${payload.meta.profile_count} Treffer fuer ${payload.query.username} wurden geladen.`,
            "success",
        );
        renderMeta(payload);
        renderVariations(payload.username_variations || []);
        // Backend liefert `reverse_image_search` (nicht `reverse_image_links`)
        renderReverseLinks(payload.reverse_image_search || {});
        renderProfiles(payload.profiles || []);
    };

    const submitSearch = async (event) => {
        event.preventDefault();
        clearErrors();
        clearResults();
        resultsPanel.hidden = false;
        setLoadingState(true);

        try {
            const response = await fetch(form.action || "/api/search", {
                method: "POST",
                headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
                body: new FormData(form),
            });
            const payload = await response.json().catch(() => ({}));

            if (!response.ok) {
                renderErrors(payload.errors || payload);
                setStatus("Die Suche konnte nicht abgeschlossen werden.", "error");
                return;
            }

            renderResult(payload);
            resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (error) {
            renderErrors({ request: "Die Plattformpruefung ist fehlgeschlagen." });
            setStatus("Die Plattformpruefung ist fehlgeschlagen.", "error");
        } finally {
            setLoadingState(false);
        }
    };

    platformTiles.forEach((tile) => {
        tile.addEventListener("change", syncPlatformTiles);
        tile.addEventListener("click", () => {
            window.requestAnimationFrame(syncPlatformTiles);
        });
    });

    form.addEventListener("submit", submitSearch);
    syncPlatformTiles();
    clearResults();
});

function formatTimestamp(value) {
    if (!value) {
        return "Jetzt";
    }

    const timestamp = new Date(value);
    if (Number.isNaN(timestamp.getTime())) {
        return "Jetzt";
    }

    return timestamp.toLocaleTimeString("de-DE", {
        hour: "2-digit",
        minute: "2-digit",
    });
}
