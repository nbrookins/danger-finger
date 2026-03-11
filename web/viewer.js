// viewer.js — stl_viewer instance, parts state, model management, explode, plug instances.
// Depends on: stl_viewer.min.js being loaded first.

var Viewer = (function () {
    var _stlViewer = null;
    var _parts = {};           // id -> {name, pos, exp, rotf}
    var _plugPositions = {};   // id -> [x,y,z]  (IDs 100-103)
    var _lastStlUrls = {};     // partName -> url
    var _previewConfig = null;
    var _partNameToId = {};
    var _baseurl = "";
    var _onModLoaded = null;   // callback when any model loads
    var _onStatus = null;      // callback(msg, isError)
    var PLUG_BASE_ID = 100;
    var EXPL_FACTOR = 25;

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
        // Reapply current explode state
        slideChange();
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
        try { _stlViewer.add_model(opts); } catch (e) { console.warn("addModel error", id, e); }
    }

    function remModels(ids) {
        ids.forEach(function (id) {
            try { _stlViewer.remove_model(id); } catch (e) {}
        });
    }

    function updateFromStlUrls(stlUrls, partVisibility) {
        // Remove all current models
        var allIds = Object.keys(_parts).map(Number);
        allIds.forEach(function (id) { try { _stlViewer.remove_model(id); } catch (e) {} });
        for (var i = 0; i < 4; i++) { try { _stlViewer.remove_model(PLUG_BASE_ID + i); } catch (e) {} }

        _lastStlUrls = {};
        for (var partName in stlUrls) {
            if (!stlUrls.hasOwnProperty(partName)) continue;
            var id = _partNameToId[partName];
            if (id === undefined) continue;
            var url = _baseurl + stlUrls[partName];
            _lastStlUrls[partName] = url;
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

        _previewConfig.plugInstances.forEach(function (inst, i) {
            var instId = PLUG_BASE_ID + i;
            _plugPositions[instId] = inst.position;
            var opts = {
                id: instId,
                filename: plugUrl,
                rotationx: degtorad(inst.rotation[0]),
                rotationy: degtorad(inst.rotation[1]),
                rotationz: degtorad(inst.rotation[2])
            };
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

        // Plug instances: explode along Y axis away from middle (Y=0 = proximal hinge)
        for (var pid in _plugPositions) {
            if (!_plugPositions.hasOwnProperty(pid)) continue;
            var pp = _plugPositions[pid];
            // Plugs at Y=0 (proximal) move proximally; plugs at Y>0 (distal) move distally
            var plugExpY = pp[1] > 8 ? 1 : -0.5;
            try {
                _stlViewer.set_position(parseInt(pid),
                    pp[0],
                    pp[1] + plugExpY * explode,
                    pp[2]);
            } catch (e) {}
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
        setStatus: setStatus,
        getLastStlUrls: getLastStlUrls,
        getPartNameToId: getPartNameToId,
        getStlViewer: getStlViewer,
    };
})();
