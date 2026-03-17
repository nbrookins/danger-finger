// viewer.js — stl_viewer instance, parts state, model management, explode, plug instances.
// Depends on: vendor/three/three.min.js, vendor/three/OrbitControls.js, stl_viewer.js

var Viewer = (function () {
    var _stlViewer = null;
    var _parts = {};           // id -> {name, pos, exp, rotf}
    var _plugPositions = {};   // id -> [x,y,z]  (IDs 100-103)
    var _plugBaseRots = {};    // id -> [rx,ry,rz] in radians (rest rotation per plug instance)
    var _lastStlUrls = {};     // partName -> url
    var _previewConfig = null;
    var _partNameToId = {};
    var _baseurl = "";
    var _onModLoaded = null;   // callback when any model loads
    var _onStatus = null;      // callback(msg, isError)
    var PLUG_BASE_ID = 100;
    var EXPL_FACTOR = 25;
    var FLEX_MAX_DEG = 90;
    // Parts excluded from the 3D preview: pins is a composite STL with both hinge pins at
    // hardcoded relative positions that can't be correctly placed by a single offset.
    var PREVIEW_SKIP_PARTS = { "pins": true };
    // Parts that move at each hinge during flex
    var PROXIMAL_FLEX_PARTS = { "middle": true, "tip": true, "tipcover": true, "bumper": true };
    var DISTAL_FLEX_PARTS = { "tip": true, "tipcover": true };

    function degtorad(deg) { return deg === 0 ? 0 : deg / 57.3; }

    function init(opts) {
        _baseurl = opts.baseurl || "";
        _onStatus = opts.onStatus || null;
        _onModLoaded = opts.onModLoaded || null;

        var container = document.getElementById("stl_cont");
        _stlViewer = new StlViewer(container, {
            auto_resize: true,
            model_loaded_callback: _modLoaded,
            on_model_mousedown: function (id) {
                var info = document.getElementById("model_info_cont");
                if (info) info.value = JSON.stringify(_stlViewer.get_model_info(id));
            }
        });
    }

    function setPartData(partsMap, partNameToId) {
        _parts = partsMap;
        _partNameToId = partNameToId;
    }

    function setStatus(msg, isError) {
        _onStatus && _onStatus(msg, isError);
    }

    function _modLoaded() {
        document.getElementById("loader").style.display = "none";
        document.getElementById("stl_cont").style.visibility = "visible";
        // Set assembled positions for all regular parts
        for (var id in _parts) {
            if (_parts.hasOwnProperty(id)) {
                var p = _parts[id];
                _stlViewer.set_position(parseInt(id), p.pos[0], p.pos[1], p.pos[2]);
            }
        }
        // Set positions for plug instances
        for (var pid in _plugPositions) {
            if (_plugPositions.hasOwnProperty(pid)) {
                var pp = _plugPositions[pid];
                _stlViewer.set_position(parseInt(pid), pp[0], pp[1], pp[2]);
            }
        }
        // Reapply current explode + flex state
        slideChange();
        flexChange();
        _onModLoaded && _onModLoaded();
    }

    function addModel(id, url) {
        console.log("addModel", id, url);
        document.getElementById("loader").src = _baseurl + "loader.gif";
        var opts = { id: id, filename: url };
        if (_previewConfig) {
            var name = _parts[id] ? _parts[id].name : null;
            if (name) {
                var rot = (_previewConfig.rotateOffsets || {})[name];
                if (rot) {
                    opts.rotationx = degtorad(rot[0]);
                    opts.rotationy = degtorad(rot[1]);
                    opts.rotationz = degtorad(rot[2]);
                }
                var col = (_previewConfig.partColors || {})[name];
                if (col) {
                    opts.color = "#" + col.map(function (c) {
                        return ("0" + Math.round(c * 255).toString(16)).slice(-2);
                    }).join("");
                }
            }
        }
        if (_parts[id]) {
            _parts[id].rotf = [opts.rotationx || 0, opts.rotationy || 0, opts.rotationz || 0];
        }
        try { _stlViewer.add_model(opts); } catch (e) { console.warn("addModel error", id, e); }
    }

    function remModels(ids) {
        ids.forEach(function (id) {
            try { _stlViewer.remove_model(id); } catch (e) {}
        });
    }

    function updateFromStlUrls(stlUrls, partVisibility, absolute) {
        // Remove all current models
        var allIds = Object.keys(_parts).map(Number);
        allIds.forEach(function (id) { try { _stlViewer.remove_model(id); } catch (e) {} });
        for (var i = 0; i < 4; i++) { try { _stlViewer.remove_model(PLUG_BASE_ID + i); } catch (e) {} }

        _lastStlUrls = {};
        for (var partName in stlUrls) {
            if (!stlUrls.hasOwnProperty(partName)) continue;
            if (PREVIEW_SKIP_PARTS[partName]) continue;
            var url = absolute ? stlUrls[partName] : _baseurl + stlUrls[partName];
            _lastStlUrls[partName] = url;
            // plug is displayed only as 4 instances, not as a single centered part
            if (partName === "plug") continue;
            var id = _partNameToId[partName];
            if (id === undefined) continue;
            if (!partVisibility || partVisibility[partName] !== false) {
                addModel(id, url);
            }
        }
        // Re-add plug instances if plug url is available
        _respawnPlugInstances(partVisibility);
    }

    function _respawnPlugInstances(partVisibility) {
        if (!_previewConfig || !_previewConfig.plugInstances) return;
        var plugUrl = _lastStlUrls["plug"] || (_baseurl + "render/plug.stl");
        var showPlugs = !partVisibility || partVisibility["plug"] !== false;
        if (!showPlugs) return;

        var plugCol = (_previewConfig.partColors || {})["plug"];
        var colorHex = plugCol ? "#" + plugCol.map(function (c) {
            return ("0" + Math.round(c * 255).toString(16)).slice(-2);
        }).join("") : null;

        _previewConfig.plugInstances.forEach(function (inst, i) {
            var instId = PLUG_BASE_ID + i;
            _plugPositions[instId] = inst.position;
            var rx = degtorad(inst.rotation[0]);
            var ry = degtorad(inst.rotation[1]);
            var rz = degtorad(inst.rotation[2]);
            _plugBaseRots[instId] = [rx, ry, rz];
            var opts = {
                id: instId,
                filename: plugUrl,
                rotationx: rx,
                rotationy: ry,
                rotationz: rz
            };
            if (colorHex) opts.color = colorHex;
            try { _stlViewer.add_model(opts); } catch (e) { console.warn("plug instance error", instId, e); }
        });
    }

    function applyPreviewConfig(json, partVisibility) {
        if (!json || !json.previewConfig) return;
        _previewConfig = json.previewConfig;

        // Apply position offsets
        var posOff = _previewConfig.positionOffsets || {};
        for (var id in _parts) {
            if (!_parts.hasOwnProperty(id)) continue;
            var name = _parts[id].name;
            if (posOff[name]) {
                _parts[id].pos = [posOff[name][0], posOff[name][1], posOff[name][2]];
            }
        }

        // Apply explode offsets from server if present
        var expOff = _previewConfig.explodeOffsets || {};
        for (var eid in _parts) {
            if (!_parts.hasOwnProperty(eid)) continue;
            var ename = _parts[eid].name;
            if (expOff[ename]) {
                _parts[eid].exp = [expOff[ename][0], expOff[ename][1], expOff[ename][2]];
            }
        }

        // Spawn plug instances
        for (var pi = 0; pi < 4; pi++) { try { _stlViewer.remove_model(PLUG_BASE_ID + pi); } catch (e) {} }
        _plugPositions = {};
        _respawnPlugInstances(partVisibility);
    }

    function slideChange() {
        var flexSlider = document.getElementById("flex");
        var hasFlex = flexSlider && parseFloat(flexSlider.value) > 0;
        if (hasFlex) {
            flexChange();
            return;
        }

        var slider = document.getElementById("explode");
        if (!slider) return;
        var explode = parseFloat(slider.value) * EXPL_FACTOR / 100.0;

        for (var id in _parts) {
            if (!_parts.hasOwnProperty(id)) continue;
            var p = _parts[id];
            try {
                _stlViewer.set_position(parseInt(id),
                    p.pos[0] + p.exp[0] * explode,
                    p.pos[1] + p.exp[1] * explode,
                    p.pos[2] + p.exp[2] * explode);
            } catch (e) {}
        }

        // Plug instances: explode outward along Z (horizontal, away from finger center)
        var plugExp = (_previewConfig && _previewConfig.explodeOffsets && _previewConfig.explodeOffsets["plug"]) || [0, 0, 1];
        for (var pid in _plugPositions) {
            if (!_plugPositions.hasOwnProperty(pid)) continue;
            var pp = _plugPositions[pid];
            var zSign = pp[2] < 0 ? -1 : 1;
            try {
                _stlViewer.set_position(parseInt(pid),
                    pp[0] + plugExp[0] * explode,
                    pp[1] + plugExp[1] * explode,
                    pp[2] + plugExp[2] * explode * zSign);
            } catch (e) {}
        }
    }

    function _rotateXY(pos, pivot, angle) {
        var dx = pos[0] - pivot[0];
        var dy = pos[1] - pivot[1];
        var c = Math.cos(angle);
        var s = Math.sin(angle);
        return [pivot[0] + dx * c - dy * s, pivot[1] + dx * s + dy * c, pos[2]];
    }

    function flexChange() {
        var slider = document.getElementById("flex");
        if (!slider) return;
        var t = parseFloat(slider.value) / 100.0;
        var flexAngle = t * FLEX_MAX_DEG * Math.PI / 180.0;

        var pivots = (_previewConfig && _previewConfig.hingePivots) || {};
        var proxPivot = pivots.proximal || [0, 0, 0];
        var distPivot = pivots.distal || [0, 24, 0];

        var explode = 0;
        var explSlider = document.getElementById("explode");
        if (explSlider) explode = parseFloat(explSlider.value) * EXPL_FACTOR / 100.0;

        var movedDistPivot = _rotateXY(distPivot, proxPivot, flexAngle);

        for (var id in _parts) {
            if (!_parts.hasOwnProperty(id)) continue;
            var p = _parts[id];
            var name = p.name;
            var basePos = [p.pos[0] + p.exp[0] * explode,
                           p.pos[1] + p.exp[1] * explode,
                           p.pos[2] + p.exp[2] * explode];
            var baseRot = p.rotf || [0, 0, 0];
            var totalFlex = 0;

            if (PROXIMAL_FLEX_PARTS[name]) {
                basePos = _rotateXY(basePos, proxPivot, flexAngle);
                totalFlex += flexAngle;
            }
            if (DISTAL_FLEX_PARTS[name]) {
                basePos = _rotateXY(basePos, movedDistPivot, flexAngle);
                totalFlex += flexAngle;
            }

            try {
                _stlViewer.set_position(parseInt(id), basePos[0], basePos[1], basePos[2]);
                if (totalFlex !== 0) {
                    _stlViewer.set_rotation(parseInt(id), baseRot[0], baseRot[1], baseRot[2] + totalFlex);
                } else {
                    _stlViewer.set_rotation(parseInt(id), baseRot[0], baseRot[1], baseRot[2]);
                }
            } catch (e) {}
        }

        // Plug instances: distal pair (indices 2,3 = IDs 102,103) move with both hinges
        var plugExp = (_previewConfig && _previewConfig.explodeOffsets && _previewConfig.explodeOffsets["plug"]) || [0, 0, 1];
        for (var pid in _plugPositions) {
            if (!_plugPositions.hasOwnProperty(pid)) continue;
            var pp = _plugPositions[pid];
            var plugIdx = parseInt(pid) - PLUG_BASE_ID;
            var isDistal = (plugIdx >= 2);
            var zSign = pp[2] < 0 ? -1 : 1;
            var plugPos = [pp[0] + plugExp[0] * explode,
                           pp[1] + plugExp[1] * explode,
                           pp[2] + plugExp[2] * explode * zSign];
            var plugTotalFlex = 0;
            var pRot = _plugBaseRots[pid] || [0, 0, 0];

            if (isDistal) {
                plugPos = _rotateXY(plugPos, proxPivot, flexAngle);
                plugTotalFlex += flexAngle;
                plugPos = _rotateXY(plugPos, movedDistPivot, flexAngle);
                plugTotalFlex += flexAngle;
            }

            try {
                _stlViewer.set_position(parseInt(pid), plugPos[0], plugPos[1], plugPos[2]);
                if (plugTotalFlex !== 0) {
                    _stlViewer.set_rotation(parseInt(pid), pRot[0], pRot[1], pRot[2] + plugTotalFlex);
                }
            } catch (e) {}
        }
    }

    function setPlugVisibility(visible, partVisibility) {
        // Remove plug instances regardless; re-add them if visible
        for (var i = 0; i < 4; i++) { try { _stlViewer.remove_model(PLUG_BASE_ID + i); } catch (e) {} }
        _plugPositions = {};
        if (visible) {
            _respawnPlugInstances(partVisibility || {});
        }
    }

    // -------------------------------------------------------------------------
    // Resize handle — drag to change viewer height
    // -------------------------------------------------------------------------
    function initResizeHandle() {
        var handle = document.getElementById("viewer_resize_handle");
        var cont   = document.getElementById("stl_cont");
        if (!handle || !cont) return;

        var _dragging  = false;
        var _startY    = 0;
        var _startH    = 0;
        var MIN_H      = 160;
        var MAX_H      = window.innerHeight * 0.85;

        handle.addEventListener("mousedown", function (e) {
            _dragging = true;
            _startY   = e.clientY;
            _startH   = cont.offsetHeight;
            document.body.style.userSelect = "none";
            e.preventDefault();
        });

        document.addEventListener("mousemove", function (e) {
            if (!_dragging) return;
            var delta = e.clientY - _startY;
            var newH  = Math.min(Math.max(_startH + delta, MIN_H), MAX_H);
            cont.style.height = newH + "px";
        });

        document.addEventListener("mouseup", function () {
            if (_dragging) {
                _dragging = false;
                document.body.style.userSelect = "";
            }
        });
    }

    // -------------------------------------------------------------------------
    // Fullscreen — toggles the #wrap div into native fullscreen
    // -------------------------------------------------------------------------
    var _savedViewerHeight = "280px";

    function toggleFullscreen() {
        var wrap = document.getElementById("wrap");
        var cont = document.getElementById("stl_cont");
        if (!wrap) return;

        var fsEl = document.fullscreenElement || document.webkitFullscreenElement;
        if (fsEl) {
            (document.exitFullscreen || document.webkitExitFullscreen).call(document);
        } else {
            // Snapshot height NOW, before the fullscreen transition overwrites it
            if (cont) _savedViewerHeight = cont.offsetHeight + "px";
            var req = wrap.requestFullscreen || wrap.webkitRequestFullscreen;
            if (req) req.call(wrap);
        }
    }

    document.addEventListener("fullscreenchange", _onFullscreenChange);
    document.addEventListener("webkitfullscreenchange", _onFullscreenChange);
    function _onFullscreenChange() {
        var wrap = document.getElementById("wrap");
        var cont = document.getElementById("stl_cont");
        var btn  = document.getElementById("fs_btn");
        if (!wrap || !cont) return;
        var inFs = !!(document.fullscreenElement || document.webkitFullscreenElement);
        if (inFs) {
            cont.style.height = "100%";
            cont.style.width  = "100%";
            wrap.style.height = "100vh";
            if (btn) btn.textContent = "✕";
        } else {
            cont.style.height = _savedViewerHeight;
            cont.style.width  = "100%";
            wrap.style.height = "";
            if (btn) btn.textContent = "⛶";
        }
    }

    function getLastStlUrls() { return _lastStlUrls; }
    function getPartNameToId() { return _partNameToId; }
    function getStlViewer() { return _stlViewer; }

    return {
        init: init,
        setPartData: setPartData,
        addModel: addModel,
        remModels: remModels,
        updateFromStlUrls: updateFromStlUrls,
        applyPreviewConfig: applyPreviewConfig,
        slideChange: slideChange,
        flexChange: flexChange,
        setPlugVisibility: setPlugVisibility,
        setStatus: setStatus,
        getLastStlUrls: getLastStlUrls,
        getPartNameToId: getPartNameToId,
        getStlViewer: getStlViewer,
        toggleFullscreen: toggleFullscreen,
        initResizeHandle: initResizeHandle,
    };
})();
