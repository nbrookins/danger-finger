


//part = 3;
//cutaway = 0;

echo ("\n..........................................................\n");
echo ("\nDangerFinger: Nick Brookins");
echo ("\n..........................................................\n");
	
/* [Socket Fit Settings] */
//Very important for fit!  Diameter of the top of socket, roughly the diameter/width of the finger stump nearer the end.  You may want to print multiple sockets with different thciknesses, as this can vary depending on healing, and swelling, even throughout a single day.  
socket_circumference_distal = 51; //52.5
//SK; 50, 48, 52

//diameter of the bottom of socket, roughly the diameter/width of the finger stump bottom.  This and the other diameter can be the same, but I have better luck making the socket tighter at the top, for a firmer hold.
socket_circumference_proximal = 66;// 68 =>21.65
//SK: 17.5; 55, 55, 61

//Depth of the socket, roughly equates to the length of the finger stump to the start of the next knuckle  
socket_depth_top = 34;
//NB: 36
//SK: 31
socket_depth = socket_depth_top;
//Depth of the socket near the palm, typically shorter to account for flexing to a fist.  Should be smaller than socket_depth_top
socket_depth_bottom = 24.5;
//NB: 25
//SK: 23

//Deptch of the scallopped cutout on each side, to make room for webbing for the next finger.  Should be smaller than socket_depth_bottom.
socket_depth_scallop_left = 20;
socket_depth_scallop_right = 24;

/* [Finger Length Settings] */

//length of the overall tip section, including the tip cover, from hinge pin, to end.  Should be set to length of finger tip from mid-knuckle to end.
tip_length = 24.5;
//24.5

//length of the middle part, from pin to pin.  Should be roughly same as length from mid-first knuckle, to mid-second knuckle.
middle_section_length = 31;
//NB: 31
//additional height of the base section, which connects to the socket and has the first hinge.  Keep this low in order to have the base hinge as close to the finger remnant as possible.  Increase it if the knuckle needs to be extended in order to align with other fingers.

base_extra_length = .5;

//length of the back-of-hand linkage.  Some matter of preference, this should be less than the length of back-of-hand, from knuckles to wrist.  It also depends on how tight the bracelet it links to is around the wrist.
linkage_length = 62;

/* [Other adjustments] */
//Which form of sides to use for the middle section.  0 to print attached plastic bumpers, or 1 for seperate (rubber) bumpers
middle_sides = 1 ;//[0:Built-in sides, 1:Slots for rubber bumper]

//a split to make it easyier to get less-elastic bumper over the middle part.  negative for split on one side, positive for the other.
bumper_split = -.1;//[.1:Left Split, -.1:Right Split, 0:Solid Bumper]

//thickness of the rubber, for socket near top.  Again preference, thinner will be more flexible and streamlined, but with less strength and stability.
socket_thickness_top = 1.9;
socket_thickness_mid = 1.65;
//thickness of the rubber socket near bottom.  I like this to be thinner - allowing for more strength where the socket interfaces with the base, while having less bulk near my hand.
socket_thickness_bottom = 1.4;

//amount to taper the opening of socket for comfort
socket_taper = .7; 

//width of the scallops as ratio of socket width 
socket_width_scallop = .75;

//Advanced: diameter of middle section,  have'nt yet tested different values here.  minimum of 15 for tunnels to fit.
middle_diameter = 15; //15
//TODO: 15

//Advanced: width of middle segment (not counting bumper), generally the width between the hinges.  Be careful with this one.
middle_width = 8; 
//TODO: 8.5

//Advanced: width at the base of the rubber tip cover, compared to middle section.  typically negative.
tip_width = -1.5;  
//TODO: -1.5

//Advanced: the percentage of the tip cover length which the fingernail covers
tip_fingernail_ratio = .47;
//TODO: .43

//Advanced: width of the linkage
linkage_width = 7;
//TODO: 8

//Diameter of the clearance hole around the hinge pin nuts
hinge_pin_clearance = 6;
//TODO: 6.75

//Advanced: hinge inner diameter
hinge_diameter = 9;

socket_interface_length=4.25;
