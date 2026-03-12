// app.js — page initialization, event wiring, profile rendering, auth flow.
// Depends on: api.js, viewer.js, params.js

(function () {
    var baseurl = "";
    var readUrl = window.__READ_URL__ || "";
    var renderUrl = window.__RENDER_URL__ || "";
    var cachedBundleBlob = null;
    var cachedBundleCfghash = null;

    // --- Auth state ---
    var _authToken = null;
    var _authUser = null;         // WP user_nicename — used as S3 profile key
    var _authDisplay = null;      // WP user_display_name — shown in UI
    var _wpAuthUrl = "";          // Populated from /api/parts response

    function isAuthenticated() { return !!_authToken; }
    function getUsername() { return _authUser || ""; }

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

    function initLoginLogout() {
        var loginBtn = document.getElementById("auth_login_btn");
        var logoutBtn = document.getElementById("auth_logout_btn");
        if (loginBtn) {
            loginBtn.onclick = function () {
                window.location.href = buildLoginUrl();
            };
        }
        if (logoutBtn) {
            logoutBtn.onclick = function () {
                clearAuthState();
                var profilesEl = document.getElementById("profiles");
                if (profilesEl) profilesEl.innerHTML = "";
            };
        }
        updateAuthUI();
    }

    // Handle the ?jwt_auth=1&user_login=...&password=... callback from WP.
    // Immediately cleans URL to prevent credentials in browser history.
    function handleAuthCallback(onDone) {
        var params = new URLSearchParams(window.location.search);
        if (params.get("jwt_auth") !== "1") {
            onDone(false);
            return;
        }
        var userLogin = params.get("user_login");
        var appPassword = params.get("password");

        // Remove all auth params from URL immediately
        history.replaceState(null, "", window.location.pathname);

        if (!userLogin || !appPassword) {
            onDone(false);
            return;
        }

        setPreviewStatus("Signing in\u2026");
        var wpBase = _wpAuthUrl || params.get("site_url") || "https://dangercreations.com";
        Api.fetchWpJwt(wpBase, userLogin, appPassword,
            function (data) {
                setAuthState(data.token, data.user_nicename, data.user_display_name);
                setPreviewStatus("Signed in as " + (_authDisplay || _authUser || ""));
                onDone(true);
            },
            function (err) {
                setPreviewStatus("Sign-in failed: " + err, true);
                onDone(false);
            }
        );
    }

    // Shared parts map: id -> {name, pos, exp}
    var parts = {
        0: { name: "base",     pos: [0, -3, 0],  exp: [0, -0.5, 0] },
        1: { name: "middle",   pos: [1, 12, 0],  exp: [0,  0,   0] },
        2: { name: "tip",      pos: [1, 26, 0],  exp: [0,  1,   0] },
        3: { name: "linkage",  pos: [0,  0, 20], exp: [0,  0,   1] },
        4: { name: "tipcover", pos: [0, 39, 0],  exp: [0,  1.5, 0] },
        5: { name: "socket",   pos: [0,-25, 0],  exp: [0, -1,   0] },
        6: { name: "plug",     pos: [0,  0, 0],  exp: [0,  0,   0] },
        7: { name: "stand",    pos: [0,-30, 0],  exp: [0, -1.5, 0] },
    };

    var partNameToId = {};
    Object.keys(parts).forEach(function (id) {
        partNameToId[parts[id].name] = parseInt(id);
    });

    function setPreviewStatus(msg, isError) {
        var el = document.getElementById("preview_status");
        if (!el) return;
        el.textContent = msg || "";
        el.className = "small mb-1 " + (isError ? "text-danger" : "text-muted");
    }

    function onPartsLoaded(json) {
        // Capture WP auth URL and app URL from server config
        if (json.wpAuthUrl) _wpAuthUrl = json.wpAuthUrl;

        // Update title and build badge
        if (json.version) {
            var title = "DangerFinger v" + json.version + " \u2013 Configure and Preview";
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
        // Build part toggles
        if (json.parts) {
            Params.buildPartToggles(json.parts);
        }
        // Apply preview config (positions, rotations, plug instances, explode offsets)
        Viewer.applyPreviewConfig(json, Params.getPartVisibility());
    }

    function onParamsLoaded(json) {
        Params.fillParams(json);
        Api.requestPreview(Params.getCurrentParams);
    }

    function onProfilesLoaded(json) {
        fillProfiles(json);
    }

    function onPreviewReady(res) {
        if (res.previewConfig) {
            Viewer.applyPreviewConfig(res, Params.getPartVisibility());
        }
        Viewer.updateFromStlUrls(res.stl_urls, Params.getPartVisibility());
        setPreviewStatus("Preview ready.");
    }

    function onPreviewError(msg, isError) {
        setPreviewStatus(msg, isError);
    }

    function onPartToggle(partName, visible) {
        var id = partNameToId[partName];
        if (id === undefined) return;
        // Plug is never added as a single centered model; setPlugVisibility owns all 4 instances.
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

    function onSaveSuccess(cfgName, res) {
        Api.fetchProfiles(getUsername());
        if (res && res.cfghash) showDownloadButton(res.cfghash);
    }

    function showDownloadButton(cfghash) {
        var btn = document.getElementById("download_btn");
        if (!btn) return;
        if (cachedBundleBlob && cachedBundleCfghash === cfghash) {
            btn.href = URL.createObjectURL(cachedBundleBlob);
        } else {
            btn.href = Api.getBundleUrl(cfghash);
        }
        btn.download = "danger_finger_" + cfghash.substring(0, 8) + ".zip";
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
        var thead = "<thead class='thead-light'><tr><th>#</th><th>Name</th><th>Load</th><th>Download</th><th>Remove</th></tr></thead>";
        table.innerHTML = thead;
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

            var loadBtn = document.createElement("button");
            loadBtn.type = "button";
            loadBtn.className = "btn btn-sm btn-outline-primary";
            loadBtn.textContent = "Load";
            loadBtn.onclick = (function (name, hash) {
                return function () { loadConfig(name, hash); };
            })(cfgName, cfghash);
            tr.insertCell(-1).appendChild(loadBtn);

            var dlLink = document.createElement("a");
            dlLink.href = Api.getBundleUrl(cfghash);
            dlLink.className = "btn btn-sm btn-outline-success";
            dlLink.textContent = "Download";
            dlLink.download = "danger_finger_" + cfghash.substring(0, 8) + ".zip";
            tr.insertCell(-1).appendChild(dlLink);

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

    function loadConfig(cfgName, cfghash) {
        setPreviewStatus("Loading config\u2026");
        Api.fetchConfig(cfghash, function (config) {
            Params.applyLoadedConfig(config);
            var cfgEl = document.getElementById("configname");
            if (cfgEl) cfgEl.value = cfgName;
            loadBundleZip(cfghash);
        });
    }

    function loadBundleZip(cfghash) {
        setPreviewStatus("Loading model files\u2026");
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
                    setPreviewStatus("Model loaded.");
                    Api.requestPreview(Params.getCurrentParams);
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

    window.addEventListener("load", function () {
        doResize();

        // Restore any previously saved auth state before initialising modules
        loadStoredAuth();
        initLoginLogout();

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

        Viewer.init({
            baseurl: baseurl,
            onStatus: setPreviewStatus,
        });
        Viewer.setPartData(parts, partNameToId);
        Viewer.initResizeHandle();

        Params.init({
            username: getUsername(),
            onPreviewRequest: function () { Api.requestPreview(Params.getCurrentParams); },
            onPartToggle: onPartToggle,
            onSaveSuccess: onSaveSuccess,
            onStatus: setPreviewStatus,
        });

        // Fetch public data immediately (no auth required)
        Api.fetchParts();
        Api.fetchParams();

        // Handle auth callback AFTER fetching parts (so _wpAuthUrl is ready if it's in the
        // /api/parts response — but we also pass the site_url from the callback as fallback).
        // We kick off fetchParts async and handle the callback in parallel since the callback
        // URL already contains site_url from WordPress.
        handleAuthCallback(function (authed) {
            // Fetch profiles once auth state is settled (whether we just authed or loaded from storage)
            if (isAuthenticated()) {
                Api.fetchProfiles(getUsername());
            }
        });

        // If already authenticated from sessionStorage (no callback), fetch profiles now
        if (isAuthenticated() && !new URLSearchParams(window.location.search).get("jwt_auth")) {
            Api.fetchProfiles(getUsername());
        }
    });

    // Expose slide_change globally for inline oninput handler in HTML
    window.slide_change = function () { Viewer.slideChange(); };
})();
