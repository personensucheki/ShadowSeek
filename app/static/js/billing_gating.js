function setLockedState(element, reason) {
    if (!element) {
        return;
    }

    element.classList.add("feature-locked");
    element.setAttribute("aria-disabled", "true");
    if ("disabled" in element) {
        element.disabled = true;
    }
    if (reason) {
        element.setAttribute("title", reason);
    }

    const nestedInputs = element.querySelectorAll("input, button, select, textarea");
    nestedInputs.forEach((nested) => {
        nested.disabled = true;
        nested.setAttribute("aria-disabled", "true");
        if (reason) {
            nested.setAttribute("title", reason);
        }
    });
}

function applyFeatureGating(entitlements) {
    if (!entitlements || !entitlements.billing_enabled) {
        return;
    }

    const lockedReason = "Upgrade noetig fuer dieses Feature";
    const lockedPlatformReason = "Upgrade noetig fuer diese Plattform";
    const features = Array.isArray(entitlements.features) ? entitlements.features : [];
    const has = (feature) => features.includes("full_access") || features.includes(feature);
    const hasAny = (featureList) => featureList.some((feature) => has(feature));

    document.querySelectorAll("[data-feature]").forEach((element) => {
        const feature = element.getAttribute("data-feature");
        if (!has(feature)) {
            const isNavbarItem = element.closest(".navbar-center") && element.tagName === "A";
            if (isNavbarItem) {
                // Navbar-Links nicht verschwinden lassen -> deaktivieren + auf Billing lenken.
                setLockedState(element, lockedReason);
                element.setAttribute("href", "/billing");
            } else {
                setLockedState(element, lockedReason);
            }
        }
    });

    document.querySelectorAll("[data-any-feature]").forEach((element) => {
        const raw = element.getAttribute("data-any-feature") || "";
        const list = raw
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);
        if (!list.length) {
            return;
        }
        if (!hasAny(list)) {
            const isNavbarItem = element.closest(".navbar-center") && element.tagName === "A";
            if (isNavbarItem) {
                setLockedState(element, lockedReason);
                element.setAttribute("href", "/billing");
            } else {
                setLockedState(element, lockedReason);
            }
        }
    });

    document.querySelectorAll("[data-platform]").forEach((element) => {
        const platform = element.getAttribute("data-platform");
        if (!Array.isArray(entitlements.enabled_platforms) || !entitlements.enabled_platforms.includes(platform)) {
            const tile = element.closest(".platform-tile") || element;
            setLockedState(tile, lockedPlatformReason);
        }
    });
}

async function bootstrapBillingGating() {
    if (!window.SHADOWSEEK_BILLING_ENABLED) {
        return;
    }

    try {
        const response = await fetch("/api/entitlements/current", {
            credentials: "same-origin",
        });
        const payload = await response.json();
        if (!response.ok || !payload.entitlements) {
            return;
        }
        applyFeatureGating(payload.entitlements);
    } catch {
        // Keep UI usable if the entitlement probe fails.
    }
}

document.addEventListener("DOMContentLoaded", bootstrapBillingGating);
