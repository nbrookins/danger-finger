#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2026 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0'''
from functools import reduce
from operator import add
from solid2 import *
from danger.constants import *
from danger.Params import *
from danger.tools import *
from danger.finger_params import *

'''
on init, populate list of parts, based on fingerpart?
use build to generate scad, following params binding.
allows external code to insert parts prior to build.
each part has print and preview offsets

part functions build and then return their parts
finger.build calls build on all parts to poulate scad,
or the part can be individually 'built'

a built part can be provided to the renderer,
and/or the scad can be saved to a .scad file

[make internal functions for modeling parts,
and assign them to the part object's 'generate' function]

add render function to finger, vs external mgmt?
'''
# ********************************** The danger finger *************************************
class DangerFingerBase(DangerFingerParams):
    ''' The actual finger model '''
    # ************************************* control params *****************************************
    def __init__(self):
        self._models = {}
        self._parts = {}
        self._animate_factor = 1

    def scad_header(self, rq):
        ''' calculate header for top of scad file'''
        if rq == RenderQuality.NONE: return ""
        return "$fa = %s; \n$fs = %s;\n" % (self.fa_[rq], self.fs_[rq])

    def _prop_offset(self, offs, f, func=lambda v: v):
        ''' calculate offsets by factor for animation, etc '''
        new_offs = {o: (func(offs[o][0]) * f, func(offs[o][1]) * f, func(offs[o][2]) * f) if isinstance(offs[o][0], (int, float)) else \
            [(func(v[0]) * f, func(v[1]) * f, func(v[2]) * f) for v in offs[o]] for o in offs}
        return new_offs

    def _part_composite(self, part):
        ''' combine models into a preview '''
        mod = None
        offsets = self.translate_offsets[str(part)] if (str(part) in self.translate_offsets) else None
        rotates = self.rotate_offsets[str(part)] if (str(part) in self.rotate_offsets) else None

        for name, model in self.parts.items():
            fp = FingerPart.from_str(name)
            if (not part & fp or bin(fp.value).count('1')>1): continue
            temp = model if iterable(model) else [model]
            if (not temp or temp[0]==None): continue

            if self.preview_cut:
                temp = [x - cube((30, 200, 30)).translate((0, -75, 0)).color("gray") for _, x in enumerate(temp, 0)]
            if (self.preview_rotate and rotates and name in rotates):
                temp = [rotate(rotates[name][i])(x) for i, x in enumerate(temp, 0)]
            if (offsets and name in offsets):
                print ("found offsets; " + str(part) + ", " + name)
                temp = [translate(offsets[name][i])(x) if offsets[name][i] != (0, 0, 0) else x for i, x in enumerate(temp, 0)]
            # tip rotate in preview mode
            if (self.preview_rotate and str(part)=="all" and name.startswith("tip") and rotates and name in rotates):
                temp = [translate((0,-self.intermediate_length/2,0))(x) for i, x in enumerate(temp,0)]
                temp = [rotate(rotates[name][i])(x) for i, x in enumerate(temp, 0)]
                temp = [translate((2,self.intermediate_length*.88,0))(x) for i, x in enumerate(temp,0)]
            mod = flatten(temp) if mod is None else mod + flatten(temp)
        if (mod):
            mod.part = str(part)
            self.models[mod.part] = mod
        return mod

    def cut_model(self):
        ''' model to cut from preview for cutaway previwe'''
        return cube((30, 200, 30)).translate((0, -75, 0))#.debug()

    def part(self, fingerpart, transforms=False):
        name = str.lower(str(fingerpart.name) if isinstance(fingerpart, FingerPart) else str(fingerpart))
        part_name = "part_%s" % name
        print(" Looking for ", part_name)
        #check for an available method for the part
        if not hasattr(self, part_name): 
            return self._part_composite(fingerpart)
        else:
            return getattr(self, part_name)()

    def build(self):#, header=False, models = {}):
        ''' build all models and render their scad code.  populates .models - this is very fast '''
        # walk possible parts looking for methods to build them and populate self.models'''
        for _, pv in FingerPart.__members__.items():
            name = str.lower(str(pv.name) if isinstance(pv, FingerPart) else str(pv))
            self._parts[name] = self.part(pv)
            offsets = self.translate_offsets[name] if (name in self.translate_offsets) else None
            rotates = self.rotate_offsets[name] if (name in self.rotate_offsets) else None
            
            #transforms
            temp = self._parts[name]#self.part(pv)
            if temp == None: continue
            #if self.preview_cut: temp = temp - cube((30, 200, 30)).translate((0, -75, 0))
            if (rotates and not isinstance(rotates, dict)): 
                temp = rotate(rotates)(temp)#(x) for i, x in enumerate(temp, 0)]
            if (offsets and not isinstance(offsets, dict)): 
                temp = translate(offsets)(temp) if offsets != (0, 0, 0) else temp
            temp = flatten(temp) #if mod is None else mod + flatten(temp)
            self._models[name] = temp.render() if self.scad_render else temp

        for name, model in self.models.items():
            obj = flatten(model)
            if obj == None: continue
            header = self.scad_header(self.render_quality)#self.preview_quality if fp == FingerPart.PREVIEW else "" if not header else
            set_list_attr(model, "part", name) #TODO - pull to post-loop?
            code = scad_render(obj, file_header=header)
            set_list_attr(model, "scad", code)

