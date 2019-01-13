
// Knick's finger v3.71
// Copyright 2014-2016 Nicholas Brookins and Danger Creations, LLC
// http://dangercreations.com/prosthetics
// http://www.thingiverse.com/thing:1340624
//
// Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0  https://creativecommons.org/licenses/by-nc-sa/4.0/
// Source code licensed under Apache 2.0: https://www.apache.org/licenses/LICENSE-2.0

/* [Socket Fit Settings] */
//Very important for fit!  Diameter of the top of socket, roughly the diameter/width of the finger stump nearer the end.  You may want to print multiple sockets with different thciknesses, as this can vary depending on healing, and swelling, even throughout a single day.
socket_circumference_distal = 54.0;
//NB 52 ->

//diameter of the bottom of socket, roughly the diameter/width of the finger stump bottom.  This and the other diameter can be the same, but I have better luck making the socket tighter at the top, for a firmer hold.
socket_circumference_proximal = 65.0;
//NB 61 ->

//Depth of the socket, roughly equates to the length of the finger stump to the start of the next knuckle
socket_depth_top = 36;

socket_depth = socket_depth_top;
//Depth of the socket near the palm, typically shorter to account for flexing to a fist.  Should be smaller than socket_depth_top
socket_depth_bottom = 27;

//Deptch of the scallopped cutout on each side, to make room for webbing for the next finger.  Should be smaller than socket_depth_bottom.
socket_depth_scallop_left = 22;
socket_depth_scallop_right = 26;

/* [Finger Length Settings] */
//length of the overall tip section, including the tip cover, from hinge pin, to end.  Should be set to length of finger tip from mid-knuckle to end.
tip_length = 25.5;

//length of the middle part, from pin to pin.  Should be roughly same as length from mid-first knuckle, to mid-second knuckle.
middle_section_length = 32;

//additional height of the base section, which connects to the socket and has the first hinge.  Keep this low in order to have the base hinge as close to the finger remnant as possible.  Increase it if the knuckle needs to be extended in order to align with other fingers.
base_extra_length = -0.75;
base_tendon_offset = -0.25;
//optional breather hole in base
base_breather_diameter = 3.75;

 //Advanced: diameter of middle section,  have'nt yet tested different values here.  minimum of 15 for tunnels to fit.
middle_diameter = 13.50; //15

//length of the back-of-hand linkage.  Some matter of preference, this should be less than the length of back-of-hand, from knuckles to wrist.  It also depends on how tight the bracelet it links to is around the wrist.
linkage_length = 70;

/* [Other adjustments] */
//Which form of sides to use for the middle section.  0 to print attached plastic bumpers, or 1 for seperate (rubber) bumpers
middle_sides = 1 ;//[0:Built-in sides, 1:Slots for rubber bumper]

//thickness of the rubber, for socket near top.  Again preference, thinner will be more flexible and streamlined, but with less strength and stability.
socket_thickness_top = 2.0;
socket_thickness_mid = 1.8;
//thickness of the rubber socket near bottom.  I like this to be thinner - allowing for more strength where the socket interfaces with the base, while having less bulk near my hand.
socket_thickness_bottom = 1.4;

socket_ridge_depth = 0.2;
socket_ridge_spacing = 0.6;

//amount to taper the opening of socket for comfort
socket_taper = .7;

//width of the scallops as ratio of socket width
socket_width_scallop = .75;

/* [Advanced Clearances] */
//Advanced: clearance between hinge and middle section on sides
hinge_side_clearance = .35;

//Advanced: extra clearance for the hinge plugs, or negative to make them slightly bigger for a pressure fit
hinge_plug_clearance = 0.1;
//Advanced: radius of the hinge pin/axle .  On my printer R 1.06 works perfect for a 2mm diameter shaft.
hinge_pin_radius = 1.08;

//Advanced: radius of the elastic and tendon tunnels
tunnel_radius = 1.1;

//Advanced: radius of set screws on tensioner block.  set to 0 to disable tensioner
tip_tensioner_screw_radius = .94;

//radius of set screws on base.  set to 0 to disable tensioner
base_tensioner_screw_radius = 0;
base_tensioner_flare = 1.5;

//cut a hole into the side of the linkage, great for a set screw
linkage_angle_hole_radius = 0;

//radius of the tendon string hole
linkage_hole_radius = 1.25; //1.44;

//Clearance between socket and base.  -.5 for Ninja flex and sloopy printing to +.5 for firm tpu and accurate
socket_clearance = -0.25;
socket_vertical_clearance = .1;

socket_interface_length=5;

/* [Other Advanced] */
//Advanced: hinge inner diameter
hinge_diameter = 8.2;

//Diameter of the clearance hole around the hinge pin nuts
hinge_plug_diameter = 6.5;
//TODO: 6.75
//Advanced: thickness of the hinge plugs
hinge_plug_thickness = 1.1;
//TODO: 1.8

