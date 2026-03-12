// api.js — all XHR calls to the backend. No DOM access. No dependencies on other modules.
// Callbacks are passed at call time or set via init.

var Api = (function () {
    var _baseurl = "";
    var _readUrl = "";
    var _onPartsLoaded = null;
    var _onParamsLoaded = null;
    var _onProfilesLoaded = null;
    var _onPreviewReady = null;
    var _onPreviewError = null;
    var _previewDebounceTimer = null;
    var PREVIEW_DEBOUNCE_MS = 500;

    function init(opts) {
        _baseurl = opts.baseurl || "";
        _readUrl = opts.readUrl || "";
        _onPartsLoaded = opts.onPartsLoaded || null;
        _onParamsLoaded = opts.onParamsLoaded || null;
        _onProfilesLoaded = opts.onProfilesLoaded || null;
        _onPreviewReady = opts.onPreviewReady || null;
        _onPreviewError = opts.onPreviewError || null;
    }

    function _readBase() { return _readUrl || _baseurl; }

    function _xhr(method, url, body, onSuccess, onError, useReadUrl) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState !== 4) return;
            if (this.status >= 200 && this.status < 300) {
                onSuccess && onSuccess(this.responseText, this.status);
            } else {
                onError && onError(this.responseText, this.status);
            }
        };
        var base = useReadUrl ? _readBase() : _baseurl;
        xhttp.open(method, base + url, true);
        xhttp.setRequestHeader("Content-Type", "application/json");
        if (body !== null && body !== undefined) {
            xhttp.send(body);
        } else {
            xhttp.send("");
        }
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
        }, true);
    }

    function fetchConfig(cfghash, onSuccess) {
        _xhr("GET", "configs/" + cfghash, null, function (text) {
            try { onSuccess && onSuccess(JSON.parse(text)); } catch (e) { console.error("fetchConfig parse error", e); }
        }, function (text, status) {
            console.error("fetchConfig failed", status, text);
        }, true);
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
                var err = "Preview failed (" + status + ")";
                try { var r = JSON.parse(text); if (r.error) err = r.error; } catch (e) {}
                _onPreviewError && _onPreviewError(err, true);
            });
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
                var errMsg = text || String(status);
                try { errMsg = JSON.parse(text).error || errMsg; } catch (e) {}
                onError && onError(errMsg);
            }
        );
    }

    function deleteConfig(username, cfgName, onSuccess) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (xhttp.readyState === 4 && xhttp.status === 204) onSuccess && onSuccess();
        };
        xhttp.open("DELETE", _baseurl + "profile/" + username + "/config/" + encodeURIComponent(cfgName), true);
        xhttp.send();
    }

    return { init: init, fetchParts: fetchParts, fetchParams: fetchParams, fetchProfiles: fetchProfiles, fetchConfig: fetchConfig, fetchBundleZip: fetchBundleZip, getBundleUrl: getBundleUrl, requestPreview: requestPreview, saveConfig: saveConfig, deleteConfig: deleteConfig };
})();
