// api.js — all XHR calls to the backend. No DOM access. No dependencies on other modules.
// Callbacks are passed at call time or set via init.

var Api = (function () {
    var _baseurl = "";
    var _readUrl = "";
    var _renderUrl = "";
    var _authToken = null;
    var _onPartsLoaded = null;
    var _onParamsLoaded = null;
    var _onProfilesLoaded = null;
    var _onPreviewReady = null;
    var _onPreviewError = null;
    var _previewDebounceTimer = null;
    var PREVIEW_DEBOUNCE_MS = 500;
    var RENDER_OFFLINE_MSG = "Render server is offline. You can still browse configurations, but live preview is unavailable.";

    function init(opts) {
        _baseurl = opts.baseurl || "";
        _readUrl = opts.readUrl || "";
        _renderUrl = opts.renderUrl || "";
        _onPartsLoaded = opts.onPartsLoaded || null;
        _onParamsLoaded = opts.onParamsLoaded || null;
        _onProfilesLoaded = opts.onProfilesLoaded || null;
        _onPreviewReady = opts.onPreviewReady || null;
        _onPreviewError = opts.onPreviewError || null;
    }

    function setAuthToken(token) { _authToken = token || null; }
    function getAuthToken() { return _authToken; }

    function _readBase() { return _readUrl || _baseurl; }
    function _renderBase() { return _renderUrl || _baseurl; }

    function _xhr(method, url, body, onSuccess, onError, urlMode) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState !== 4) return;
            if (this.status >= 200 && this.status < 300) {
                onSuccess && onSuccess(this.responseText, this.status);
            } else if (this.status === 0) {
                onError && onError("", 0);
            } else {
                onError && onError(this.responseText, this.status);
            }
        };
        xhttp.onerror = function () { onError && onError("", 0); };
        var base = urlMode === "read" ? _readBase() : urlMode === "render" ? _renderBase() : _baseurl;
        xhttp.open(method, base + url, true);
        xhttp.setRequestHeader("Content-Type", "application/json");
        if (_authToken) {
            xhttp.setRequestHeader("Authorization", "Bearer " + _authToken);
        }
        if (body !== null && body !== undefined) {
            xhttp.send(body);
        } else {
            xhttp.send("");
        }
    }

    /**
     * Exchange a WordPress Application Password for a JWT token.
     * Called after the authorize-application.php callback returns user_login + password.
     *
     * @param {string}   wpAuthUrl    WordPress base URL (e.g. "https://dangercreations.com")
     * @param {string}   userLogin    WP username from callback URL
     * @param {string}   appPassword  Application Password from callback URL
     * @param {Function} onSuccess    Called with { token, user_nicename, user_display_name, user_email }
     * @param {Function} onError      Called with error message string
     */
    function fetchWpJwt(wpAuthUrl, userLogin, appPassword, onSuccess, onError) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState !== 4) return;
            if (this.status === 200) {
                try {
                    var data = JSON.parse(this.responseText);
                    if (data.token) {
                        onSuccess && onSuccess(data);
                    } else {
                        onError && onError(data.message || "No token in response");
                    }
                } catch (e) {
                    onError && onError("JSON parse error: " + e.message);
                }
            } else {
                var msg = "JWT request failed (" + this.status + ")";
                try { msg = JSON.parse(this.responseText).message || msg; } catch (e2) {}
                onError && onError(msg);
            }
        };
        var endpoint = wpAuthUrl.replace(/\/$/, "") + "/wp-json/jwt-auth/v1/token";
        xhttp.open("POST", endpoint, true);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({ username: userLogin, password: appPassword }));
    }

    function fetchParts() {
        _xhr("GET", "api/parts", null, function (text) {
            try { _onPartsLoaded && _onPartsLoaded(JSON.parse(text)); } catch (e) { console.error("fetchParts parse error", e); }
        }, function (text, status) {
            console.error("fetchParts failed", status, text);
        });
    }

    function fetchParams() {
        _xhr("GET", "params/all", null, function (text) {
            try { _onParamsLoaded && _onParamsLoaded(JSON.parse(text)); } catch (e) { console.error("fetchParams parse error", e); }
        }, function (text, status) {
            console.error("fetchParams failed", status, text);
        });
    }

    function fetchProfiles(username) {
        _xhr("GET", "profiles/" + username, null, function (text) {
            try { _onProfilesLoaded && _onProfilesLoaded(JSON.parse(text)); } catch (e) { console.error("fetchProfiles parse error", e); }
        }, function (text, status) {
            console.error("fetchProfiles failed", status, text);
        }, "read");
    }

    function fetchConfig(cfghash, onSuccess) {
        _xhr("GET", "configs/" + cfghash, null, function (text) {
            try { onSuccess && onSuccess(JSON.parse(text)); } catch (e) { console.error("fetchConfig parse error", e); }
        }, function (text, status) {
            console.error("fetchConfig failed", status, text);
        }, "read");
    }

    function fetchBundleZip(cfghash, onSuccess, onError) {
        var xhttp = new XMLHttpRequest();
        xhttp.responseType = "arraybuffer";
        xhttp.onload = function () {
            if (xhttp.status === 200) {
                onSuccess && onSuccess(xhttp.response);
            } else {
                onError && onError("Failed to load bundle.zip (" + xhttp.status + ")");
            }
        };
        xhttp.onerror = function () { onError && onError("Network error loading bundle.zip"); };
        xhttp.open("GET", _readBase() + "render/" + cfghash + "/bundle.zip", true);
        xhttp.send();
    }

    function getBundleUrl(cfghash) {
        return _readBase() + "render/" + cfghash + "/bundle.zip";
    }

    function requestPreview(getCurrentParams) {
        if (_previewDebounceTimer) clearTimeout(_previewDebounceTimer);
        _previewDebounceTimer = setTimeout(function () {
            _previewDebounceTimer = null;
            _onPreviewError && _onPreviewError("Updating preview\u2026", false);
            var body = JSON.stringify(getCurrentParams());
            _xhr("POST", "api/preview", body, function (text) {
                try {
                    var res = JSON.parse(text || "{}");
                    if (res.stl_urls && Object.keys(res.stl_urls).length) {
                        _onPreviewReady && _onPreviewReady(res);
                    } else {
                        _onPreviewError && _onPreviewError("Preview returned no models.", true);
                    }
                } catch (e) {
                    _onPreviewError && _onPreviewError("Preview parse error.", true);
                }
            }, function (text, status) {
                if (status === 0) {
                    _onPreviewError && _onPreviewError(RENDER_OFFLINE_MSG, true);
                    return;
                }
                var err = "Preview failed (" + status + ")";
                try { var r = JSON.parse(text); if (r.error) err = r.error; } catch (e) {}
                _onPreviewError && _onPreviewError(err, true);
            }, "render");
        }, PREVIEW_DEBOUNCE_MS);
    }

    function saveConfig(username, cfgName, currentParams, onSuccess, onError) {
        _xhr("POST", "profile/" + username + "/config/" + encodeURIComponent(cfgName),
            JSON.stringify(currentParams),
            function (text, status) {
                var res = {};
                try { res = JSON.parse(text || "{}"); } catch (e) {}
                onSuccess && onSuccess(res);
            },
            function (text, status) {
                if (status === 0) { onError && onError(RENDER_OFFLINE_MSG); return; }
                var errMsg = text || String(status);
                try { errMsg = JSON.parse(text).error || errMsg; } catch (e) {}
                onError && onError(errMsg);
            },
            "render"
        );
    }

    function deleteConfig(username, cfgName, onSuccess, onError) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState !== 4) return;
            if (this.status === 204) { onSuccess && onSuccess(); }
            else if (this.status === 0) { onError && onError(RENDER_OFFLINE_MSG); }
        };
        xhttp.onerror = function () { onError && onError(RENDER_OFFLINE_MSG); };
        xhttp.open("DELETE", _renderBase() + "profile/" + username + "/config/" + encodeURIComponent(cfgName), true);
        if (_authToken) xhttp.setRequestHeader("Authorization", "Bearer " + _authToken);
        xhttp.send();
    }

    return {
        init: init,
        setAuthToken: setAuthToken,
        getAuthToken: getAuthToken,
        fetchWpJwt: fetchWpJwt,
        fetchParts: fetchParts,
        fetchParams: fetchParams,
        fetchProfiles: fetchProfiles,
        fetchConfig: fetchConfig,
        fetchBundleZip: fetchBundleZip,
        getBundleUrl: getBundleUrl,
        requestPreview: requestPreview,
        saveConfig: saveConfig,
        deleteConfig: deleteConfig,
    };
})();