//Advanced: radius of an accessory hole from the tip cover end, great for LEDs and lasers :)
tip_accessory_radius = 0;

//Advanced: width of middle segment (not counting bumper), generally the width between the hinges.  Be careful with this one.
middle_width = 8.0;

//Advanced: width at the base of the rubber tip cover, compared to middle section.  typically negative.
tip_width = -4.0;

//Advanced: the percentage of the tip cover length which the fingernail covers
tip_fingernail_ratio = .48;
//TODO: .43

//Advanced: width of the linkage
linkage_width = 6.75;
//TODO: 8
slot_len = 9.0;
slot_spacing = 2.65;
slot_width = linkage_width*.18;

//Advanced: height of the linkage
linkage_height = 4.25;
//advanced, height of the hook
linkage_end2_height = 6.8;
//advanced, length of the hook
linkage_end2_length = 12.25;

//offset from end 1
linkage_angle_hole_offset = 4.5;

/* [Hidden] */

//advanced, length of the hole
linkage_hole_length = linkage_length*0.8;//20;
//advanced, radius of a hole through the entire linkage
linkage_holethrough_radius = 0;//.75;

//optional angle modifier
linkage_angle_hole_angle = 15;
//how much rounding to apply to end 1
linkage_end1_round = 1.2;
//how much rounding to apply to end 2
linkage_end2_round = 1.2;

//advanced, width of the hook
linkage_end2_width = 5.5;
//advanced, thickness of the hook
linkage_end2_thickness = 2.3;
//advanced, offset of the hook
linkage_end2_offset = -0.2;

//which end style to use for end1
linkage_end1 = 2; //[0:Plain,1:Hole,3:Loop, 5:Hook ]
//which end style to use for end2
linkage_end2 = 5; //[0:Plain,1:Hole,3:Loop,5:Hook ]

linkage_hookopening_offset = -0.28 *1;
linkage_hookvertical_offset = -0.3 *1;
linkage_bottom_trim =.12;

hinge_bend_padding = .25 ;

//vertical clearance for the curve between middle section and hinges, where tendon/elastic pass
hinge_end_clearance = 1;

base_tunnel_height=.25;

//how much curved bulge to put on the plugs
hinge_plug_bulge = .2;

bumper_length_round = 2.0;

//multiplier for rounding of the hinges.  larger numbers make for less rounding. set to 0 to disable.
hinge_rounding=5.65;//hinge_rounding = 3.0; //TODO

//advanced, the clearance between rubber tip and the tip core
tip_post_clearance =.15;
//Advanced: width of the base section, beyond the middle_diameter
base_width = 4.75;
//vertical clearance for the curve between middle section and hinges, where tendon/elastic pass
//the thickness of the hinge in between the middle section and nut.
hinge_thickness = 1.4;
//Depth of the indent in the center of the middle part of hinge, allowing clearnce for the elastic or tendon
hinge_indent_depth = 0.6;

//clearance for the tunnels to the side
tunnel_clearance = .7;

tip_clearance = .15;
tip_post_height = 1.5;
tip_ridge_height = 1.5;

tensioner_nut_diam = 3.9 + .99;
tensioner_nut_thickness = 1.85;
tip_tensioner_height = tensioner_nut_diam - 0.5;
tensioner_bolt_diam = 1.95;
tip_tensioner_width = tensioner_nut_thickness * 2.0;
tip_tensioner_length = tensioner_nut_diam * 1.3;

fprint_ridge_thickness = 0.6;
fprint_ridge_offset = 1.1;
fprint_ridge_height = 1;
fprint_style = 1; //[0:disable, 1:lines, 2:concentric]

//include extra clearance for tendon string
socket_string_clearance = 0.0;//.5;

//how thick to make the built-in washers on the hinges
washer_depth_outside = .5;
//how wide to make the washers
washer_radius = 0.5;

socket_catch_height =  2;
socket_post_height =  2;

//stump indent for sphere size
stump_indent = 12.0;//socket_post_diameter*.9;
//stump indent offset for sphere
stump_indent_offset = 5.4;//1.5;

tip_fingernail_rot = 1 * -3;
tip_fingernail_offset = 1 * 2.2;
tip_cuticle_rot = 1* 60;

socket_interface_clearance_top = 0.25;
socket_interface_taper = 1.0;
socket_interface_clearance = 1.0;

socket_slot_width = 1.5;
socket_slot_depth_top = 1.0;
socket_slot_depth_bottom = 2.0;

hinge_plug_ridge_height = 0.5;
hinge_plug_side_clearance = 0.25;

 middle_diameter_width = middle_width + hinge_side_clearance*2 + hinge_thickness*6;//15

//width of the post ridge
tip_ridge_width = (middle_diameter_width + tip_width) - 2.5; //hack constant
//width of the post conencting tip to tip cover
tip_post_width = tip_ridge_width - 1.75;
