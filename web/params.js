// params.js — parameter form rendering, dirty/change tracking, part toggle builder.
// Depends on: api.js (calls Api.requestPreview through callback)

var Params = (function () {
    var _params = {};
    var _partVisibility = {};
    var _username = "";
    var _onPreviewRequest = null;
    var _onPartToggle = null;
    var _onSaveRequested = null;
    var _onRenderRequested = null;
    var _onStatus = null;

    function init(opts) {
        _username = opts.username || "";
        _onPreviewRequest = opts.onPreviewRequest || null;
        _onPartToggle = opts.onPartToggle || null;
        _onSaveRequested = opts.onSaveRequested || null;
        _onRenderRequested = opts.onRenderRequested || null;
        _onStatus = opts.onStatus || null;
    }

    function setUsername(username) { _username = username || ""; }
    function getUsername() { return _username || ""; }
    function getParams() { return _params; }
    function getPartVisibility() { return _partVisibility; }

    function getCurrentParams() {
        var out = {};
        for (var k in _params) {
            if (!_params.hasOwnProperty(k)) continue;
            if (_params[k] && _params[k]["Value"] !== undefined) {
                var n = parseFloat(_params[k]["Value"]);
                out[k] = isNaN(n) ? _params[k]["Value"] : n;
            }
        }
        return out;
    }

    function getConfigName() {
        var cfgEl = document.getElementById("configname");
        var cfg = (cfgEl && cfgEl.value) ? cfgEl.value.trim() : "unnamed";
        return cfg || "unnamed";
    }

    function setConfigName(name) {
        var cfgEl = document.getElementById("configname");
        if (cfgEl) cfgEl.value = name || "";
    }

    function _minmax(v, minv, maxv) {
        var val = parseFloat(v);
        if (!isNaN(minv) && minv !== null && val < parseFloat(minv)) val = parseFloat(minv);
        if (!isNaN(maxv) && maxv !== null && val > parseFloat(maxv)) val = parseFloat(maxv);
        return val;
    }

    function _updateParamRow(k) {
        var el = document.getElementById("param_val_" + k);
        if (!el) return;
        var p = _params[k];
        var isModified = p.dirty || p.Changed;
        var row = el.closest("tr");
        if (row) {
            row.classList.toggle("table-warning", !!p.dirty);
            row.classList.toggle("table-info", !!p.Changed && !p.dirty);
        }
        var badge = document.getElementById("param_badge_" + k);
        if (badge) {
            if (p.dirty) {
                badge.textContent = "unsaved";
                badge.className = "badge badge-warning ml-1";
                badge.style.display = "";
            } else if (p.Changed) {
                badge.textContent = "modified";
                badge.className = "badge badge-info ml-1";
                badge.style.display = "";
            } else {
                badge.style.display = "none";
            }
        }
        var resetBtn = document.getElementById("param_reset_" + k);
        if (resetBtn) resetBtn.style.display = isModified ? "" : "none";
    }

    function onChange(k) {
        var el = document.getElementById("param_val_" + k);
        if (!el || !_params[k]) return;
        var raw = el.value;
        var p = _params[k];
        var isEnum = Array.isArray(p.EnumOptions);
        var val;
        if (isEnum) {
            val = raw;
        } else {
            val = _minmax(raw, p["Minimum"], p["Maximum"]);
            el.value = val;
        }
        p["Value"] = val;
        p["Changed"] = (String(val) !== String(p["Default"]));
        p.dirty = true;
        _updateParamRow(k);
        _onPreviewRequest && _onPreviewRequest();
    }

    var _presets = {
        "Adult index finger": {
            intermediate_length: 24, distal_length: 24, distal_base_length: 6,
            socket_circumference_proximal: 63.4, socket_circumference_distal: 57.3, socket_depth: 34
        },
        "Adult pinky": {
            intermediate_length: 16, distal_length: 16, distal_base_length: 4.5,
            socket_circumference_proximal: 52, socket_circumference_distal: 46, socket_depth: 28
        },
        "Child index (age 8-12)": {
            intermediate_length: 18, distal_length: 18, distal_base_length: 5,
            socket_circumference_proximal: 48, socket_circumference_distal: 42, socket_depth: 26
        },
        "Adult thumb": {
            intermediate_length: 20, distal_length: 22, distal_base_length: 7,
            socket_circumference_proximal: 72, socket_circumference_distal: 64, socket_depth: 30
        },
    };

    function _paramRowHtml(key, p) {
        var isEnum = Array.isArray(p["EnumOptions"]);
        var val = p["Value"];
        var def = p["Default"];
        var minv = p["Minimum"];
        var maxv = p["Maximum"];
        var doc = p["Documentation"] || "";

        var rangeHtml = (minv !== null && minv !== undefined && maxv !== null && maxv !== undefined)
            ? '<span class="text-muted small">' + minv + '–' + maxv + '</span>' : "";
        var defHtml = '<span class="text-muted small">' + (def !== null && def !== undefined ? def : "") + '</span>';
        var inputHtml;
        if (isEnum) {
            inputHtml = '<select id="param_val_' + key + '" class="form-control form-control-sm" onchange="Params.onChange(\'' + key + '\')">';
            p["EnumOptions"].forEach(function (opt) {
                inputHtml += '<option value="' + opt + '"' + (String(val) === String(opt) ? ' selected' : '') + '>' + opt + '</option>';
            });
            inputHtml += '</select>';
        } else {
            inputHtml = '<input id="param_val_' + key + '" type="number" step="any" class="form-control form-control-sm" value="' + val + '" onchange="Params.onChange(\'' + key + '\')" />';
        }

        var resetHtml = '<button type="button" id="param_reset_' + key + '" class="btn btn-sm btn-link text-muted p-0" style="display:none" onclick="Params.resetParam(\'' + key + '\')" title="Reset to default">&times;</button>';

        return '<tr>'
            + '<td class="align-middle"><code>' + key + '</code><span id="param_badge_' + key + '" class="badge ml-1" style="display:none"></span></td>'
            + '<td class="align-middle small text-muted">' + doc + '</td>'
            + '<td>' + inputHtml + '</td>'
            + '<td class="align-middle">' + defHtml + '</td>'
            + '<td class="align-middle">' + rangeHtml + '</td>'
            + '<td class="align-middle text-center">' + resetHtml + '</td>'
            + '</tr>';
    }

    function fillParams(json) {
        _params = {};
        for (var k in json) {
            if (!json.hasOwnProperty(k)) continue;
            if (json[k]["Hidden"]) continue;
            _params[k] = Object.assign({}, json[k], { dirty: false, Changed: false });
        }

        var commonRows = "", stdRows = "", advRows = "";
        var keys = Object.keys(_params);
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            var p = _params[key];
            var rowHtml = _paramRowHtml(key, p);
            if (p["Section"] === "common") commonRows += rowHtml;
            else if (p["Advanced"]) advRows += rowHtml;
            else stdRows += rowHtml;
        }

        var theadHtml = '<thead class="thead-light"><tr>'
            + '<th>Parameter</th><th>Description</th><th style="min-width:130px">Value</th><th>Default</th><th>Range</th><th></th>'
            + '</tr></thead>';

        var container = document.getElementById("showData");
        container.innerHTML = "";

        var form = document.createElement("form");
        form.id = "form";
        form.method = "POST";

        var presetDiv = document.createElement("div");
        presetDiv.className = "form-inline mb-2";
        presetDiv.innerHTML = '<label class="mr-2 small font-weight-bold">Start from preset:</label>';
        var presetSelect = document.createElement("select");
        presetSelect.id = "preset_select";
        presetSelect.className = "form-control form-control-sm";
        var defaultOpt = document.createElement("option");
        defaultOpt.value = "";
        defaultOpt.textContent = "Custom";
        presetSelect.appendChild(defaultOpt);
        Object.keys(_presets).forEach(function (name) {
            var opt = document.createElement("option");
            opt.value = name;
            opt.textContent = name;
            presetSelect.appendChild(opt);
        });
        presetSelect.onchange = function () {
            var name = presetSelect.value;
            if (!name || !_presets[name]) return;
            applyLoadedConfig(_presets[name]);
            _onPreviewRequest && _onPreviewRequest();
            presetSelect.value = "";
        };
        presetDiv.appendChild(presetSelect);
        form.appendChild(presetDiv);

        if (commonRows) {
            var commonHeader = document.createElement("h6");
            commonHeader.className = "mt-1 mb-1";
            commonHeader.innerHTML = '<span class="badge badge-primary mr-1">Common</span> Start here &mdash; most-used sizing parameters'
                + ' <a href="#" class="small ml-2" onclick="Params.resetAll(); return false;">Reset all to defaults</a>';
            form.appendChild(commonHeader);
            var commonTable = document.createElement("table");
            commonTable.className = "table table-sm table-hover table-bordered mb-2";
            commonTable.innerHTML = theadHtml + '<tbody>' + commonRows + '</tbody>';
            form.appendChild(commonTable);
        }

        if (stdRows) {
            var stdHeader = document.createElement("h6");
            stdHeader.className = "mt-2 mb-1 text-muted";
            stdHeader.textContent = "Standard Parameters";
            form.appendChild(stdHeader);
            var stdTable = document.createElement("table");
            stdTable.className = "table table-sm table-hover table-bordered mb-2";
            stdTable.innerHTML = theadHtml + '<tbody>' + stdRows + '</tbody>';
            form.appendChild(stdTable);
        }

        var actionDiv = document.createElement("div");
        actionDiv.className = "form-inline mb-2";
        actionDiv.innerHTML = ''
            + '<label class="mr-2" for="configname">Save as:</label>'
            + '<input id="configname" type="text" class="form-control form-control-sm mr-2" placeholder="Config name" />'
            + '<button id="save_btn" type="button" class="btn btn-primary btn-sm mr-2" onclick="Params.submitSave()">Save</button>'
            + '<button id="render_btn" type="button" class="btn btn-outline-success btn-sm" onclick="Params.submitRender()">Render</button>';
        form.appendChild(actionDiv);
        container.appendChild(form);

        var advDiv = document.createElement("div");
        advDiv.innerHTML = ''
            + '<div class="mt-2">'
            + '<a class="text-muted small" data-toggle="collapse" href="#advancedParams" role="button" aria-expanded="false">'
            + 'Show advanced settings <span class="badge badge-warning">⚠ affects print fit</span>'
            + '</a>'
            + '<div class="collapse" id="advancedParams">'
            + '<div class="alert alert-warning mt-1 mb-1 py-1 small">These parameters affect print fit and physical dimensions. Change only if you know what you are doing.</div>'
            + '<table class="table table-sm table-hover table-bordered">'
            + theadHtml + '<tbody>' + advRows + '</tbody>'
            + '</table></div></div>';
        container.appendChild(advDiv);

        var adv2 = document.getElementById("advData");
        if (adv2) adv2.innerHTML = "";
    }

    function resetParam(k) {
        if (!_params[k]) return;
        var def = _params[k]["Default"];
        if (def === null || def === undefined) return;
        _params[k]["Value"] = def;
        _params[k]["Changed"] = false;
        _params[k].dirty = false;
        var el = document.getElementById("param_val_" + k);
        if (el) el.value = def;
        _updateParamRow(k);
        _onPreviewRequest && _onPreviewRequest();
    }

    function resetAll() {
        for (var k in _params) {
            if (!_params.hasOwnProperty(k)) continue;
            var def = _params[k]["Default"];
            if (def === null || def === undefined) continue;
            _params[k]["Value"] = def;
            _params[k]["Changed"] = false;
            _params[k].dirty = false;
            var el = document.getElementById("param_val_" + k);
            if (el) el.value = def;
            _updateParamRow(k);
        }
        _onPreviewRequest && _onPreviewRequest();
    }

    function clearDirty() {
        for (var k in _params) {
            if (_params.hasOwnProperty(k)) {
                _params[k].dirty = false;
                _updateParamRow(k);
            }
        }
    }

    function applyLoadedConfig(config) {
        for (var k in config) {
            if (!config.hasOwnProperty(k)) continue;
            _params[k] = _params[k] || {};
            _params[k]["Value"] = config[k];
            _params[k]["Changed"] = (String(config[k]) !== String(_params[k]["Default"]));
            _params[k].dirty = false;
            var el = document.getElementById("param_val_" + k);
            if (el) {
                el.value = config[k];
                _updateParamRow(k);
            }
        }
        clearDirty();
    }

    function setButtonsDisabled(disabled) {
        var saveBtn = document.getElementById("save_btn");
        var renderBtn = document.getElementById("render_btn");
        if (saveBtn) saveBtn.disabled = !!disabled;
        if (renderBtn) renderBtn.disabled = !!disabled;
    }

    function setRenderDisabled(disabled) {
        var renderBtn = document.getElementById("render_btn");
        if (renderBtn) renderBtn.disabled = !!disabled;
    }

    function setRenderButtonLabel(label) {
        var renderBtn = document.getElementById("render_btn");
        if (renderBtn) renderBtn.textContent = label || "Render";
    }

    function submitSave() {
        _onSaveRequested && _onSaveRequested({
            username: _username,
            configName: getConfigName(),
            params: getCurrentParams(),
        });
    }

    function submitRender() {
        _onRenderRequested && _onRenderRequested({
            username: _username,
            configName: getConfigName(),
            params: getCurrentParams(),
        });
    }

    function buildPartToggles(partList) {
        var container = document.getElementById("part-toggles");
        if (!container) return;
        container.innerHTML = "";
        partList.forEach(function (part) {
            var id = part.id;
            var label = part.label || id;
            _partVisibility[id] = true;
            var wrapper = document.createElement("div");
            wrapper.className = "form-check form-check-inline mr-3";
            var cb = document.createElement("input");
            cb.type = "checkbox";
            cb.className = "form-check-input";
            cb.id = "toggle_" + id;
            cb.checked = true;
            cb.onchange = (function (partId) {
                return function () {
                    _partVisibility[partId] = cb.checked;
                    _onPartToggle && _onPartToggle(partId, cb.checked);
                };
            })(id);
            var lbl = document.createElement("label");
            lbl.className = "form-check-label";
            lbl.htmlFor = "toggle_" + id;
            lbl.textContent = label;
            wrapper.appendChild(cb);
            wrapper.appendChild(lbl);
            container.appendChild(wrapper);
        });
    }

    return {
        init: init,
        setUsername: setUsername,
        getUsername: getUsername,
        getParams: getParams,
        getPartVisibility: getPartVisibility,
        getCurrentParams: getCurrentParams,
        getConfigName: getConfigName,
        setConfigName: setConfigName,
        fillParams: fillParams,
        onChange: onChange,
        applyLoadedConfig: applyLoadedConfig,
        resetParam: resetParam,
        resetAll: resetAll,
        clearDirty: clearDirty,
        submitSave: submitSave,
        submitRender: submitRender,
        buildPartToggles: buildPartToggles,
        setButtonsDisabled: setButtonsDisabled,
        setRenderDisabled: setRenderDisabled,
        setRenderButtonLabel: setRenderButtonLabel,
    };
})();
