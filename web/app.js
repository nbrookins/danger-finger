// app.js — page initialization, event wiring, profile rendering, auth flow.
// Depends on: api.js, viewer.js, params.js

(function () {
    var baseurl = "";
    var readUrl = window.__READ_URL__ || "";
    var renderUrl = window.__RENDER_URL__ || "";
    var cachedBundleBlob = null;
    var cachedBundleCfghash = null;
    var _authToken = null;
    var _authUser = null;
    var _authDisplay = null;
    var _wpAuthUrl = "";
    var _latestPreviewHash = null;
    var _latestRenderHash = null;
    var _latestJobId = null;
    var _lastRenderedCfghash = null;
    var _pollTimer = null;
    var _paramsLoaded = false;
    var _authSettled = false;
    var _restoredDraft = false;
    var _paramsDirty = false;
    var _initialRenderDone = false;
    var _appVersion = "";
    var _defaultCfghash = "";
    var DRAFT_KEY = "df_guest_draft";
    var DRAFT_TTL_MS = 10 * 60 * 1000;

    function isAuthenticated() { return !!_authToken; }
    function getUsername() { return _authUser || ""; }

    function _downloadName(suffix) {
        var v = _appVersion || "0";
        return "DangerFinger_v" + v + "_" + suffix + ".zip";
    }

    function setAuthState(token, nicename, displayName) {
        _authToken = token;
        _authUser = nicename;
        _authDisplay = displayName || nicename;
        Api.setAuthToken(token);
        Params.setUsername(nicename);
        try { sessionStorage.setItem("wp_jwt", token); } catch (e) {}
        try { sessionStorage.setItem("wp_user", nicename); } catch (e) {}
        try { sessionStorage.setItem("wp_display", displayName || nicename); } catch (e) {}
        updateAuthUI();
        updateProfilesUI();
    }

    function clearAuthState() {
        _authToken = null;
        _authUser = null;
        _authDisplay = null;
        Api.setAuthToken(null);
        Params.setUsername("");
        try { sessionStorage.removeItem("wp_jwt"); } catch (e) {}
        try { sessionStorage.removeItem("wp_user"); } catch (e) {}
        try { sessionStorage.removeItem("wp_display"); } catch (e) {}
        updateAuthUI();
        updateProfilesUI();
    }

    function loadStoredAuth() {
        try {
            var token = sessionStorage.getItem("wp_jwt");
            var user = sessionStorage.getItem("wp_user");
            var display = sessionStorage.getItem("wp_display");
            if (token && user) {
                _authToken = token;
                _authUser = user;
                _authDisplay = display || user;
                Api.setAuthToken(token);
                Params.setUsername(user);
            }
        } catch (e) {}
    }

    function updateAuthUI() {
        var loginBtn = document.getElementById("auth_login_btn");
        var logoutBtn = document.getElementById("auth_logout_btn");
        var userDisplay = document.getElementById("auth_user_display");
        if (!loginBtn) return;
        if (isAuthenticated()) {
            loginBtn.style.display = "none";
            logoutBtn.style.display = "";
            if (userDisplay) userDisplay.textContent = _authDisplay || _authUser || "";
        } else {
            loginBtn.style.display = "";
            logoutBtn.style.display = "none";
            if (userDisplay) userDisplay.textContent = "";
        }
    }

    function updateProfilesUI() {
        var container = document.getElementById("profiles");
        if (!container) return;
        if (!isAuthenticated()) {
            container.innerHTML = '<div class="text-muted small">Log in to view and manage saved configs.</div>';
        }
    }

    function buildLoginUrl() {
        var base = _wpAuthUrl || "https://dangercreations.com";
        var appUrl = window.location.origin + window.location.pathname;
        var successUrl = appUrl + "?jwt_auth=1";
        return base.replace(/\/$/, "") + "/wp-admin/authorize-application.php?"
            + "app_name=DangerFinger"
            + "&app_id=dangerfinger-configurator"
            + "&success_url=" + encodeURIComponent(successUrl)
            + "&reject_url=" + encodeURIComponent(appUrl);
    }

    function saveDraftState(intent) {
        var state = {
            params: Params.getCurrentParams(),
            configName: Params.getConfigName(),
            latestPreviewHash: _latestPreviewHash,
            latestRenderHash: _latestRenderHash,
            latestJobId: _latestJobId,
            pendingAction: intent || null,
            savedAt: Date.now(),
        };
        try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify(state)); } catch (e) {}
    }

    function loadDraftState() {
        try {
            var raw = sessionStorage.getItem(DRAFT_KEY);
            if (!raw) return null;
            var state = JSON.parse(raw);
            if (!state.savedAt || (Date.now() - state.savedAt) > DRAFT_TTL_MS) {
                sessionStorage.removeItem(DRAFT_KEY);
                return null;
            }
            return state;
        } catch (e) {
            return null;
        }
    }

    function clearDraftState() {
        try { sessionStorage.removeItem(DRAFT_KEY); } catch (e) {}
    }

    function startLoginFlow(intent) {
        saveDraftState(intent || null);
        window.location.href = buildLoginUrl();
    }

    function initLoginLogout() {
        var loginBtn = document.getElementById("auth_login_btn");
        var logoutBtn = document.getElementById("auth_logout_btn");
        if (loginBtn) loginBtn.onclick = function () { startLoginFlow(null); };
        if (logoutBtn) {
            logoutBtn.onclick = function () {
                clearAuthState();
                updateProfilesUI();
            };
        }
        updateAuthUI();
    }

    function handleAuthCallback(onDone) {
        var params = new URLSearchParams(window.location.search);
        if (params.get("jwt_auth") !== "1") {
            onDone(false);
            return;
        }
        var userLogin = params.get("user_login");
        var appPassword = params.get("password");
        history.replaceState(null, "", window.location.pathname);
        if (!userLogin || !appPassword) {
            onDone(false);
            return;
        }
        setPreviewStatus("Signing in...", false);
        var wpBase = _wpAuthUrl || params.get("site_url") || "https://dangercreations.com";
        Api.fetchWpJwt(wpBase, userLogin, appPassword, function (data) {
            setAuthState(data.token, data.user_nicename, data.user_display_name);
            setPreviewStatus("Signed in as " + (_authDisplay || _authUser || ""), false);
            onDone(true);
        }, function (err) {
            setPreviewStatus("Sign-in failed: " + err, true);
            onDone(false);
        });
    }

    var parts = {
        0: { name: "base", pos: [0, -3, 0], exp: [0, -0.5, 0] },
        1: { name: "middle", pos: [1, 12, 0], exp: [0, 0, 0] },
        2: { name: "tip", pos: [1, 26, 0], exp: [0, 1, 0] },
        3: { name: "linkage", pos: [0, 0, 20], exp: [0, 0, 1] },
        4: { name: "tipcover", pos: [0, 39, 0], exp: [0, 1.5, 0] },
        5: { name: "socket", pos: [0, -25, 0], exp: [0, -1, 0] },
        6: { name: "plug", pos: [0, 0, 0], exp: [0, 0, 0] },
        7: { name: "stand", pos: [0, -30, 0], exp: [0, -1.5, 0] },
        8: { name: "bumper", pos: [1, 12, 0], exp: [1, 0, 0] }
    };
    var partNameToId = {};
    Object.keys(parts).forEach(function (id) { partNameToId[parts[id].name] = parseInt(id, 10); });

    function setPreviewStatus(msg, isError) {
        var el = document.getElementById("preview_status");
        if (!el) return;
        el.textContent = msg || "";
        el.className = "small mb-1 " + (isError ? "text-danger" : "text-muted");
    }

    function showRenderOverlay(show) {
        var overlay = document.getElementById("render_overlay");
        if (overlay) overlay.style.display = show ? "" : "none";
    }

    function showRenderProgress(show) {
        var el = document.getElementById("render_progress_overlay");
        if (el) el.style.display = show ? "" : "none";
    }

    function onParamsDirty() {
        _paramsDirty = true;
        if (_initialRenderDone) showRenderOverlay(true);
    }

    function triggerRender(quality) {
        _paramsDirty = false;
        showRenderOverlay(false);
        showRenderProgress(true);
        Api.requestPreview(Params.getCurrentParams(), quality || "default");
    }

    function onPartsLoaded(json) {
        if (json.wpAuthUrl) _wpAuthUrl = json.wpAuthUrl;
        if (json.version) _appVersion = json.version;
        if (json.defaultCfghash) _defaultCfghash = json.defaultCfghash;
        if (json.version) {
            var title = "DangerFinger v" + json.version + " - Configure and Preview";
            document.title = title;
            var h1 = document.querySelector("h1");
            if (h1) {
                h1.textContent = title;
                if (json.build) {
                    var badge = document.createElement("span");
                    badge.textContent = json.build;
                    badge.title = "Server build: git commit and date";
                    badge.style.cssText = "font-size:0.55em;font-weight:400;color:#aaa;margin-left:0.75em;font-family:monospace;vertical-align:middle;";
                    h1.appendChild(badge);
                }
            }
        }
        if (json.parts) Params.buildPartToggles(json.parts);
        Viewer.applyPreviewConfig(json, Params.getPartVisibility());
    }

    var DEFAULT_STL_PARTS = ["base", "middle", "tip", "linkage", "tipcover", "socket", "plug", "stand", "bumper"];

    function loadDefaultStls() {
        var stlUrls = {};
        DEFAULT_STL_PARTS.forEach(function (name) {
            stlUrls[name] = "/defaults/" + name + ".stl";
        });
        Viewer.updateFromStlUrls(stlUrls, Params.getPartVisibility());
        _initialRenderDone = true;
        _paramsDirty = false;
        setPreviewStatus("", false);
        showDefaultDownloadButton();
    }

    function showDefaultDownloadButton() {
        var btn = document.getElementById("download_btn");
        if (!btn) return;
        var hash8 = _defaultCfghash ? _defaultCfghash.substring(0, 8) : "default";
        var fname = _downloadName(hash8);
        btn.href = "/defaults/" + fname;
        btn.download = fname;
        btn.style.display = "";
    }

    function maybeRestoreDraft() {
        if (_restoredDraft || !_paramsLoaded || !_authSettled) return;
        _restoredDraft = true;
        if (restoreFromHash()) {
            triggerRender();
            return;
        }
        var state = loadDraftState();
        if (!state) {
            loadDefaultStls();
            return;
        }
        if (state.params) Params.applyLoadedConfig(state.params);
        if (state.configName) Params.setConfigName(state.configName);
        _latestPreviewHash = state.latestPreviewHash || null;
        _latestRenderHash = state.latestRenderHash || null;
        _latestJobId = state.latestJobId || null;
        triggerRender();
        if (state.pendingAction === "save" && isAuthenticated()) {
            window.setTimeout(function () {
                handleSaveRequested({
                    username: getUsername(),
                    configName: Params.getConfigName(),
                    params: Params.getCurrentParams()
                });
            }, 50);
        }
    }

    function onParamsLoaded(json) {
        Params.fillParams(json);
        _paramsLoaded = true;
        maybeRestoreDraft();
    }

    function onProfilesLoaded(json) { fillProfiles(json); }

    function onPreviewReady(res) {
        showRenderProgress(false);
        if (res.previewConfig) Viewer.applyPreviewConfig(res, Params.getPartVisibility());
        Viewer.updateFromStlUrls(res.stl_urls, Params.getPartVisibility());
        _latestPreviewHash = res.cfghash || null;
        _lastRenderedCfghash = res.cfghash || null;
        _initialRenderDone = true;
        saveDraftState(loadDraftState() && loadDraftState().pendingAction ? loadDraftState().pendingAction : null);
        var qualityLabel = (res.quality === "high") ? "high" : "default";
        setPreviewStatus("Render complete (" + qualityLabel + " quality).", false);
        showRenderOverlay(false);
        if (res.quality === "high" && res.cfghash) {
            showDownloadButton(res.cfghash);
        }
    }

    function onPreviewError(msg, isError) {
        if (isError) showRenderProgress(false);
        setPreviewStatus(msg, isError);
    }

    function onPartToggle(partName, visible) {
        var id = partNameToId[partName];
        if (id === undefined) return;
        if (partName === "plug") {
            Viewer.setPlugVisibility(visible, Params.getPartVisibility());
            return;
        }
        var lastUrls = Viewer.getLastStlUrls();
        if (visible) {
            var url = lastUrls[partName];
            if (url) Viewer.addModel(id, url);
        } else {
            Viewer.remModels([id]);
        }
    }

    function updateRenderStatusUi(payload) {
        if (!payload) return;
        if (payload.cfghash) _latestRenderHash = payload.cfghash;
        if (payload.job_id) _latestJobId = payload.job_id;
        if (payload.status_message) setPreviewStatus(payload.status_message, payload.status === "failed");
        if (payload.status === "complete" && payload.cfghash) {
            _lastRenderedCfghash = payload.cfghash;
            Params.setButtonsDisabled(false);
            Params.setRenderDisabled(true);
            Params.setRenderButtonLabel("Rendered");
            showDownloadButton(payload.cfghash);
            clearDraftState();
            if (isAuthenticated()) Api.fetchProfiles(getUsername());
            stopPolling();
        } else if (payload.status === "running") {
            Params.setButtonsDisabled(false);
            Params.setRenderDisabled(true);
            Params.setRenderButtonLabel("Rendering...");
        } else if (payload.status === "queued") {
            Params.setButtonsDisabled(false);
            Params.setRenderDisabled(true);
            Params.setRenderButtonLabel("Queued...");
        } else if (payload.status === "failed") {
            Params.setButtonsDisabled(false);
            Params.setRenderDisabled(false);
            Params.setRenderButtonLabel("Render");
        }
    }

    function stopPolling() {
        if (_pollTimer) {
            clearTimeout(_pollTimer);
            _pollTimer = null;
        }
    }

    function schedulePoll() {
        stopPolling();
        _pollTimer = setTimeout(pollRenderStatus, 3000);
    }

    function pollRenderStatus() {
        if (_latestJobId) {
            Api.fetchJobStatus(_latestJobId, function (payload) {
                updateRenderStatusUi(payload);
                if (payload.status === "queued" || payload.status === "running") schedulePoll();
            }, function (err) {
                setPreviewStatus(err || "Failed to check render status.", true);
                Params.setButtonsDisabled(false);
            });
            return;
        }
        if (_latestRenderHash) {
            Api.fetchRenderStatus(_latestRenderHash, function (payload) {
                updateRenderStatusUi(payload);
                if (payload.status === "queued" || payload.status === "running") schedulePoll();
            }, function (err) {
                setPreviewStatus(err || "Failed to check render status.", true);
                Params.setButtonsDisabled(false);
            });
        }
    }

    function handleRenderRequested(payload) {
        Params.setButtonsDisabled(true);
        Params.setRenderButtonLabel("Submitting...");
        saveDraftState(null);
        Api.renderConfig(payload.params, function (res) {
            updateRenderStatusUi(res);
            if (res.status === "queued" || res.status === "running") schedulePoll();
        }, function (err) {
            Params.setButtonsDisabled(false);
            Params.setRenderButtonLabel("Render");
            setPreviewStatus("Render failed: " + err, true);
        });
    }

    function handleSaveRequested(payload) {
        if (!isAuthenticated()) {
            setPreviewStatus("Log in to save this configuration to your profile.", false);
            saveDraftState("save");
            startLoginFlow("save");
            return;
        }
        Params.setButtonsDisabled(true);
        Api.saveConfig(getUsername(), payload.configName, payload.params, function (res) {
            Params.setButtonsDisabled(false);
            Params.clearDirty();
            clearDraftState();
            setPreviewStatus('Saved as "' + payload.configName + '".', false);
            if (res && res.render_status) {
                updateRenderStatusUi(res.render_status);
                if (res.render_status.status === "queued" || res.render_status.status === "running") schedulePoll();
            }
            Api.fetchProfiles(getUsername());
        }, function (err) {
            Params.setButtonsDisabled(false);
            setPreviewStatus("Save failed: " + err, true);
        });
    }

    function showDownloadButton(cfghash) {
        var btn = document.getElementById("download_btn");
        if (!btn) return;
        if (cachedBundleBlob && cachedBundleCfghash === cfghash) btn.href = URL.createObjectURL(cachedBundleBlob);
        else btn.href = Api.getBundleUrl(cfghash);
        btn.download = _downloadName(cfghash.substring(0, 8));
        btn.style.display = "";
    }

    function hideDownloadButton() {
        var btn = document.getElementById("download_btn");
        if (btn) btn.style.display = "none";
    }

    function fillProfiles(json) {
        var configs = json["configs"] || {};
        var container = document.getElementById("profiles");
        if (!container) return;
        var table = document.createElement("table");
        table.className = "table table-sm table-bordered mb-0";
        table.innerHTML = "<thead class='thead-light'><tr><th>#</th><th>Name</th><th>Status</th><th>Load</th><th>Download</th><th>Remove</th></tr></thead>";
        var tbody = document.createElement("tbody");
        var rowNum = 0;
        for (var cfgName in configs) {
            if (!configs.hasOwnProperty(cfgName)) continue;
            var entry = configs[cfgName];
            var cfghash = (typeof entry === "string") ? entry : entry.cfghash;
            if (!cfghash) continue;
            var tr = tbody.insertRow(-1);
            tr.insertCell(-1).textContent = ++rowNum;
            tr.insertCell(-1).textContent = cfgName;
            var statusCell = tr.insertCell(-1);
            statusCell.id = "profile_status_" + cfghash.substring(0, 8);
            statusCell.innerHTML = '<span class="text-muted small">Checking...</span>';
            _checkProfileStatus(cfghash, statusCell);
            var loadBtn = document.createElement("button");
            loadBtn.type = "button";
            loadBtn.className = "btn btn-sm btn-outline-primary";
            loadBtn.textContent = "Load";
            loadBtn.onclick = (function (name, hash) { return function () { loadConfig(name, hash); }; })(cfgName, cfghash);
            tr.insertCell(-1).appendChild(loadBtn);
            var dlCell = tr.insertCell(-1);
            dlCell.id = "profile_dl_" + cfghash.substring(0, 8);
            var dlLink = document.createElement("a");
            dlLink.href = Api.getBundleUrl(cfghash);
            dlLink.className = "btn btn-sm btn-outline-success";
            dlLink.textContent = "Download";
            dlLink.download = _downloadName(cfghash.substring(0, 8));
            dlCell.appendChild(dlLink);
            var delBtn = document.createElement("button");
            delBtn.type = "button";
            delBtn.className = "btn btn-sm btn-outline-secondary";
            delBtn.textContent = "Remove";
            delBtn.onclick = (function (name) {
                return function () {
                    if (!confirm('Remove saved config "' + name + '"?')) return;
                    Api.deleteConfig(getUsername(), name, function () {
                        Api.fetchProfiles(getUsername());
                    }, function (err) {
                        setPreviewStatus(err || "Delete failed.", true);
                    });
                };
            })(cfgName);
            tr.insertCell(-1).appendChild(delBtn);
        }
        table.appendChild(tbody);
        container.innerHTML = "";
        container.appendChild(table);
    }

    function _checkProfileStatus(cfghash, statusCell) {
        Api.fetchRenderStatus(cfghash, function (payload) {
            if (payload.status === "complete") {
                statusCell.innerHTML = '<span class="badge badge-success">Ready</span>';
            } else if (payload.status === "running" || payload.status === "queued") {
                statusCell.innerHTML = '<span class="badge badge-warning">' + (payload.status === "running" ? "Rendering..." : "Queued...") + '</span>';
                setTimeout(function () { _checkProfileStatus(cfghash, statusCell); }, 5000);
            } else {
                statusCell.innerHTML = '<span class="badge badge-secondary">Saved</span>';
            }
        }, function () {
            statusCell.innerHTML = '<span class="badge badge-secondary">Saved</span>';
        });
    }

    function loadConfig(cfgName, cfghash) {
        setPreviewStatus("Loading config...", false);
        Api.fetchConfig(cfghash, function (config) {
            Params.applyLoadedConfig(config);
            Params.setConfigName(cfgName);
            loadBundleZip(cfghash);
        });
    }

    function loadBundleZip(cfghash) {
        setPreviewStatus("Loading model files...", false);
        Api.fetchBundleZip(cfghash, function (arrayBuffer) {
            var blob = new Blob([arrayBuffer], { type: "application/zip" });
            cachedBundleBlob = blob;
            cachedBundleCfghash = cfghash;
            JSZip.loadAsync(arrayBuffer).then(function (zip) {
                var stlUrls = {};
                var promises = [];
                zip.forEach(function (path, entry) {
                    if (!path.endsWith(".stl")) return;
                    var partName = path.replace(".stl", "");
                    promises.push(entry.async("arraybuffer").then(function (buf) {
                        var stlBlob = new Blob([buf], { type: "application/octet-stream" });
                        stlUrls[partName] = URL.createObjectURL(stlBlob);
                    }));
                });
                Promise.all(promises).then(function () {
                    Viewer.updateFromStlUrls(stlUrls, Params.getPartVisibility(), true);
                    showDownloadButton(cfghash);
                    _lastRenderedCfghash = cfghash;
                    _initialRenderDone = true;
                    setPreviewStatus("Model loaded (print quality).", false);
                });
            }).catch(function (err) {
                console.error("JSZip extract failed:", err);
                setPreviewStatus("Failed to extract model files", true);
            });
        }, function (errMsg) {
            setPreviewStatus(errMsg, true);
        });
    }

    function doResize() {
        var height = isNaN(window.innerHeight) ? window.clientHeight : window.innerHeight;
        var cont = document.getElementById("stl_cont");
        if (cont) cont.style.height = height * 0.4 + "px";
    }

    function isInIframe() {
        try { return window.self !== window.top; } catch (e) { return true; }
    }

    function launchFullPage() {
        var state = { params: Params.getCurrentParams(), configName: Params.getConfigName() };
        var hash = "#config=" + encodeURIComponent(JSON.stringify(state));
        var url = window.location.origin + window.location.pathname + hash;
        window.open(url, "_blank");
    }

    function copyShareLink() {
        var state = { params: Params.getCurrentParams(), configName: Params.getConfigName() };
        var hash = "#config=" + encodeURIComponent(JSON.stringify(state));
        var url = window.location.origin + window.location.pathname + hash;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(url).then(function () { _showShareTooltip("Copied!"); });
        } else {
            var ta = document.createElement("textarea");
            ta.value = url;
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            _showShareTooltip("Copied!");
        }
    }

    function _showShareTooltip(msg) {
        var btn = document.getElementById("share_btn");
        if (!btn) return;
        var orig = btn.textContent;
        btn.textContent = msg;
        setTimeout(function () { btn.textContent = orig; }, 1500);
    }

    function restoreFromHash() {
        var hash = window.location.hash;
        if (!hash || !hash.startsWith("#config=")) return false;
        try {
            var json = decodeURIComponent(hash.substring(8));
            var state = JSON.parse(json);
            if (state.params) Params.applyLoadedConfig(state.params);
            if (state.configName) Params.setConfigName(state.configName);
            history.replaceState(null, "", window.location.pathname + window.location.search);
            return true;
        } catch (e) {
            console.error("Failed to restore from hash:", e);
            return false;
        }
    }

    window.addEventListener("load", function () {
        doResize();
        loadStoredAuth();
        initLoginLogout();
        updateProfilesUI();
        hideDownloadButton();

        if (isInIframe()) {
            var fpBtn = document.getElementById("fullpage_btn");
            if (fpBtn) { fpBtn.style.display = ""; fpBtn.onclick = launchFullPage; }
        }
        var shareBtn = document.getElementById("share_btn");
        if (shareBtn) shareBtn.onclick = copyShareLink;

        var viewerRenderBtn = document.getElementById("viewer_render_btn");
        if (viewerRenderBtn) viewerRenderBtn.onclick = triggerRender;

        Api.init({
            baseurl: baseurl,
            readUrl: readUrl,
            renderUrl: renderUrl,
            onPartsLoaded: onPartsLoaded,
            onParamsLoaded: onParamsLoaded,
            onProfilesLoaded: onProfilesLoaded,
            onPreviewReady: onPreviewReady,
            onPreviewError: onPreviewError,
        });

        Viewer.init({ baseurl: baseurl, onStatus: setPreviewStatus });
        Viewer.setPartData(parts, partNameToId);
        Viewer.initResizeHandle();

        Params.init({
            username: getUsername(),
            onParamsDirty: onParamsDirty,
            onPartToggle: onPartToggle,
            onSaveRequested: handleSaveRequested,
            onRenderRequested: handleRenderRequested,
            onHighQualityRequested: function() { triggerRender("high"); },
            onStatus: setPreviewStatus,
        });

        Api.fetchParts();
        Api.fetchParams();

        var isAuthRedirect = new URLSearchParams(window.location.search).get("jwt_auth") === "1";
        handleAuthCallback(function () {
            _authSettled = true;
            maybeRestoreDraft();
            if (isAuthenticated()) Api.fetchProfiles(getUsername());
        });

        if (!isAuthRedirect) {
            _authSettled = true;
            maybeRestoreDraft();
            if (isAuthenticated()) Api.fetchProfiles(getUsername());
        }
    });

    window.slide_change = function () { Viewer.slideChange(); };
    window.flex_change = function () { Viewer.flexChange(); };
})();