def rcylinder(r, h, rnd=0, center=False):
    ''' primitive for a cylinder with rounded edges'''
    if rnd == 0: return cylinder(r=r, h=h, center=center)
    mod_cyl = translate((0, 0, -h/2 if center else 0))( \
        rotate_extrude(convexity=1)(offset(r=rnd)(offset(delta=-rnd)(square((r, h)) + square((rnd, h))))))
    return mod_cyl

def flaredcyl(r=0, h=0, fr=0, fh=0):
    return rotate_extrude()(
        offset(r = -fr)(offset(r = fr)(
            square([r, h]) +\
            square([r + fr, fh]))))

def rcube(size, rnd=0, center=True):
    ''' primitive for a cube with rounded edges on 4 sides '''
    if rnd == 0: return cube(size, center=center)
    round_ratio = (1-rnd) * 1.1 + 0.5
    #TODO fix rounded cube for detent use-case
    c = cube(size, center=center) * resize((size[0]*round_ratio, 0, 0))(cylinder(h=size[2], d=size[1]*round_ratio, center=center))
    return c

def rcubecyl(h, w, l, t, rnd=None, rnd1=None, rnd2=None, center=True):
    """Rounded cuboid-cylinder hybrid.
    Usage:
      - `rnd` applies equal rounding to both halves.
      - `rnd1` and/or `rnd2` override per-side rounding (left/right).
    If a side's rounding is 0 it will use a plain `cylinder` for that half."""
    cy = cylinder(r=0, h=0)  # Empty placeholder
    if rnd1 is None and rnd2 is None:
        cy = rcylinder(r=w, h=h, rnd=rnd, center=center).resizeX(l)#.debug()#.translate((0, 0, half_h / 2.0))
    else:
        # Resolve rounding values with precedence: explicit rnd1/rnd2 override rnd
        left_rnd = rnd1 if rnd1 is not None else (rnd or 0)
        right_rnd = rnd2 if rnd2 is not None else (rnd if rnd is not None else left_rnd)

        # Build left/right halves using half the cylinder height and translate them
        # so they abut at the center. This lets one side be rounded and the other
        # be plain (or differently rounded).
        half_h = h / 2.0
        left_r = max(0, w - left_rnd)
        cy_left = rcylinder(r=left_r, h=half_h, rnd=left_rnd, center=center).resizeX(l).translate((0, 0, half_h / 2.0))

        right_r = max(0, w - right_rnd)
        if right_rnd > 0:
            cy_right = rcylinder(r=right_r, h=half_h, rnd=right_rnd, center=center).resizeX(l).translate((0, 0, -half_h / 2.0))
        else:
            cy_right = cylinder(r=right_r, h=half_h, center=center).resizeX(l).translate((0, 0, -half_h / 2.0))
        cy = cy_left + cy_right  
    # Compose using scaled translated anchors (shifted in Z to match halves)
    # anchor_left = cy_left.scaleX(.5).scaleY(1.1).translateX(t / 2.0)
    # anchor_right = cy_right.scaleX(.5).scaleY(1.1).translateX(-t / 2.0)
    # hub = hull()(anchor_left, anchor_right, cy_left, cy_right)
    anchor1 = cy.scaleX(.5).translateX(t / 2.0)#.scaleY(1.1)
    anchor2 = cy.scaleX(.5).translateX(-t / 2.0)#.scaleY(1.1)
    hub = hull()(anchor1, anchor2, cy)

    return hub.rotate((90, 0, 0))

