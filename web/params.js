// params.js — parameter form rendering, dirty/change tracking, part toggle builder.
// Depends on: api.js (calls Api.requestPreview)

var Params = (function () {
    var _params = {};          // paramName -> {Value, Default, Minimum, Maximum, Advanced, Documentation, Hidden, EnumOptions, dirty, Changed}
    var _partVisibility = {};  // partName -> bool (true = visible)
    var _username = "nick";
    var _onPreviewRequest = null;
    var _onPartToggle = null;  // callback(partName, visible)
    var _onSaveSuccess = null;

    function init(opts) {
        _username = opts.username || "nick";
        _onPreviewRequest = opts.onPreviewRequest || null;
        _onPartToggle = opts.onPartToggle || null;
        _onSaveSuccess = opts.onSaveSuccess || null;
    }

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
        var isChanged = p.Changed;
        var isDirty = p.dirty;
        var row = el.closest("tr");
        if (row) {
            row.classList.toggle("table-warning", isDirty);
            row.classList.toggle("table-info", isChanged && !isDirty);
        }
        var badge = document.getElementById("param_badge_" + k);
        if (badge) {
            if (isDirty) {
                badge.textContent = "unsaved";
                badge.className = "badge badge-warning ml-1";
                badge.style.display = "";
            } else if (isChanged) {
                badge.textContent = "modified";
                badge.className = "badge badge-info ml-1";
                badge.style.display = "";
            } else {
                badge.style.display = "none";
            }
        }
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
        p["dirty"] = true;
        _updateParamRow(k);
        _onPreviewRequest && _onPreviewRequest();
    }

    function fillParams(json) {
        _params = {};
        for (var k in json) {
            if (!json.hasOwnProperty(k)) continue;
            if (json[k]["Hidden"]) continue;
            _params[k] = Object.assign({}, json[k], { dirty: false, Changed: false });
        }

        var stdRows = "", advRows = "";
        var rowIdx = 1;

        for (var key in _params) {
            if (!_params.hasOwnProperty(key)) continue;
            var p = _params[key];
            var isAdv = !!p["Advanced"];
            var isEnum = Array.isArray(p["EnumOptions"]);
            var val = p["Value"];
            var def = p["Default"];
            var minv = p["Minimum"];
            var maxv = p["Maximum"];
            var doc = p["Documentation"] || "";

            var rangeHtml = (minv !== null && minv !== undefined && maxv !== null && maxv !== undefined)
                ? '<span class="text-muted small">' + minv + '\u2013' + maxv + '</span>'
                : "";

            var defHtml = '<span class="text-muted small">' + (def !== null && def !== undefined ? def : "") + "</span>";

            var inputHtml;
            if (isEnum) {
                inputHtml = '<select id="param_val_' + key + '" class="form-control form-control-sm" onchange="Params.onChange(\'' + key + '\')">';
                p["EnumOptions"].forEach(function (opt) {
                    inputHtml += '<option value="' + opt + '"' + (String(val) === String(opt) ? " selected" : "") + ">" + opt + "</option>";
                });
                inputHtml += "</select>";
            } else {
                inputHtml = '<input id="param_val_' + key + '" type="number" step="any" class="form-control form-control-sm" value="' + val + '" onchange="Params.onChange(\'' + key + '\')" />';
            }

            var rowHtml = "<tr>" +
                '<td class="align-middle"><code>' + key + '</code><span id="param_badge_' + key + '" class="badge ml-1" style="display:none"></span></td>' +
                '<td class="align-middle small text-muted">' + doc + "</td>" +
                "<td>" + inputHtml + "</td>" +
                "<td class='align-middle'>" + defHtml + "</td>" +
                "<td class='align-middle'>" + rangeHtml + "</td>" +
                "</tr>";

            if (isAdv) {
                advRows += rowHtml;
            } else {
                stdRows += rowHtml;
            }
            rowIdx++;
        }

        var theadHtml = "<thead class='thead-light'><tr>" +
            "<th>Parameter</th><th>Description</th><th style='min-width:130px'>Value</th><th>Default</th><th>Range</th>" +
            "</tr></thead>";

        var container = document.getElementById("showData");
        container.innerHTML = "";

        // Standard table
        var stdTable = document.createElement("table");
        stdTable.className = "table table-sm table-hover table-bordered mb-2";
        stdTable.innerHTML = theadHtml + "<tbody>" + stdRows + "</tbody>";

        var form = document.createElement("form");
        form.id = "form";
        form.method = "POST";
        form.appendChild(stdTable);

        // Save row
        var saveDiv = document.createElement("div");
        saveDiv.className = "form-inline mb-2";
        saveDiv.innerHTML =
            '<label class="mr-2" for="configname">Save as:</label>' +
            '<input id="configname" type="text" class="form-control form-control-sm mr-2" placeholder="Config name" />' +
            '<button type="button" class="btn btn-primary btn-sm" onclick="Params.submit()">Save</button>';
        form.appendChild(saveDiv);

        container.appendChild(form);

        // Advanced collapse
        var advDiv = document.createElement("div");
        advDiv.innerHTML =
            '<div class="mt-2">' +
            '<a class="text-muted small" data-toggle="collapse" href="#advancedParams" role="button" aria-expanded="false">' +
            'Show advanced settings <span class="badge badge-warning">⚠ affects print fit</span>' +
            '</a>' +
            '<div class="collapse" id="advancedParams">' +
            '<div class="alert alert-warning mt-1 mb-1 py-1 small">These parameters affect print fit and physical dimensions. Change only if you know what you are doing.</div>' +
            '<table class="table table-sm table-hover table-bordered">' +
            theadHtml + "<tbody>" + advRows + "</tbody>" +
            "</table></div></div>";
        container.appendChild(advDiv);

        // Legacy advData clear
        var adv2 = document.getElementById("advData");
        if (adv2) adv2.innerHTML = "";
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
            _params[k]["dirty"] = false;
            var el = document.getElementById("param_val_" + k);
            if (el) { el.value = config[k]; _updateParamRow(k); }
        }
        clearDirty();
    }

    function submit() {
        var cfgEl = document.getElementById("configname");
        var cfg = (cfgEl && cfgEl.value) ? cfgEl.value.trim() : "unnamed";
        if (!cfg) cfg = "unnamed";
        Api.saveConfig(_username, cfg, getCurrentParams(),
            function () {
                clearDirty();
                _onSaveSuccess && _onSaveSuccess(cfg);
                alert('Saved as "' + cfg + '"');
            },
            function (err) { alert("Save failed: " + err); }
        );
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
        getParams: getParams,
        getPartVisibility: getPartVisibility,
        getCurrentParams: getCurrentParams,
        fillParams: fillParams,
        onChange: onChange,
        applyLoadedConfig: applyLoadedConfig,
        clearDirty: clearDirty,
        submit: submit,
        buildPartToggles: buildPartToggles,
    };
})();
