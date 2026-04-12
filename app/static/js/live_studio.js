(function () {
    "use strict";

    const bootstrap = window.LIVE_STUDIO_BOOTSTRAP || {};
    const categories = Array.isArray(bootstrap.categories) ? bootstrap.categories : [];

    const sheetAliasMap = {
        hint: "utility",
        "co-stream": "utility",
        fanclub: "utility",
        promote: "utility",
        transfer: "utility",
        "share-camera": "utility"
    };

    const utilitySheetTitles = {
        hint: "Hinweise",
        "co-stream": "Zusammen streamen",
        fanclub: "Fanclub",
        promote: "Werben",
        transfer: "Uebertragen",
        "share-camera": "Kamera teilen"
    };

    const state = {
        isCameraActive: false,
        isPreviewReady: false,
        cameraError: "",
        currentCameraFacing: "user",
        isMicActive: true,
        activeMode: "direct",
        activeSheet: null,
        isTitleEditing: false,
        liveTitle: "ShadowSeek Live Session",
        selectedCategory: categories[0] || "Games",
        selectedGiftGoal: "rose",
        settings: {
            optimize_stability: true,
            remove_noise: false,
            audience_control: false,
            live_gifts: true,
            gift_gallery: true,
            ai_content: false
        },
        pollDraft: {
            question: "",
            options: ["", ""]
        },
        contacts: ["Cain", "Franzi", "SEMIS", "Flowayne", "FrauHeissler", "Marius"],
        shareTargets: ["Link kopieren", "Telegram", "Messenger", "SMS", "Signal", "Teams"],
        isStartReady: false,
        isBusy: false,
        currentStreamId: null,
        stream: null,
        socket: null,
        viewerCount: 0,
        likeCount: 0,
        activityItems: [],
        liveStartedAt: null,
        toastVisible: true
    };

    const dom = {};
    let sheetOpenTrigger = null;

    function qs(selector) {
        return document.querySelector(selector);
    }

    function qsa(selector) {
        return Array.from(document.querySelectorAll(selector));
    }

    function initLiveStudio() {
        captureDomRefs();
        bindUI();
        initRenderData();
        renderSettingsRows();
        renderShareRows();
        renderGoalCards();
        renderPollOptionInputs();
        renderPollValidity();
        updateStartReadiness();
        renderState();
        initSocketLifecycle();
        initCamera();
        startLiveTicker();
    }

    function captureDomRefs() {
        dom.stageVideo = qs("#stage-video");
        dom.stageFallback = qs("#stage-fallback");
        dom.fallbackEnableCamera = qs("#fallback-enable-camera");
        dom.topClose = qs("#top-close");
        dom.hintToast = qs("#hint-toast");
        dom.hintToastClose = qs("#hint-toast-close");
        dom.titleInput = qs("#live-title-input");
        dom.editTitleBtn = qs("#edit-title-btn");
        dom.categoryPill = qs("#category-pill");
        dom.modeButtons = qsa("#mode-switch [data-mode]");
        dom.inlineFrontCamera = qs("#inline-front-camera");
        dom.inlineBackCamera = qs("#inline-back-camera");
        dom.inlineMicToggle = qs("#inline-mic-toggle");
        dom.obsCopyKey = qs("#obs-copy-key");
        dom.startLiveBtn = qs("#start-live-btn");
        dom.statusLine = qs("#studio-status-line");
        dom.sheetBackdrop = qs("#sheet-backdrop");
        dom.sheets = qsa(".sheet");
        dom.settingsList = qs("#settings-list");
        dom.shareContacts = qs("#share-contacts");
        dom.shareActions = qs("#share-actions");
        dom.pollForm = qs("#poll-form");
        dom.pollQuestion = qs("#poll-question");
        dom.pollOptionA = qs("#poll-option-a");
        dom.pollOptionB = qs("#poll-option-b");
        dom.pollExtraOptions = qs("#poll-extra-options");
        dom.pollAddOption = qs("#poll-add-option");
        dom.pollSaveBtn = qs("#poll-save-btn");
        dom.goalGrid = qs("#goal-grid");
        dom.saveGoalBtn = qs("#save-goal-btn");
        dom.addCameraBtn = qs("#add-camera-btn");
        dom.categorySearch = qs("#category-search");
        dom.categoryList = qs("#category-list");
        dom.utilityTitle = qs("#utility-sheet-title");
        dom.utilityText = qs("#utility-sheet-text");
        dom.statViews = qs("#stat-views");
        dom.statFollowers = qs("#stat-followers");
        dom.statDuration = qs("#stat-duration");
        dom.stageViewerCount = qs("#stage-viewer-count");
        dom.stageLikeCount = qs("#stage-like-count");
        dom.stageActivityFeed = qs("#stage-activity-feed");
        dom.stageReactionsLayer = qs("#stage-reactions-layer");
    }

    function initRenderData() {
        state.liveTitle = dom.titleInput && dom.titleInput.value ? dom.titleInput.value : state.liveTitle;
        if (dom.categoryPill) dom.categoryPill.textContent = state.selectedCategory;
    }

    function bindUI() {
        if (dom.fallbackEnableCamera) {
            dom.fallbackEnableCamera.addEventListener("click", function () {
                initCamera();
            });
        }

        if (dom.topClose) {
            dom.topClose.addEventListener("click", function () {
                if (state.activeSheet) {
                    closeSheet();
                    return;
                }
                disconnectSocket();
                stopCamera();
                window.location.href = "/";
            });
        }

        if (dom.hintToastClose) {
            dom.hintToastClose.addEventListener("click", function () {
                state.toastVisible = false;
                renderState();
            });
        }

        if (dom.titleInput) {
            dom.titleInput.addEventListener("input", function (event) {
                updateTitle(event.target.value || "");
            });
            dom.titleInput.addEventListener("focus", function () {
                state.isTitleEditing = true;
            });
            dom.titleInput.addEventListener("blur", function () {
                state.isTitleEditing = false;
            });
        }

        if (dom.editTitleBtn && dom.titleInput) {
            dom.editTitleBtn.addEventListener("click", function () {
                dom.titleInput.focus();
                dom.titleInput.select();
            });
        }

        dom.modeButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                setMode(button.getAttribute("data-mode"));
            });
        });

        if (dom.inlineFrontCamera) {
            dom.inlineFrontCamera.addEventListener("click", function () {
                switchCamera("user");
            });
        }

        if (dom.inlineBackCamera) {
            dom.inlineBackCamera.addEventListener("click", function () {
                switchCamera("environment");
            });
        }

        if (dom.inlineMicToggle) {
            dom.inlineMicToggle.addEventListener("click", function () {
                toggleMic();
            });
        }

        if (dom.obsCopyKey) {
            dom.obsCopyKey.addEventListener("click", function () {
                if (!bootstrap.streamKey) {
                    setStatus("Kein Stream-Key verfuegbar.");
                    return;
                }
                navigator.clipboard.writeText(bootstrap.streamKey).then(function () {
                    setStatus("Stream-Key kopiert.");
                }).catch(function () {
                    setStatus("Kopieren nicht moeglich.");
                });
            });
        }

        if (dom.startLiveBtn) {
            dom.startLiveBtn.addEventListener("click", function () {
                handleStartLive();
            });
        }

        document.addEventListener("click", function (event) {
            const sheetBtn = event.target.closest("[data-open-sheet]");
            if (sheetBtn) {
                openSheet(sheetBtn.getAttribute("data-open-sheet"), sheetBtn);
                return;
            }

            if (event.target.closest("[data-close-sheet]")) {
                closeSheet();
                return;
            }

            const toolAction = event.target.closest("[data-tool-action]");
            if (toolAction && toolAction.getAttribute("data-tool-action") === "switch-camera") {
                switchCamera();
            }
        });

        if (dom.sheetBackdrop) {
            dom.sheetBackdrop.addEventListener("click", function () {
                closeSheet();
            });
        }

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && state.activeSheet) {
                closeSheet();
            }
        });

        if (dom.pollQuestion) {
            dom.pollQuestion.addEventListener("input", function (event) {
                state.pollDraft.question = event.target.value;
                renderPollValidity();
            });
        }
        if (dom.pollOptionA) {
            dom.pollOptionA.addEventListener("input", function (event) {
                state.pollDraft.options[0] = event.target.value;
                renderPollValidity();
            });
        }
        if (dom.pollOptionB) {
            dom.pollOptionB.addEventListener("input", function (event) {
                state.pollDraft.options[1] = event.target.value;
                renderPollValidity();
            });
        }
        if (dom.pollAddOption) {
            dom.pollAddOption.addEventListener("click", function () {
                addPollOption();
            });
        }
        if (dom.pollForm) {
            dom.pollForm.addEventListener("submit", function (event) {
                event.preventDefault();
                savePoll();
            });
        }

        if (dom.saveGoalBtn) {
            dom.saveGoalBtn.addEventListener("click", function () {
                setStatus("Geschenkziel gespeichert: " + state.selectedGiftGoal);
                closeSheet();
            });
        }

        if (dom.addCameraBtn) {
            dom.addCameraBtn.addEventListener("click", function () {
                setStatus("Kamera-Slot vorbereitet.");
                closeSheet();
            });
        }

        if (dom.categoryList) {
            dom.categoryList.addEventListener("click", function (event) {
                const item = event.target.closest(".category-item");
                if (!item) return;
                state.selectedCategory = item.getAttribute("data-category-value");
                renderState();
                updateStartReadiness();
                closeSheet();
            });
        }

        if (dom.categorySearch) {
            dom.categorySearch.addEventListener("input", function (event) {
                const value = (event.target.value || "").trim().toLowerCase();
                qsa(".category-item").forEach(function (item) {
                    item.hidden = !item.textContent.toLowerCase().includes(value);
                });
            });
        }

        qsa("[data-goal-tab]").forEach(function (button) {
            button.addEventListener("click", function () {
                qsa("[data-goal-tab]").forEach(function (el) {
                    el.classList.toggle("is-active", el === button);
                });
            });
        });
    }

    function initSocketLifecycle() {
        window.addEventListener("beforeunload", function () {
            disconnectSocket();
        });
    }

    function initLiveSocket(streamId) {
        if (!streamId || typeof window.io !== "function") return;

        disconnectSocket();
        const socket = window.io("/live");
        state.socket = socket;

        socket.on("connect", function () {
            socket.emit("join_stream", { stream_id: String(streamId) });
            appendActivity("System", "Live room verbunden.", "system");
        });

        socket.on("disconnect", function () {
            appendActivity("System", "Verbindung unterbrochen.", "system");
        });

        socket.on("viewer_update", function (data) {
            const count = Number((data || {}).viewer_count || 0);
            state.viewerCount = Number.isFinite(count) ? count : 0;
            renderLiveCenterStats();
            renderStageStats();
        });

        socket.on("new_message", function (data) {
            const username = String((data || {}).username || "Guest");
            const message = String((data || {}).message || "").trim();
            if (!message) return;
            appendActivity(username, message, "message");
        });

        socket.on("new_like", function (data) {
            const likes = Number((data || {}).likes || state.likeCount + 1);
            state.likeCount = Number.isFinite(likes) ? likes : state.likeCount + 1;
            renderStageStats();
            spawnLikeBurst();
            appendActivity("Like", "Neue Reaktion im Stream", "like");
        });

        socket.on("new_gift", function (data) {
            const username = String((data || {}).username || "Anonymous");
            const giftType = String((data || {}).gift_type || "Gift");
            const amount = Number((data || {}).amount || 1);
            appendActivity(username, giftType + " x" + String(amount), "gift");
        });
    }

    function disconnectSocket() {
        if (!state.socket) return;
        try {
            if (state.currentStreamId) {
                state.socket.emit("leave_stream", { stream_id: String(state.currentStreamId) });
            }
            state.socket.disconnect();
        } catch (_error) {
            // intentional no-op
        }
        state.socket = null;
    }

    async function initCamera() {
        if (state.activeMode === "voice" || state.activeMode === "studio") {
            stopCamera();
            return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            state.cameraError = "Kamera API nicht verfuegbar.";
            state.isCameraActive = false;
            state.isPreviewReady = false;
            renderState();
            return;
        }

        state.isBusy = true;
        state.cameraError = "";
        renderState();
        try {
            stopCamera();
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: state.currentCameraFacing },
                audio: true
            });
            state.stream = stream;
            if (dom.stageVideo) dom.stageVideo.srcObject = stream;
            state.isCameraActive = true;
            state.isPreviewReady = true;
            state.stream.getAudioTracks().forEach(function (track) {
                track.enabled = state.isMicActive;
            });
            setStatus("Kamera aktiv.");
        } catch (error) {
            state.cameraError = (error && error.message) || "Kamera konnte nicht gestartet werden.";
            state.isCameraActive = false;
            state.isPreviewReady = false;
            setStatus("Kamerafehler: " + state.cameraError);
        } finally {
            state.isBusy = false;
            updateStartReadiness();
            renderState();
        }
    }

    function stopCamera() {
        if (state.stream) {
            state.stream.getTracks().forEach(function (track) {
                track.stop();
            });
        }
        state.stream = null;
        state.isCameraActive = false;
        state.isPreviewReady = false;
        if (dom.stageVideo) dom.stageVideo.srcObject = null;
        updateStartReadiness();
    }

    async function switchCamera(targetFacing) {
        if (targetFacing) {
            state.currentCameraFacing = targetFacing;
        } else {
            state.currentCameraFacing = state.currentCameraFacing === "user" ? "environment" : "user";
        }
        if (state.activeMode === "voice" || state.activeMode === "studio") {
            renderState();
            return;
        }
        await initCamera();
    }

    function toggleMic() {
        state.isMicActive = !state.isMicActive;
        if (state.stream) {
            state.stream.getAudioTracks().forEach(function (track) {
                track.enabled = state.isMicActive;
            });
        }
        updateStartReadiness();
        renderState();
    }

    function setMode(mode) {
        state.activeMode = mode || "direct";
        if (state.activeMode === "voice") {
            stopCamera();
            setStatus("Sprachchat aktiv.");
        } else if (state.activeMode === "studio") {
            stopCamera();
            setStatus("LIVE Studio aktiv. Nutze OBS/RTMP fuer Ingest.");
        } else {
            initCamera();
        }
        updateStartReadiness();
        renderState();
    }

    function openSheet(name, triggerElement) {
        const mappedName = sheetAliasMap[name] || name;
        state.activeSheet = mappedName;
        sheetOpenTrigger = triggerElement || document.activeElement;

        if (mappedName === "utility" && dom.utilityTitle && dom.utilityText) {
            dom.utilityTitle.textContent = utilitySheetTitles[name] || "Tool";
            dom.utilityText.textContent = "Dieses Modul ist vorbereitet und kann in der naechsten Phase erweitert werden.";
        }

        dom.sheets.forEach(function (sheet) {
            const visible = sheet.getAttribute("data-sheet") === mappedName;
            sheet.hidden = !visible;
            sheet.classList.toggle("is-open", visible);
        });
        if (dom.sheetBackdrop) dom.sheetBackdrop.hidden = false;
        document.body.classList.add("is-scroll-locked");
    }

    function closeSheet() {
        state.activeSheet = null;
        dom.sheets.forEach(function (sheet) {
            sheet.classList.remove("is-open");
            sheet.hidden = true;
        });
        if (dom.sheetBackdrop) dom.sheetBackdrop.hidden = true;
        document.body.classList.remove("is-scroll-locked");
        if (sheetOpenTrigger && sheetOpenTrigger.focus) sheetOpenTrigger.focus();
    }

    function updateTitle(value) {
        state.liveTitle = (value || "").trim() || "ShadowSeek Live Session";
        updateStartReadiness();
    }

    function addPollOption() {
        if (state.pollDraft.options.length >= 5) {
            setStatus("Maximal 5 Optionen moeglich.");
            return;
        }
        state.pollDraft.options.push("");
        renderPollOptionInputs();
        renderPollValidity();
    }

    function savePoll() {
        if (!isPollValid()) {
            setStatus("Abstimmung unvollstaendig.");
            return;
        }
        setStatus("Abstimmung gespeichert.");
        closeSheet();
    }

    function selectGiftGoal(id) {
        state.selectedGiftGoal = id;
        renderGoalCards();
    }

    async function handleStartLive() {
        if (!state.isStartReady || state.isBusy) return;
        state.isBusy = true;
        setStatus("Live-Session wird gestartet...");
        renderState();

        const payload = {
            title: state.liveTitle,
            description: "ShadowSeek Live Studio Session",
            category: state.selectedCategory,
            game: state.activeMode === "mobile" ? "mobile" : "",
            tags: ["shadowseek", "live", state.activeMode],
            allow_gifts: true
        };

        try {
            const response = await fetch("/api/live/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok || !result.success) throw new Error(result.error || "Start fehlgeschlagen");
            state.currentStreamId = result.stream_id;
            state.liveStartedAt = Date.now();
            initLiveSocket(state.currentStreamId);

            if (state.activeMode === "studio") {
                try {
                    const providerResponse = await fetch("/api/live/streams/" + String(result.stream_id) + "/start", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({})
                    });
                    const providerResult = await providerResponse.json().catch(function () { return {}; });
                    if (providerResponse.ok && providerResult.success) {
                        setStatus("LIVE Studio aktiv. Ingest bereit.");
                    } else {
                        setStatus("Stream angelegt. Provider aktuell nicht startbar.");
                    }
                } catch (_providerErr) {
                    setStatus("Stream angelegt. Provider aktuell nicht erreichbar.");
                }
            } else {
                setStatus("LIVE aktiv - Stream ID " + result.stream_id);
            }

            openSheet("live-center", dom.startLiveBtn);
        } catch (error) {
            setStatus("Live Start fehlgeschlagen: " + ((error && error.message) || "Unbekannt"));
        } finally {
            state.isBusy = false;
            renderState();
        }
    }

    function renderState() {
        if (dom.stageFallback) dom.stageFallback.hidden = state.isPreviewReady && !state.cameraError;
        if (dom.hintToast) dom.hintToast.hidden = !state.toastVisible;
        if (dom.categoryPill) dom.categoryPill.textContent = state.selectedCategory;

        if (dom.inlineFrontCamera) {
            dom.inlineFrontCamera.classList.toggle("is-active", state.currentCameraFacing === "user");
        }
        if (dom.inlineBackCamera) {
            dom.inlineBackCamera.classList.toggle("is-active", state.currentCameraFacing === "environment");
        }
        if (dom.inlineMicToggle) {
            dom.inlineMicToggle.classList.toggle("is-active", state.isMicActive);
            dom.inlineMicToggle.textContent = state.isMicActive ? "Mikro an" : "Mikro aus";
        }

        dom.modeButtons.forEach(function (button) {
            button.classList.toggle("is-active", button.getAttribute("data-mode") === state.activeMode);
        });

        if (dom.startLiveBtn) {
            dom.startLiveBtn.disabled = !state.isStartReady || state.isBusy;
            dom.startLiveBtn.textContent = state.isBusy ? "Starte LIVE..." : "LIVE starten";
        }

        if (!state.isBusy && !state.currentStreamId) {
            if (!state.isStartReady) {
                if (state.activeMode !== "voice" && state.activeMode !== "studio" && !state.isPreviewReady) {
                    setStatus("Kamera bereitstellen, um LIVE zu starten.");
                }
            }
        }

        renderLiveCenterStats();
        renderStageStats();
    }

    function renderLiveCenterStats() {
        if (dom.statViews) dom.statViews.textContent = String(state.viewerCount);
        if (dom.statFollowers) dom.statFollowers.textContent = state.currentStreamId ? "3" : "0";
        if (dom.statDuration) {
            if (!state.liveStartedAt) {
                dom.statDuration.textContent = "0";
            } else {
                const minutes = Math.max(1, Math.floor((Date.now() - state.liveStartedAt) / 60000));
                dom.statDuration.textContent = String(minutes);
            }
        }
    }

    function renderStageStats() {
        if (dom.stageViewerCount) dom.stageViewerCount.textContent = String(state.viewerCount);
        if (dom.stageLikeCount) dom.stageLikeCount.textContent = String(state.likeCount) + " Likes";
    }

    function appendActivity(author, text, type) {
        if (!dom.stageActivityFeed) return;
        const row = document.createElement("li");
        row.className = "stage-activity-item";
        if (type === "gift") row.classList.add("stage-activity-item--gift");
        if (type === "like") row.classList.add("stage-activity-item--like");
        row.innerHTML = "<strong>" + escapeHtml(author) + ":</strong> " + escapeHtml(text);

        dom.stageActivityFeed.prepend(row);
        while (dom.stageActivityFeed.children.length > 5) {
            dom.stageActivityFeed.removeChild(dom.stageActivityFeed.lastElementChild);
        }
    }

    function spawnLikeBurst() {
        if (!dom.stageReactionsLayer) return;
        const burst = document.createElement("span");
        burst.className = "stage-like-burst";
        burst.textContent = "❤";
        burst.style.right = String(8 + Math.round(Math.random() * 74)) + "px";
        burst.style.animationDuration = String(1100 + Math.round(Math.random() * 420)) + "ms";
        dom.stageReactionsLayer.appendChild(burst);
        window.setTimeout(function () {
            burst.remove();
        }, 1700);
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function updateStartReadiness() {
        const hasTitle = !!(state.liveTitle && state.liveTitle.length >= 3);
        const hasCategory = !!state.selectedCategory;
        const needsCamera = state.activeMode !== "voice" && state.activeMode !== "studio";
        const cameraReady = !needsCamera || (state.isCameraActive && state.isPreviewReady);
        state.isStartReady = hasTitle && hasCategory && cameraReady;
    }

    function renderSettingsRows() {
        if (!dom.settingsList) return;
        const items = [
            { key: "about", label: "Ueber mich", sub: "Stelle dich und dein LIVE vor.", type: "nav" },
            { key: "multi_guest", label: "Multi-Gast-LIVE", sub: "Personalisierte Funktionen rund um Gaeste.", type: "nav" },
            { key: "boards", label: "Boards", sub: "Ordnung fuer deine Studio-Werkzeuge.", type: "nav" },
            { key: "practice", label: "Uebungsmodus", sub: "Vorab-LIVE nur fuer dich sichtbar.", type: "nav" },
            { key: "viewer_visibility", label: "Wer dieses LIVE anschauen kann", sub: "Sichtbarkeit und Zielgruppe.", type: "nav" },
            { key: "mods", label: "Moderator*innen", sub: "Moderation fuer deinen Stream.", type: "nav" },
            { key: "marked_viewers", label: "Markierte Zuschauer*innen", sub: "Wichtige Accounts sichtbar halten.", type: "nav" },
            { key: "optimize_stability", label: "Optimieren fuer Stabilitaet", sub: "Reduziert Verzoegerungen und Stoerungen.", type: "toggle" },
            { key: "remove_noise", label: "Hintergrundgeraeusche entfernen", sub: "Verbessert die Verstaendlichkeit.", type: "toggle" },
            { key: "audience_control", label: "Publikumssteuerung", sub: "Interaktionsrechte regeln.", type: "toggle" },
            { key: "live_gifts", label: "LIVE-Geschenke", sub: "Geschenke waehrend LIVE erlauben.", type: "toggle" },
            { key: "gift_gallery", label: "Geschenkgalerie", sub: "Aktiviert Geschenk-Anzeige im Stream.", type: "toggle" },
            { key: "rankings", label: "Ranglisten", sub: "Top-Unterstuetzer sichtbar machen.", type: "nav" },
            { key: "comment_settings", label: "Kommentareinstellungen", sub: "Kommentarfluss kontrollieren.", type: "nav" },
            { key: "recordings", label: "LIVE-Aufnahmen", sub: "Replays, Highlights und Clips.", type: "nav" },
            { key: "disclosure", label: "Inhaltsoffenlegung", sub: "Kennzeichnung von Werbeinhalten.", type: "nav" },
            { key: "ai_content", label: "KI-generierter Inhalt", sub: "KI-Einsatz transparent kennzeichnen.", type: "toggle" },
            { key: "donation", label: "Spendenaktion hinzufuegen", sub: "Unterstuetzung fuer dein LIVE.", type: "nav" }
        ];

        dom.settingsList.innerHTML = "";
        items.forEach(function (item) {
            const row = document.createElement("article");
            row.className = "settings-row";
            const left = document.createElement("div");
            const title = document.createElement("h4");
            const text = document.createElement("p");
            title.textContent = item.label;
            text.textContent = item.sub;
            left.appendChild(title);
            left.appendChild(text);
            row.appendChild(left);

            if (item.type === "toggle") {
                const toggle = document.createElement("button");
                toggle.type = "button";
                toggle.className = "settings-toggle";
                toggle.classList.toggle("is-on", !!state.settings[item.key]);
                toggle.setAttribute("aria-label", item.label);
                toggle.addEventListener("click", function () {
                    state.settings[item.key] = !state.settings[item.key];
                    renderSettingsRows();
                });
                row.appendChild(toggle);
            } else {
                const arrow = document.createElement("button");
                arrow.type = "button";
                arrow.className = "icon-inline-btn";
                arrow.textContent = ">";
                arrow.setAttribute("aria-label", item.label + " oeffnen");
                row.appendChild(arrow);
            }
            dom.settingsList.appendChild(row);
        });
    }

    function renderShareRows() {
        if (dom.shareContacts) {
            dom.shareContacts.innerHTML = "";
            state.contacts.forEach(function (name) {
                const contact = document.createElement("button");
                contact.type = "button";
                contact.className = "share-contact";
                contact.textContent = name;
                dom.shareContacts.appendChild(contact);
            });
        }

        if (dom.shareActions) {
            dom.shareActions.innerHTML = "";
            state.shareTargets.forEach(function (target) {
                const action = document.createElement("button");
                action.type = "button";
                action.className = "share-action";
                action.textContent = target;
                action.addEventListener("click", function () {
                    if (target === "Link kopieren") {
                        navigator.clipboard.writeText(window.location.origin + "/live").then(function () {
                            setStatus("Live-Link kopiert.");
                        }).catch(function () {
                            setStatus("Link konnte nicht kopiert werden.");
                        });
                    } else {
                        setStatus("Share vorbereitet: " + target);
                    }
                });
                dom.shareActions.appendChild(action);
            });
        }
    }

    function renderPollOptionInputs() {
        if (!dom.pollExtraOptions) return;
        dom.pollExtraOptions.innerHTML = "";
        for (let index = 2; index < state.pollDraft.options.length; index += 1) {
            const input = document.createElement("input");
            input.maxLength = 50;
            input.placeholder = "Option " + String.fromCharCode(65 + index);
            input.value = state.pollDraft.options[index] || "";
            input.addEventListener("input", function (event) {
                state.pollDraft.options[index] = event.target.value;
                renderPollValidity();
            });
            dom.pollExtraOptions.appendChild(input);
        }
    }

    function isPollValid() {
        if (!state.pollDraft.question.trim()) return false;
        return state.pollDraft.options.filter(function (item) {
            return item.trim().length > 0;
        }).length >= 2;
    }

    function renderPollValidity() {
        if (dom.pollSaveBtn) dom.pollSaveBtn.disabled = !isPollValid();
    }

    function renderGoalCards() {
        if (!dom.goalGrid) return;
        const goals = [
            { id: "rose", title: "Rose x1", hint: "Schneller Einstieg fuer Support" },
            { id: "diamond", title: "Diamond x20", hint: "Mission fuer Reward-Boost" },
            { id: "super-fan", title: "Super Fan x3", hint: "Fanclub Fokus" },
            { id: "promote", title: "Promotion Ziel", hint: "Mehr Sichtbarkeit waehrend LIVE" }
        ];
        dom.goalGrid.innerHTML = "";
        goals.forEach(function (goal) {
            const card = document.createElement("button");
            card.type = "button";
            card.className = "goal-card";
            card.classList.toggle("is-selected", state.selectedGiftGoal === goal.id);
            card.innerHTML = "<strong>" + goal.title + "</strong><p>" + goal.hint + "</p>";
            card.addEventListener("click", function () {
                selectGiftGoal(goal.id);
            });
            dom.goalGrid.appendChild(card);
        });
    }

    function setStatus(message) {
        if (dom.statusLine) dom.statusLine.textContent = message || "";
    }

    function startLiveTicker() {
        window.setInterval(function () {
            if (state.currentStreamId) {
                renderLiveCenterStats();
                renderStageStats();
            }
        }, 4500);
    }

    window.initLiveStudio = initLiveStudio;
    window.addEventListener("DOMContentLoaded", initLiveStudio);
})();