def trim(x=0, y=0, z=0, center=True, offset=(0, 0, 0)):
    """Return a transform function that trims an object by intersecting it with a cube.

    For any axis where the value is non-zero, the cube size on that axis will be
    the absolute value provided. For axes set to 0 the axis is left effectively
    unbounded by using a very large size so the intersection does not clip it.

    Parameters:
    - x, y, z: dimensions of the cutting cube
    - center: whether the cube is centered (default True)
    - offset: optional (ox, oy, oz) tuple to translate the cutting cube

    Usage: `trim(x=10)(obj)` — similar to `rotate(...)`/`translate(...)` style.
           `trim(x=10, offset=(5, 0, 0))(obj)` — offsets the cube by 5 in X.
    """
    BIG = 10000.0
    sx = abs(x) if x != 0 else BIG
    sy = abs(y) if y != 0 else BIG
    sz = abs(z) if z != 0 else BIG
    cutting_cube = cube((sx, sy, sz), center=center)

    # Apply offset if provided
    if offset != (0, 0, 0):
        cutting_cube = cutting_cube.translate(offset)

    def _trim(obj):
        return intersection()(obj, cutting_cube)

    return _trim

# Allow method-style usage `obj.trim((x,y,z))` by patching OpenSCADObject if available.
try:
    from solid2.core.object_base.object_base_impl import OpenSCADObject

    def _open_scad_trim(self, dims, offset=(0, 0, 0)):
        """Method wrapper enabling `obj.trim((x,y,z))` or `obj.trim((x,y,z), offset)`.

        Accepts a 3-tuple/list `(x,y,z)` or a single numeric value (interpreted as x).
        Optional `offset` tuple offsets the cutting cube.
        """
        if isinstance(dims, (list, tuple)):
            if len(dims) == 3:
                xval, yval, zval = dims
            else:
                raise ValueError("trim expects a 3-tuple/list or numeric x value")
        elif isinstance(dims, (int, float)):
            xval, yval, zval = dims, 0, 0
        else:
            raise TypeError(f"Unsupported trim argument: {type(dims)}")
        return trim(xval, yval, zval, offset=offset)(self)

    OpenSCADObject.trim = _open_scad_trim
except Exception:
    # If solid2 internals differ, silently skip method patching.
    pass

def get_adjusted_spacing(char, base_spacing):
    """Returns adjusted spacing based on character width heuristics."""
    # Convert char to lowercase for dictionary lookup if needed,
    # or handle case-sensitive if 'I' != 'i' spacing is needed.
    adjustment = WIDTH_ADJUSTMENTS.get(char, 1.0) # Default to 1.0 (no change)
    return base_spacing * adjustment

def circular_text(txt, radius, size, thickness, spacing, rot, reverse=False):
        """ Generates OpenSCAD code for text wrapped around a circle using solidpython."""
        scad_objects = []
    # Calculate the total required angle dynamically first
        total_angle_needed = sum(get_adjusted_spacing(c, spacing) for c in txt)
        # We need to track the current angle placement as we iterate
        current_angle = (total_angle_needed * 1 if reverse else -1) / 2.0 # Start centered
        for char in txt:
            char_spacing = get_adjusted_spacing(char, spacing)
            #char_spacing = spacing
            current_angle = current_angle + (char_spacing / 2.0 * 1 if reverse else -1)
            angle = current_angle
            current_angle = current_angle + (char_spacing / 2.0 * 1 if reverse else -1)

            char_2d = text(char, size=size, halign="center", valign="center")
            char_3d = linear_extrude(height=thickness)(char_2d)
            oriented_char_3d = rotate(rot)(char_3d)
            # Position and orient the character
            positioned_char = rotate([0, 0, angle * (-1 if reverse else 1)])(
                                translate([0, radius, 0])(oriented_char_3d))
            scad_objects.append(positioned_char)
        return union()(scad_objects).debug()

