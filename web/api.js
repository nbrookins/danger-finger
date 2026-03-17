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
    var _previewPollTimer = null;
    var _latestPreviewJobId = null;
    var PREVIEW_DEBOUNCE_MS = 500;
    var PREVIEW_POLL_MS = 2000;
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

    function _parseJson(text) {
        try { return JSON.parse(text || "{}"); } catch (e) { return {}; }
    }

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
        if (_authToken) xhttp.setRequestHeader("Authorization", "Bearer " + _authToken);
        xhttp.send(body !== null && body !== undefined ? body : "");
    }

    function fetchWpJwt(wpAuthUrl, userLogin, appPassword, onSuccess, onError) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState !== 4) return;
            if (this.status === 200) {
                var data = _parseJson(this.responseText);
                if (data.token) onSuccess && onSuccess(data);
                else onError && onError(data.message || "No token in response");
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
        if (window.__STATIC_PARTS__) {
            _onPartsLoaded && _onPartsLoaded(window.__STATIC_PARTS__);
            return;
        }
        _xhr("GET", "api/parts", null, function (text) {
            try { _onPartsLoaded && _onPartsLoaded(JSON.parse(text)); } catch (e) { console.error("fetchParts parse error", e); }
        }, function (text, status) {
            console.error("fetchParts failed", status, text);
        });
    }

    function fetchParams() {
        if (window.__STATIC_PARAMS__) {
            _onParamsLoaded && _onParamsLoaded(window.__STATIC_PARAMS__);
            return;
        }
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
            if (xhttp.status === 200) onSuccess && onSuccess(xhttp.response);
            else onError && onError("Failed to load bundle.zip (" + xhttp.status + ")");
        };
        xhttp.onerror = function () { onError && onError("Network error loading bundle.zip"); };
        xhttp.open("GET", _readBase() + "render/" + cfghash + "/bundle.zip", true);
        xhttp.send();
    }

    function getBundleUrl(cfghash) {
        return _readBase() + "render/" + cfghash + "/bundle.zip";
    }

    function fetchRenderStatus(cfghash, onSuccess, onError) {
        _xhr("GET", "render/" + cfghash + "/status", null, function (text) {
            onSuccess && onSuccess(_parseJson(text));
        }, function (text, status) {
            if (status === 0) { onError && onError(RENDER_OFFLINE_MSG, status); return; }
            var data = _parseJson(text);
            onError && onError(data.error || ("Status request failed (" + status + ")"), status, data);
        }, "read");
    }

    function fetchJobStatus(jobId, onSuccess, onError) {
        _xhr("GET", "api/jobs/" + jobId, null, function (text) {
            onSuccess && onSuccess(_parseJson(text));
        }, function (text, status) {
            if (status === 0) { onError && onError(RENDER_OFFLINE_MSG, status); return; }
            var data = _parseJson(text);
            onError && onError(data.error || ("Job request failed (" + status + ")"), status, data);
        }, "read");
    }

    function requestPreview(currentParams, quality) {
        if (_previewDebounceTimer) clearTimeout(_previewDebounceTimer);
        if (_previewPollTimer) clearTimeout(_previewPollTimer);
        var payload = Object.assign({}, currentParams);
        if (quality) payload.quality = quality;
        _onPreviewError && _onPreviewError("Rendering...", false);
        var body = JSON.stringify(payload);
        _xhr("POST", "api/preview", body, function (text, status) {
            var res = _parseJson(text);
            if (status === 202 && res.job_id) {
                _latestPreviewJobId = res.job_id;
                _onPreviewError && _onPreviewError("Render queued...", false);
                _pollPreview(res.job_id);
            } else if (res.stl_urls && Object.keys(res.stl_urls).length) {
                _onPreviewReady && _onPreviewReady(res);
            } else {
                _onPreviewError && _onPreviewError("Render returned no models.", true);
            }
        }, function (text, status) {
            if (status === 0) {
                _onPreviewError && _onPreviewError(RENDER_OFFLINE_MSG, true);
                return;
            }
            var r = _parseJson(text);
            _onPreviewError && _onPreviewError(r.error || ("Render failed (" + status + ")"), true);
        }, "render");
    }

    function _pollPreview(jobId) {
        if (_previewPollTimer) clearTimeout(_previewPollTimer);
        _previewPollTimer = setTimeout(function () {
            _previewPollTimer = null;
            if (_latestPreviewJobId !== jobId) return;
            _xhr("GET", "api/jobs/" + jobId, null, function (text) {
                if (_latestPreviewJobId !== jobId) return;
                var payload = _parseJson(text);
                if (payload.status === "complete" && payload.result) {
                    var res = payload.result;
                    if (res.stl_urls && Object.keys(res.stl_urls).length) {
                        _onPreviewReady && _onPreviewReady(res);
                    } else {
                        _onPreviewError && _onPreviewError("Preview returned no models.", true);
                    }
                } else if (payload.status === "failed") {
                    _onPreviewError && _onPreviewError(payload.error || "Preview failed.", true);
                } else {
                    var msg = payload.status === "running" ? "Rendering..." : "Render queued...";
                    _onPreviewError && _onPreviewError(msg, false);
                    _pollPreview(jobId);
                }
            }, function (text, status) {
                if (_latestPreviewJobId !== jobId) return;
                if (status === 0) {
                    _onPreviewError && _onPreviewError(RENDER_OFFLINE_MSG, true);
                    return;
                }
                _onPreviewError && _onPreviewError("Failed to check preview status.", true);
            }, "render");
        }, PREVIEW_POLL_MS);
    }

    function saveConfig(username, cfgName, currentParams, onSuccess, onError) {
        _xhr("POST", "profile/" + username + "/config/" + encodeURIComponent(cfgName), JSON.stringify(currentParams), function (text) {
            onSuccess && onSuccess(_parseJson(text));
        }, function (text, status) {
            if (status === 0) { onError && onError(RENDER_OFFLINE_MSG); return; }
            var data = _parseJson(text);
            onError && onError(data.error || text || String(status), data, status);
        }, "render");
    }

    function renderConfig(currentParams, onSuccess, onError) {
        _xhr("POST", "api/render", JSON.stringify(currentParams), function (text, status) {
            onSuccess && onSuccess(_parseJson(text), status);
        }, function (text, status) {
            if (status === 0) { onError && onError(RENDER_OFFLINE_MSG); return; }
            var data = _parseJson(text);
            onError && onError(data.error || text || String(status), data, status);
        }, "render");
    }

    function deleteConfig(username, cfgName, onSuccess, onError) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState !== 4) return;
            if (this.status === 204) onSuccess && onSuccess();
            else if (this.status === 0) onError && onError(RENDER_OFFLINE_MSG);
            else {
                var data = _parseJson(this.responseText);
                onError && onError(data.error || "Delete failed.");
            }
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
        fetchRenderStatus: fetchRenderStatus,
        fetchJobStatus: fetchJobStatus,
        requestPreview: requestPreview,
        saveConfig: saveConfig,
        renderConfig: renderConfig,
        deleteConfig: deleteConfig,
    };
})();
