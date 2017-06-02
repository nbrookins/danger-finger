
// Knick's finger v3.71
// Copyright 2014-2016 Nicholas Brookins and Danger Creations, LLC
// http://dangercreations.com/prosthetics
// http://www.thingiverse.com/thing:1340624
//
// Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0
// https://creativecommons.org/licenses/by-nc-sa/4.0/
// Source code licensed under Apache 2.0:
// https://www.apache.org/licenses/LICENSE-2.0
//
// Updates:
// improved socket and added new variables to match the measurement guide
// fixed the plugs, which were not generating due to a configurator bug I had to workaround
// fixed many variables and hid some that shouldn't be changed often
// added tensioners, carved inside of tip cover, made wire holes, improved some parametrics, added post clearance
// improved stump indent and scallop
//Constants//
ver = 3.71;
pi = 3.14159 * 1;

/* [General Parameters] */
//TODO batch = //[0,1,2]
//Choose which part to create.  Best practice is to set all settings, and then generate each part, one by one.  The middle and bumper sections are only used with 2 knuckles.
part = 8; //[ 6:Tip Cover, 5:Tip Knuckle, 4:Middle Segment, 7:Middle Bumper, 3:Base Knuckle, 8:Finger Socket, 9:Knuckle Plugs, 10: Wrist Linkage]  
	
//How many knuckles/hinges to create.  In single knuckle mode, do not create the middle or bumper parts, they are not used and will cause an error.
knuckles = 2; // [1,2]

/* [Preview Settings] */
//Enable to preview all parts together!  KEEP THIS OFF in order to create individual printable parts.
preview = 0; //[0:Print Mode, 1:Preview Mode (dont print!)]
 
// rotate the base and tip parts, to see how the hinges interact with the middle section.  Only relevant when previewing.  0 for straight, and up to 95 for fully bent.
rotatetest = 0; //[0:95]

//explode parts apart to see them individually better.  Only relevant when previewing.
explode = 0; //[0,1] 
make_cutaway = 1*  0;

//echo (cutawy);

//Advanced: build parts more crudely, but much more quickly - for twiddling.  print mode automatically turns this off
fast = 1*  0;
	
/* [Socket Fit Settings] */
//Very important for fit!  Diameter of the top of socket, roughly the diameter/width of the finger stump nearer the end.  You may want to print multiple sockets with different thciknesses, as this can vary depending on healing, and swelling, even throughout a single day.  
socket_circumference_distal = 52;
//SK; 50, 48, 52

//diameter of the bottom of socket, roughly the diameter/width of the finger stump bottom.  This and the other diameter can be the same, but I have better luck making the socket tighter at the top, for a firmer hold.
socket_circumference_proximal = 61;
//SK: 17.5; 55, 55, 61

//Depth of the socket, roughly equates to the length of the finger stump to the start of the next knuckle  
socket_depth_top = 28;
//NB: 36
//SK: 31
echo ("..........................................................\n");
echo ("DangerCreations Finger v", ver);
echo ("Preview Mode: Full");
echo ("..........................................................\n");
socket_depth = socket_depth_top;
//Depth of the socket near the palm, typically shorter to account for flexing to a fist.  Should be smaller than socket_depth_top
socket_depth_bottom = 20;
//NB: 25
//SK: 23

//Deptch of the scallopped cutout on each side, to make room for webbing for the next finger.  Should be smaller than socket_depth_bottom.
socket_depth_scallop_left = 18;
socket_depth_scallop_right = 18;
//socket_depth_scallop = 21;
//NB: 21
//SK: 20

/* [Finger Length Settings] */

//length of the overall tip section, including the tip cover, from hinge pin, to end.  Should be set to length of finger tip from mid-knuckle to end.
tip_length = 22;
//24.5

//length of the middle part, from pin to pin.  Should be roughly same as length from mid-first knuckle, to mid-second knuckle.
middle_section_length = 26;
//NB: 31
//additional height of the base section, which connects to the socket and has the first hinge.  Keep this low in order to have the base hinge as close to the finger remnant as possible.  Increase it if the knuckle needs to be extended in order to align with other fingers.

base_extra_length = .5;

//length of the back-of-hand linkage.  Some matter of preference, this should be less than the length of back-of-hand, from knuckles to wrist.  It also depends on how tight the bracelet it links to is around the wrist.
linkage_length = 58;

/* [Other adjustments] */
//Which form of sides to use for the middle section.  0 to print attached plastic bumpers, or 1 for seperate (rubber) bumpers
middle_sides = 1 ;//[0:Built-in sides, 1:Slots for rubber bumper]

//a split to make it easyier to get less-elastic bumper over the middle part.  negative for split on one side, positive for the other.
bumper_split = -.1;//[.1:Left Split, -.1:Right Split, 0:Solid Bumper]

//thickness of the rubber, for socket near top.  Again preference, thinner will be more flexible and streamlined, but with less strength and stability.
socket_thickness_top = 2.1;
socket_thickness_mid = 1.7;
//thickness of the rubber socket near bottom.  I like this to be thinner - allowing for more strength where the socket interfaces with the base, while having less bulk near my hand.
socket_thickness_bottom = 1.4;

socket_ridge_depth =.2;
socket_ridge_spacing =.85;

//amount to taper the opening of socket for comfort
socket_taper = .7; 

//width of the scallops as ratio of socket width 
socket_width_scallop = .75;

/* [Advanced Clearances] */
//Advanced: clearance between hinge and middle section on sides
hinge_side_clearance = .35;
	
//Advanced: extra clearance for the hinge plugs, or negative to make them slightly bigger for a pressure fit
hinge_plug_clearance = -0.55;
//Advanced: radius of the hinge pin/axle .  On my printer R 1.06 works perfect for a 2mm diameter shaft.
hinge_pin_radius = 1.08;

//Advanced: radius of the elastic and tendon tunnels
tunnel_radius = 1.1;

//Advanced: radius of set screws on tensioner block.  set to 0 to disable tensioner 
tip_tensioner_screw_radius = .94;

//radius of set screws on base.  set to 0 to disable tensioner 
base_tensioner_screw_radius = 1.01;
//.94;

//cut a hole into the side of the linkage, great for a set screw
linkage_angle_hole_radius = 1.01;
//.94;

//radius of the tendon string hole
linkage_hole_radius = 1.1; //1.44;

//Clearance between socket and base.  -.5 for Ninja flex and sloopy printing to +.5 for firm tpu and accurate
socket_clearance = -0.25;
socket_vertical_clearance = .1;

socket_interface_length=5;

/* [Other Advanced] */
//Advanced: hinge inner diameter
hinge_diameter = 8.5;
//TODO: 10

//Diameter of the clearance hole around the hinge pin nuts
//hinge_pin_clearance = 6.75;

//Diameter of the clearance hole around the hinge pin nuts
hinge_pin_clearance = 5.5;
//TODO: 6.75
//Advanced: thickness of the hinge plugs 
hinge_plug_thickness = 1.1;
//TODO: 1.8

//Advanced: thickness of the hole in the hinge plug.  Makes room for pin and makes the plug flexible
hinge_nut_thickness = hinge_plug_thickness *.5;

//Advanced: radius of an accessory hole from the tip cover end, great for LEDs and lasers :)
tip_accessory_radius = 0;

//Advanced: diameter of middle section,  have'nt yet tested different values here.  minimum of 15 for tunnels to fit.
middle_diameter = 14.5; //15
//TODO: 15

//Advanced: width of middle segment (not counting bumper), generally the width between the hinges.  Be careful with this one.
middle_width = 7.5; 
//TODO: 8.5

//Advanced: width at the base of the rubber tip cover, compared to middle section.  typically negative.
tip_width = -1.8;  
//TODO: -1.5

//Advanced: the percentage of the tip cover length which the fingernail covers
tip_fingernail_ratio = .44;
//TODO: .43

//Advanced: width of the linkage
linkage_width = 6;
//TODO: 8

//Advanced: height of the linkage
linkage_height = 4.3;
//advanced, height of the hook 
linkage_end2_height = 6;
//advanced, length of the hook
linkage_end2_length = 12;

//offset from end 1
linkage_angle_hole_offset = 3;

/* [Hidden] */
//Advanced: width of the base section, beyond the middle_diameter
base_width = 3; 

//advanced, length of the hole 
linkage_hole_length = linkage_length*0.9;//20;
//advanced, radius of a hole through the entire linkage
linkage_holethrough_radius = 0;//.75;

//optional angle modifier
linkage_angle_hole_angle = 0;
//how much rounding to apply to end 1
linkage_end1_round = 1;
//how much rounding to apply to end 2
linkage_end2_round = 1;

//advanced, width of the hook 
linkage_end2_width = 5.5;
//advanced, thickness of the hook 
linkage_end2_thickness = 2;
//advanced, offset of the hook 
linkage_end2_offset = 0.25;

//which end style to use for end1
linkage_end1 = 1; //[0:Plain,1:Hole,3:Loop, 5:Hook ]
//which end style to use for end2
linkage_end2 = 5; //[0:Plain,1:Hole,3:Loop,5:Hook ]

linkage_hookopening_offset = .25 *1;
linkage_hookvertical_offset = -.4 *1;
	
//extra width of the hinges (and bumper) beyond middle diameter, which affects overall finger width
hinge_width = -0.5; 

hinge_bend_padding = .25 ;

//Advanced: width of the nut for the plug cutout
hinge_nut_width = 4.0;//3; //4.05
//TODO 4.5

//use 6 for a hex nut, with about 5mm diameter for an M2.
hinge_nut_sides = 80 ;
	
//vertical clearance for the curve between middle section and hinges, where tendon/elastic pass
hinge_end_clearance = 1;

base_tunnel_height=.25;	
	
//how much curved bulge to put on the plugs
hinge_plug_bulge = .5;
	
//multiplier for rounding of the hinges.  larger numbers make for less rounding. set to 0 to disable.
hinge_rounding = 1.4;

//advanced, the clearance between rubber tip and the tip core
tip_post_clearance =.15;

//vertical clearance for the curve between middle section and hinges, where tendon/elastic pass
//the thickness of the hinge in between the middle section and nut.  
hinge_offset = 1 ;
//Depth of the indent in the center of the middle part of hinge, allowing clearnce for the elastic or tendon
hinge_indent_depth = .65;

//clearance for the tunnels to the side
tunnel_clearance = .75;

middle_tensioner_screw_radius = 0;//.9;

//width of the post conencting tip to tip cover
tip_post_width = 8.7;
//TODO: 9.75
//width of the post ridge
tip_ridge_width = 10;
//TODO: 11

tip_clearance = .5;
tip_post_height = 1.5;
tip_ridge_height = 1.5;

tip_tensioner_height =  3.5;//2.65;

fprint_ridge_thickness = 0.4;
fprint_ridge_offset = 1;
fprint_ridge_height = 1;
fprint_style = 1; //[0:disable, 1:lines, 2:concentric]

//include extra clearance for tendon string
socket_string_clearance = 0.0;//.5;

washer_depth_inside = 0;
//how thick to make the built-in washers on the hinges
washer_depth_outside = .4;
//how wide to make the washers
washer_radius = 0.7;

socket_catch_height =  2;
socket_post_height =  2;
             
//socket_ridgehold = 2;
bumper_pegs = 2 ;

tip_ridge_flat = 1.5;

//stump indent for sphere size
stump_indent = 8.25;//socket_post_diameter*.9;
//stump indent offset for sphere
stump_indent_offset = 6.0;//1.5;

tip_fingernail_rot = 1 * -3;
tip_fingernail_offset = 1 * 2.2;
tip_cuticle_rot = 1* 60;

//config_nbrookins.scad
config = "config_nbrookins.scad";
include <config_nbrookins.scad>;

// *********** Auto-calculated global variables ************
middle_length = middle_section_length - hinge_diameter;
tip_tensioner_width = tunnel_radius*3 +.1;
socket_width_top = socket_circumference_distal / pi;
//NB: 17
socket_width_bottom = socket_circumference_proximal / pi;
//NB: 22
socket_ridge_number = ceil(socket_depth/socket_ridge_spacing) +1;
socket_width_diff =  socket_width_bottom/2 - socket_width_top/2;

base_length = 9 + base_extra_length; 

tip_cover_width = middle_diameter + tip_width; //[13.5 : 30]
base_total_width = middle_diameter + base_width;
fprint_ridge_area = tip_cover_width/1.0;
	
fn_fast = 1*20;
fn_accurate =1* 96;
	
//radius of wire for a tunnel from tip to base
wire_radius = .5 *0;

//the width of the hinge indent
hinge_indent_width = middle_width*.65;

//base_hinge_end_clearance = .5 *1;
hinge_outer_diameter = hinge_diameter + hinge_end_clearance;

tip_base_length = (knuckles==2)? hinge_outer_diameter/2 + 1  :  hinge_outer_diameter/2 + 2;
tip_core_length = tip_base_length + tip_post_height + tip_ridge_height;//hinge_diameter/2 
tip_cover_length = tip_length - tip_base_length;
tip_cover_base_length = tip_cover_length - tip_cover_width/2;

tip_pocket_width = tip_post_width;
tip_pocket_depth = (tip_cover_base_length*.75);

tip_tensioner_length = tip_ridge_width*.6;
tip_tensioner_slot_width = tunnel_radius*1.6;
	
//how far to explode
fnv = (fast==1 || preview==1) ? fn_fast : fn_accurate;
explode_distance = explode ? 12 : 0;

base_mid_width = middle_width-1;

//length of bottom part
bumper_length = (knuckles==1) ? (tip_base_length ) : (middle_length - hinge_diameter) -hinge_end_clearance*2;			

socket_hold_length = base_length - socket_catch_height - socket_post_height;
base_hump = socket_width_top/2 + socket_thickness_top/2 +base_tunnel_height;

tip_min_bottom = tip_post_height + tip_ridge_height+hinge_end_clearance*3;
fn_temp = tip_fingernail_ratio * tip_length;
tip_fn_length = (tip_cover_length-fn_temp >= tip_min_bottom) ? fn_temp : tip_cover_length-tip_min_bottom;

$fn=fnv ;
//$fn= 96;

//make magic happen
main();

module main(){
	if(preview == 1){
		difference(){
			generate_preview();
			if(make_cutaway==1){
				translate([-20,0,0])
				cube([40,100,200], center=true);
			}
		}
	} else { //PRINT MODE!
			difference(){
        
        union(){
		//Base section
		if (part== 3) 
			make_base();
//			echo (cutaway);
		

		//Linkage
		if (part== 10 )
		rotate([90,180,90])
		make_linkage();

		//hinge Plugs
		if (part == 9 )
		for (a = [0:3]) {
			translate([explode_distance*2,(hinge_pin_clearance+1)*a,0])
			make_plug();
		}
	
		//Middle section 
		if(part== 4)
		//2 knuckles
		if (knuckles == 2 ){
			rotate([0,-90 ,0])
			translate([0, explode_distance*3, middle_length/2 + (explode_distance)])
			make_middle();
		}else{
			linear_extrude(height=1)
			text("Not Used");
		}
	
		//Bumper for middle section
		if (part== 7)
		if (knuckles == 2 ){
			make_bumper();
		}else{
			linear_extrude(height=1)
			text("Not Used");
		}

		//2 Segment Tip with hinge			
		if (part== 5 )
		if (knuckles == 2 ){
			rotate([-90,0,0])
			translate([0,0,middle_length + (explode_distance*2) ])
			make_tip();
		} else {	//1 knuckle
			//1 segment tip (no hinge)
			rotate([180,0,0])
			make_mid_tip();
		}

		//Socket
		if (part== 8)
		difference(){
			rotate([0,180,0])
			translate([0,-explode_distance,0])
			make_socket();
			if(make_cutaway==1)
			translate([-15,0,0])
			cube([30,30,30], center=true);
		}
		//Tip cover
		if (part== 6)
		make_tipcover();			
    }
    
    if(make_cutaway==1){
		translate([-20,-10,-10])
		cube([40,40,40], center=true);
		}
    }
	} //end preview else
}

module generate_preview(){
				//make base for socket
				make_base();

				//Middle section for 2 knuckles
				if (knuckles == 2){
					rotate([rotatetest>0 ? -rotatetest : 0, 0,0]){
						//mid section
						translate([0,0, middle_length/2 + (explode_distance )])
						make_middle();

						//Bumper for middle section
						translate ([0, (explode_distance*2), middle_length/2  + (explode_distance)])
						make_bumper();
					}
				}

				//Socket
				//color("green")
				translate([0,0,-socket_interface_length -1 - (explode_distance) ])
				make_socket();

				translate([0,-20,-40])
				make_linkage();

				offst = middle_width/2 + 2 + hinge_plug_clearance*2 + hinge_offset + explode_distance;
				//hinge covers for preview
				rotate([0,90,0])
				for (i=[-1:2:1])
				translate([0,0,offst*i]){
					//base plugs
					rotate([0,i==-1?180:0,0])
					make_plug();
					if (knuckles == 2){
						//tip plugs
						rotate([0,0,-(rotatetest>0? rotatetest :0)])
						translate([-(middle_length + explode_distance*2),0,0])
						rotate([0,i==-1?180:0,0])
						make_plug();
					}
				}

				//TIP for for preview
				if (knuckles == 2){
					//2 Segment Tip with hinge 
					rotate([-(rotatetest>0? rotatetest :0) ,0,0])
					translate([0,0,middle_length ])
					rotate([-(rotatetest>0? rotatetest :0),0,0]){
						//tip
						translate([0,0, (explode_distance*2)])
						make_tip();
						//cover
						translate([0,0, tip_base_length+ (explode_distance*3) ])
						make_tipcover();
					}
					} else{ //Single-Knuckle-Mode 
						//1 segment tip (no hinge)
						translate([0,0, (explode_distance) ])
						rotate([-(rotatetest>0?rotatetest:0),0,0]){
							//tip
							make_mid_tip();
							//cover
							translate([0,0, tip_base_length+ (explode_distance*2) ])
							make_tipcover();
						}
					}
				}

//functions and model sections -- modify at own risk
module make_tipcover (){	
	difference(){
		intersection(){
			//plain rounded tip
			hull(){
				translate([0,0,tip_cover_base_length])
				resize ([tip_cover_width,0,0])
				sphere(tip_cover_width/2);

				translate([0,0,0.1])
				cylinder (h=tip_cover_base_length, d1=tip_cover_width, d2=tip_cover_width-.5 );//+ tip_post_clearance*2
			}

			//cut out fingernail - 
			union(){
				rotate([tip_fingernail_rot,0,0])
				translate([0,tip_fingernail_offset, tip_cover_base_length-4])
				resize ([0, tip_cover_width*1.15, tip_cover_width*2.1])
				sphere(tip_cover_width*.8);

				rotate([-15,0,0])
				translate([tip_cover_width -5,-.5,tip_cover_length/2])
				cylinder(d=tip_cover_width, h=tip_cover_length*2,center=true);
				rotate([-15,0,0])
				translate([-tip_cover_width +5,-.5,tip_cover_length/2])
				cylinder(d=tip_cover_width, h=tip_cover_length*2,center=true);

				rotate([tip_cuticle_rot,0,0])
				translate([0,0,-tip_cover_width + tip_cover_length - tip_fn_length])
				cube([tip_cover_width*2,tip_cover_width*2,tip_cover_width*2], center=true);	
			}	

			//round fingerprint surface	
			translate([0,-1.9, tip_cover_length/2-3.75	])
			rotate([5,0,0]){
				union(){
					resize ([0, tip_cover_width*1.2, tip_cover_length*1.8])
					sphere(tip_cover_width*.8);		
	
					if(fprint_ridge_height > 0)
					intersection(){
						resize ([0, tip_cover_width*1.2 + fprint_ridge_height, tip_cover_length*1.8])
						sphere(tip_cover_width*.8);		

						if(fprint_style == 1) //horiz finger prints
						translate([0,tip_cover_length/4, -tip_cover_length/2+3])
						for (i=[fprint_ridge_area +4:-fprint_ridge_offset : fprint_ridge_offset]){  
							translate([0,0,i])
							cube([tip_cover_width, tip_cover_width, fprint_ridge_thickness], center=true);
						}
		
						if(fprint_style == 2)//concentric
						rotate([105,0,0])
						translate([0,tip_cover_length/4.5, -tip_cover_width/2.2])
						for (i=[fprint_ridge_area:-fprint_ridge_offset:fprint_ridge_offset]){  
							rotate([180,0,0])
							resize([0,i*1.2,0])
							difference(){
								cylinder(d=i,h=4);
								translate([0,0,-.01])
								cylinder(d=i - fprint_ridge_thickness, h=4 + .02);
							}
						}			
					}
				}
			}
		}
        
        //HACK - copy of fingernail stuff for inside cut out.
        difference(){
        	intersection(){
                translate([0,-3.5, tip_cover_length/2-3.75])
                rotate([5,0,0])
				resize ([tip_cover_width*.9, tip_cover_width*1.2 + fprint_ridge_height, tip_cover_length*1.7])
                sphere(tip_cover_width*.8);		
                    
                rotate([tip_fingernail_rot,0,0])
				translate([0,tip_fingernail_offset +1.5, tip_cover_base_length-4])
				resize ([tip_cover_width*1.4, tip_cover_width*1.15, tip_cover_width*2.1])
				sphere(tip_cover_width*.8);
            }
            translate([0,0,-14 + tip_ridge_height*2+  tip_post_height])
           cylinder (h=14, d=tip_post_width*2);
            
           translate([0,0,tip_cover_length-1.5])
           cylinder (h=5, d=tip_post_width*2);
        }
            
		//cut out post area
		union(){
			diam = tip_ridge_width + tip_post_clearance;
			difference(){
				union(){
					//bottom of post
					cylinder (h=tip_post_height+1, d=tip_post_width);
					//move up a little, make bottom nice and snug
					translate([0,0, tip_post_height+tip_post_clearance]){
						//post ridge cutout
						cylinder (h=tip_ridge_height, d=diam);	//+tip_post_clearance
						//transition
						translate([0,0, tip_ridge_height -.01 ])
						cylinder (h=tip_ridge_height, d1=tip_ridge_width -1, d2=tip_pocket_width);	
					}
				}
				translate([0,-diam/2 ,tip_ridge_height+  tip_post_height+tip_post_clearance])
				cube([diam, tip_ridge_flat, tip_ridge_height*2], center=true);					
			}

			//pocket
		*#	translate([0,0, tip_post_height+tip_ridge_height *2])
			cylinder (h=tip_ridge_height+tip_post_clearance + tip_pocket_depth, d1=tip_pocket_width,d2=tip_pocket_width*.65);	

			//laser hole
			translate([0,0, tip_post_height])
			cylinder (h=tip_length, r=tip_accessory_radius);						
		}
	}
}

module make_mid_tip(){
	difference () {
		//mainsection
		union(){
			//main section
			//hinge circles
			rotate([0,90,0]) 
			//translate([tip_base_length/2,0,0]) 
			cylinder (d=hinge_diameter, h=middle_width, center=true);	

			//post
			translate([0,0,tip_base_length +tip_post_height/2 ])
			cylinder (h=tip_post_height, d=tip_post_width-tip_clearance, center=true);
			//ridge
			translate([0,0,tip_base_length + tip_post_height + tip_ridge_height/2])
			cylinder (h=tip_ridge_height, d=tip_ridge_width-tip_clearance, center=true);

			//echo (base_total_width);
			translate([0,0,tip_base_length/2]) 
			cylinder (h=tip_base_length, d1=middle_diameter, d2=tip_cover_width+.25, $fn=fnv, center=true);

			//tensioner block
			if (tip_tensioner_screw_radius > 0){
				translate([0,-.25, tip_base_length + tip_post_height +tip_ridge_height +tip_tensioner_height/2])
				create_tip_tensioner();
			}
		}

		hinge_cutout = tip_base_length - (tip_base_length-hinge_outer_diameter/2) + hinge_side_clearance;
		//trim SIDES
		translate([middle_width/2+.01, -hinge_diameter, -0.01])
		cube([middle_width, hinge_diameter*2, hinge_cutout], center=false);
		translate([-middle_width*1.5+.01, -hinge_diameter,-0.01])
		cube([middle_width, hinge_diameter*2, hinge_cutout], center=false);	

		//elastic hole
		hull(){
			translate([-tunnel_radius-tunnel_clearance, -hinge_diameter/2 - tunnel_radius/2, 0]) 
			sphere(tunnel_radius);

			translate([0,-2,tip_base_length+ tip_post_height + tip_ridge_height]) 
			sphere(tunnel_radius);
		}	
		//enlarge
		//	translate([0,-2,tip_base_length+ tip_post_height + tip_ridge_height]) 
		//sphere(tunnel_radius*1.75);

		//enlarge base side
		translate([-tunnel_radius-tunnel_clearance/2,-(hinge_diameter/2 + tunnel_radius - tunnel_clearance*1.5), tunnel_radius*2 - tunnel_radius*6]) 	
		cylinder (r2=tunnel_radius, r1=tunnel_radius*1.5, h=tunnel_radius*6);

		//tendon hole
		hull(){
			translate([0, hinge_diameter/2 + tunnel_radius/2, 0]) 
			sphere(tunnel_radius);

			translate([0,1.5,tip_base_length  + tip_post_height + tip_ridge_height]) 
			sphere(tunnel_radius);
		}	
		//enlarge
		//	translate([0,1.5,tip_base_length+ tip_post_height + tip_ridge_height]) 
		//	sphere(tunnel_radius*1.75);

		rotate([0,90,0]){
			//hinge pins
			//translate([tip_base_length/2,0,0]) 
			cylinder (r=hinge_pin_radius, h=middle_width*2, center=true);

			//hinge indent
			translate([0,0,-tunnel_clearance]) {
				difference(){
					cylinder (r=hinge_diameter/2+.1, h=hinge_indent_width, center=true);
					union(){
						cylinder (r=hinge_diameter/2-hinge_indent_depth, h=hinge_indent_width+.1, center=true);												
						translate ([-middle_width/2 ,0,0])
						cube ([middle_width, hinge_diameter,hinge_indent_width], center=true);
					}
				}
			}
		}

		//trim out bottom
		translate ([-middle_width-.05, hinge_diameter/2-.01, -tip_base_length/2-.01])
		cube([middle_width*2 +.1, middle_width, tip_base_length*2]);		

	}
}

module make_tip(){
	union(){
		//cut center 
		difference () {
			//mainsection
			union(){
				intersection(){
					//hinge circles
					rotate([0,90,0]) 
					hull(){
						//hinge circle
						cylinder (d=hinge_outer_diameter, h=middle_diameter+hinge_width, center=true);
						//nut hole ridges
						cylinder(h = middle_diameter+hinge_width, d=hinge_pin_clearance+1, center=true);
					}
					if(hinge_rounding>0){
						resize([0,hinge_diameter*hinge_rounding,hinge_diameter*hinge_rounding])
						sphere(hinge_diameter);
					}
				}
				difference(){
					//body 
					hull(){
						translate([0,0,-hinge_bend_padding])
						cylinder (h=tip_base_length + hinge_bend_padding, r1=middle_diameter/2 , r2=tip_cover_width/2+.2);

						//expiriment
						translate ([0, hinge_outer_diameter/2-.5, 1.25])
						cube ([ middle_width+2.5+hinge_side_clearance*2, 1, 2.5 ],center=true);	//sloppy 2.5mm
					}
					//bottom trim
					translate ([-middle_width, hinge_outer_diameter/2, -2])
					cube ([ middle_width*2, hinge_diameter/2, hinge_diameter*2 ],center=false);	
				}
				//post
				translate([0,0,tip_base_length])
				cylinder (h=tip_post_height, d=tip_post_width-tip_clearance);
				//ridge
				translate([0,0,tip_base_length + tip_post_height])
				difference(){
					cylinder (h=tip_ridge_height, d=tip_ridge_width-tip_clearance);
	
					diam = tip_ridge_width + tip_post_clearance;
					translate([0,-diam/2 +.25,  tip_post_height-.5 ])//TODO - hack
					cube([diam, tip_ridge_flat, tip_ridge_height*2], center=true);		
				}

				//tensioner block
				if (tip_tensioner_screw_radius > 0){
					translate([0,-.25, tip_base_length + tip_post_height +tip_ridge_height +tip_tensioner_height/2])
					create_tip_tensioner();
				}
			}
			//area to cut
			union(){				
				hull(){	
					//back cut
					rotate([0,90,0]) {
						cylinder (d=hinge_outer_diameter, h=middle_width+hinge_side_clearance*2, center=true);	
						//hinge_diameter+hinge_end_clearance*2
		
						//upper back cut						
						translate([hinge_diameter/4,0,0]) 
						cylinder (d=hinge_outer_diameter, h=middle_width+hinge_side_clearance*2, center=true);	
					}
				}

				//front cut
				translate ([0, hinge_diameter/2, 0])//-hinge_end_clearance])
				cube ([ middle_width+hinge_side_clearance*2, hinge_diameter, hinge_outer_diameter],true);

				//back flat cut
				rotate([0,90,0]){
					//nut hole
					cylinder (r=hinge_pin_radius, h=middle_width*3, center=true);
					// cut dips around hole for axle nuts
					for (i=[-1:2:1]){
						translate([0,0,i * (middle_width/2+hinge_side_clearance*2 + hinge_offset +5)])
						cylinder(h = 10, d=hinge_pin_clearance, center=true);
			
						translate([0,0,i*((middle_diameter+hinge_width)/2 + 4.999)])
						cylinder(h = 10, d=hinge_pin_clearance+2, center=true);
					}
				}

				//angle elastic hole
				hull(){
					translate([0,-(hinge_diameter/2 + tunnel_radius/2) +.4,0]) 
					sphere(tunnel_radius);

					//clone this one..
					translate([0, -tunnel_radius-tunnel_clearance , tip_core_length]) 
					sphere(tunnel_radius);
				}	
				//enlarge
				translate([0,-(hinge_diameter/2 + tunnel_radius/2) +tunnel_clearance*2 -.2,-.5]) 
				//sphere(hole*1.5);
				cylinder (r1=tunnel_radius*2, r2=tunnel_radius, h=tunnel_radius*2.5);

				//tendon hole
				hull(){
					translate([0,hinge_diameter/2 + tunnel_radius, hinge_diameter/2 - tunnel_radius -3]) 
					sphere(tunnel_radius);

					translate([0,1,tip_core_length ]) 
					sphere(tunnel_radius);
				}	

				//wire_tunnel
				translate([-2.75,0,0])
				cylinder (r=wire_radius, h=tip_length);
			}
		}
		if(washer_depth_outside>0)
		rotate([0,90,0]){
			//washers
			difference(){
				cylinder (r=hinge_pin_radius+washer_radius, h=middle_width+hinge_side_clearance*2, center=true);
				union(){
					cylinder(h = middle_width*2, r=hinge_pin_radius, center=true);
					cylinder(h = middle_width + hinge_side_clearance*2 - washer_depth_outside*2, r=hinge_pin_radius + washer_radius*2, center=true);						
				}
			}
		}
	}
}

module create_tip_tensioner(){
	difference(){					
		cube([tip_tensioner_width, tip_tensioner_length, tip_tensioner_height], true);
		//holes
		for (i=[-1:2:1])
		translate([0, tip_tensioner_length/2 * .42*i, -.2 ]){  //offset each way
			//cylinder (r= tip_tensioner_hole_radius, h = tip_tensioner_height+.01, center=true);	
			cube ([tunnel_radius*1.3, tunnel_radius*1.8, tip_tensioner_height+.5], true);	
			
			translate([tip_tensioner_width/2, 0, 0])
			rotate([0,90,0])
			cylinder (r= tip_tensioner_screw_radius, h = tip_tensioner_width+.01, center=true);	
		}
	}
}

module make_middle(){
	difference(){
		union(){		
			total_middle_length = middle_length + hinge_bend_padding*2;
			difference(){
				//main section
				union(){
					//main middle cylinder
					cylinder (h=total_middle_length, d=middle_diameter, center=true);
					//hinge circles
					rotate([0,90,0]) 
					for (i=[-1:2:1])
					translate([i*middle_length/2,0,0]) 
					cylinder (d=hinge_diameter, h=middle_width, center=true);	
				} 	
				//trim bottom hinge area			
				translate ([0, hinge_diameter, 0 ])
				cube([middle_width +.1, hinge_diameter, middle_length*1.5 ], center=true);		
		
				//trim out sides/top&bottom				
				for (i=[-1:2:1]){
					translate ([0, i*(hinge_diameter - tunnel_radius) , 0 ])
					cube([middle_width +.1, hinge_diameter, bumper_length], center=true);		
					
					//sides
					translate ([ i*(middle_width - 1), 0, 0 ])
					cube([middle_width +.1, hinge_diameter, bumper_length], center=true);	
				
					translate([i * (middle_width+.01), 0, 0])
					cube([middle_width, hinge_diameter*2,total_middle_length+.02], center=true);
				}
			
				//bumper holder middle hole	
				rotate([0,90,0])
				cylinder(d=hinge_diameter*.5, h=hinge_diameter, center=true);

				//wire_tunnel
				translate([-1,-3,0])
				cylinder (r=wire_radius, h=middle_length*1.5, center=true);	

				//top elastic holefrom base			
				translate([-tunnel_radius-tunnel_clearance+.25,-(hinge_diameter/2 + tunnel_radius - tunnel_clearance),0]) 
				cylinder (r=tunnel_radius, h=total_middle_length+.1, center=true);
			
				//enlarge tip side for knot
				translate([-tunnel_radius-tunnel_clearance+.25, -(hinge_diameter/2 + tunnel_radius - tunnel_clearance)+.2, (middle_length)/2-tunnel_radius+.01]) 	
				cylinder (r1=tunnel_radius*1.2, r2=tunnel_radius*1.2, h=tunnel_radius*2.5, center=true);

				//enlarge base side
				translate([-tunnel_radius-tunnel_clearance,-(hinge_diameter/2 + tunnel_radius - tunnel_clearance*1.5),-middle_length/2 + tunnel_radius*2 - tunnel_radius*6]) 	
				cylinder (r2=tunnel_radius/2, r1=tunnel_radius*1.5, h=tunnel_radius*6);

				//enlarge top angled elastic hole, tip side 
				translate([tunnel_radius+tunnel_clearance/2, -(hinge_diameter/2 - tunnel_radius/2), middle_length/2-tunnel_radius]) 	
				cylinder (r1=tunnel_radius, r2=tunnel_radius*1.2, h=tunnel_radius*6);
			
				if(middle_tensioner_screw_radius > 0){
					translate([0, hinge_diameter/2 + tunnel_radius*.8  -1, -middle_length/2 +4.25])  // /3				
					rotate([-45,0,0])
					cylinder(r=middle_tensioner_screw_radius, h=4, center=true);
				}else{
					//bottom knot flare
					translate([0,hinge_diameter/2 -1.8,-middle_length/2+hinge_diameter/3+2.75])
					sphere (tunnel_radius*1.7);			
				}
				//top tunnel down
				hull(){
					translate([ tunnel_radius+tunnel_clearance/2 ,-hinge_diameter/2 , middle_length/2])		
					sphere (tunnel_radius);			
					translate([0, hinge_diameter/2 -2 , -middle_length/2 +hinge_diameter/2 ]) 
					sphere (tunnel_radius);		
				}	

				//hinge indent
				rotate([0,90,0]) {
					translate([-middle_length/2,0,0]) {
						difference(){
							cylinder (r=hinge_diameter/2+.1, h=hinge_indent_width, center=true);
							cylinder (r=hinge_diameter/2-hinge_indent_depth, h=hinge_indent_width+.1, center=true);
							translate ([middle_width/2 ,0,0])
							cube ([middle_width, hinge_diameter ,hinge_indent_width], center=true);
						}
					}
				
					translate([middle_length/2,0,]) {
						difference(){
							cylinder (r=hinge_diameter/2+.1, h=hinge_indent_width, center=true);
							union(){
								cylinder (r=hinge_diameter/2-hinge_indent_depth, h=hinge_indent_width+.1, center=true);												
								translate ([-middle_width/2 ,0,0])
								cube ([middle_width, hinge_diameter,hinge_indent_width], center=true);
							}
						}
					}
				
					//flat indent for bottom
					translate([0,hinge_diameter/2,0])// + tunnel_radius - tunnel_clearance,0]) 
					cube ([middle_length+6,hinge_indent_depth*2,hinge_indent_width], center=true);
				}
			}
			rotate([0,90,0]){
				//washers
				for (i=[-1:2:1])
				translate([i*middle_length/2,0,0]) 
				cylinder (r=hinge_pin_radius+washer_radius, h=middle_width+washer_depth_inside*2, center=true);
			}
		
			if(middle_sides == 0)	
			make_bumper();
	
		}
	
		//hinge pins
		rotate([0,90,0]) {
			for (i=[-1:2:1])
			translate([i*middle_length/2,0,0]) 
			cylinder (r=hinge_pin_radius, h=middle_width*2, center=true);
		}
	}
}

module make_bumper(){
	union(){
		intersection(){
			difference(){
				cylinder (h=bumper_length, d=middle_diameter, center=true);

				height = hinge_diameter - tunnel_clearance -  tunnel_radius     /2;
				width = middle_width-2+tunnel_clearance;
				//cut middle
				cube([width, height, bumper_length +.1], center=true);

				hull(){
					//center cut
					resize([0,hinge_diameter*1.2,0])
					cylinder(d=middle_width-.25,h=middle_length,center=true);
					//top hole
					translate([-tunnel_radius-tunnel_clearance,-(hinge_diameter/2 + tunnel_radius - tunnel_clearance*1.3),0]) 
					cylinder (r=tunnel_radius, h=middle_length+hinge_diameter, center=true);
					//bottom tendon hole				
					translate([0,hinge_diameter/2 ,0]) 
					cylinder (r=tunnel_radius, h=middle_length+hinge_diameter, center=true);
				}
				//bumper_split
				if (bumper_split != 0){
					i = bumper_split < 0 ? -1 : 1;
					translate([i*(width/2 -.05),height/2 + 2.5,0])
					cube([abs(bumper_split),6,bumper_length+1], center=true);
				}
			}

			hull(){
				resize([middle_diameter ,//bumper_length*1.5 +2, 
				middle_diameter+hinge_width -.5,
				bumper_length*1.5  ])//middle_diameter+hinge_width, (bumper_length+1) *.85])
				sphere(	/*(bumper_length+1) *.85*/  middle_diameter, center=true);

				difference(){
					cylinder (h=bumper_length, d=middle_diameter +.25, center=true);
					translate([0,tunnel_radius+tunnel_clearance,0])
					cube([middle_diameter+2,middle_diameter,bumper_length +.1], center=true);
				}
			}
		}
		//plugs fr holding
		if (bumper_pegs >0 )
		difference(){
			rotate([0,90,0])
			cylinder(d=hinge_diameter*.5, h=hinge_diameter, center=true);	
			cube([middle_width - bumper_pegs*2,middle_diameter/2,bumper_length], center=true);
		}
	}
}

module make_plug(){ 
	hh=hinge_plug_thickness;
	dd=(hinge_pin_clearance-hinge_plug_clearance)*1;

	difference(){
		union(){
			if(hinge_plug_bulge > 0){
				translate([0,0,hh/2])
				resize([0,0,hinge_plug_bulge*2])
				sphere(dd/2);
			}
			cylinder(d=dd, h=hh, center=true);
		}		
		translate([0,0, ( -hh/2 +hinge_nut_thickness/2) ]) 
		cylinder(d=hinge_nut_width, h=hinge_nut_thickness+.01, $fn=hinge_nut_sides, center=true);
	}
}
						
module make_base(){
	union(){			
		//cut center 
		difference (){
			//mainsection
			union(){
				intersection(){
					rotate([0,90,0]) 
					hull(){
						//hinge circle  hinge_diameter+hinge_end_clearance*3   SLOPPY +1 constant..
						cylinder (d=hinge_outer_diameter, h=middle_diameter+hinge_width +1, center=true);
						//nut hole ridges
						cylinder(h = middle_diameter+hinge_width, d=hinge_pin_clearance+1, center=true);
					}
					if(hinge_rounding>0){
						resize([0,hinge_diameter*hinge_rounding,hinge_diameter*hinge_rounding])
						sphere(hinge_diameter +.5);
					}
				}

				translate([0,0,-socket_hold_length -1])
				intersection(){
					//main cylinder
					cylinder (d1=base_total_width-.5, d2=middle_diameter, h=socket_hold_length + hinge_bend_padding +1, center=false);

					s = base_total_width*1.75;
					translate([0,  -s/2.65 + hinge_diameter/2 ,0])
					cylinder (d1=s-.5, d2=s-5, h=socket_hold_length+ hinge_bend_padding+1, center=false);
				}

				//Socket interface
				translate([0,0,-(hinge_diameter/2 +2  +socket_interface_length )]) { //HACK! +2
					cylinder (d1=base_total_width, d2=middle_diameter-2, h=socket_interface_length, center=false);	
					//orientation slot
					intersection(){
						cylinder (d1=base_total_width+1, d2=middle_diameter-2+1, h=socket_interface_length, center=false);	
						translate([-1,0,0])
						cube([1.5,base_total_width,socket_interface_length]);
					}
				}
			}
			//area to cut
			union(){
				//test cylinder (d=2, h=30, center=true);	
				hull(){
					rotate([0,90,0]){
						//back cut
						cylinder (d=hinge_outer_diameter, h=middle_width+hinge_side_clearance*2, center=true);	
						//upper back cut						
						translate([-hinge_diameter/4,0,0]) 
						cylinder (d=hinge_outer_diameter, h=middle_width+hinge_side_clearance*2, center=true);	
						//front cut
						translate([1.25,hinge_diameter,0]) //add 1 to drop it a bit
						cylinder (d=hinge_outer_diameter, h=middle_width+hinge_side_clearance*2, center=true);	
					}		
				}
				//flat interface
				translate ([0,-hinge_diameter/2 , 2.5 + hinge_bend_padding ])
				cube([middle_width+hinge_side_clearance*2+.001, 5, 4], true);		
			}

			//pin
			rotate([0,90,0]){
				cylinder(h = middle_width*3, r=hinge_pin_radius, center=true);
				// cut dips around hole for axle nuts
				for (i=[-1:2:1]){  
					//sloppy constant .75!
					translate([0,0,i*(middle_width/2+hinge_side_clearance*2 + hinge_offset + 5 +.75)])
					cylinder(h = 10, d=hinge_pin_clearance, center=true);
				}
			}	

			//tendon hole
			hull(){
				translate([(tunnel_radius/2)+.5, -(hinge_diameter/2 + tunnel_radius - tunnel_clearance*2) +2.5,-hinge_diameter/2 +1]) 
				sphere (tunnel_radius);

				translate([tunnel_radius,-base_hump, -(hinge_diameter/1.5) +1])//-base_length + tunnel_radius + tunnel_clearance])
				sphere (tunnel_radius);
			}
			translate([(tunnel_radius/2)+.5,-(hinge_diameter/2 + tunnel_radius - tunnel_clearance*2) +4,-hinge_diameter/2 +.5]) 
			//	sphere (tunnel_radius*1.3);
			rotate([90,0,0])
			cylinder(r=tunnel_radius, h=4.5);

			//elastic hole
			hull(){		
				translate([-(tunnel_radius+tunnel_clearance), -(hinge_diameter/2 )-1 ,0]) 
				sphere (tunnel_radius);

				translate([-(tunnel_radius),  -base_total_width/2 - tunnel_radius/2 + tunnel_clearance*3.2  +2.5 ,-base_length -2.25])
				sphere (tunnel_radius);
			}	
			//Hacky?
			translate([-(tunnel_radius+tunnel_clearance), -(hinge_diameter/2 )-.5, -.5]) 
			resize([0,0,tunnel_radius*4])
			sphere (tunnel_radius*1.5);		

			//widen elastic bottom hole
			translate([-(tunnel_radius) ,-base_total_width/2 - tunnel_radius/2 +tunnel_clearance*3.75 +1,-base_length-1 ])
			sphere (tunnel_radius*1.4);

			//set screw hole
			if (base_tensioner_screw_radius > 0 ){
				translate([-(tunnel_radius)-.5, -base_total_width/2 - tunnel_radius/2 +tunnel_clearance*2 +5,3.35+ -base_length + socket_catch_height+base_tensioner_screw_radius -tunnel_radius -.1]){
				rotate([110,0,0])
				cylinder(r=base_tensioner_screw_radius, h=4, center=true);
				translate([0,1.75,0.5])
				rotate([110,0,0])
				cylinder(r=base_tensioner_screw_radius+.2, h=3, center=true);
			}
			}

			//stump indent
			translate ([0,0,(-base_length -stump_indent) +stump_indent_offset -2.5]) //socket_catch_height*2
			sphere (stump_indent, $fn=fast?80:fn_accurate);
		}

		if(washer_depth_outside>0)
		rotate([0,90,0]){
			//washers
			difference(){
				cylinder (r=hinge_pin_radius+washer_radius, h=middle_width+hinge_side_clearance*2, center=true);
				union(){
					cylinder(h = middle_width*2, r=hinge_pin_radius, center=true);
					cylinder(h = middle_width+hinge_side_clearance*2-washer_depth_outside*2, r=hinge_pin_radius+washer_radius*2, center=true);						
				}
			}
		}
	}
}
   

module make_socket(){
	difference(){
		//main socket body
		s_top = base_total_width + socket_thickness_top*2;
		union(){
			translate ([0,0,-socket_interface_length -socket_vertical_clearance])
			cylinder (d1=base_total_width + socket_thickness_top*2, d2=middle_diameter-1+ socket_thickness_top*2, h=socket_interface_length, center=false);	

			translate ([0,0, - socket_interface_length -socket_vertical_clearance - socket_depth/2 ]) 
			cylinder(h = socket_depth, r1=(socket_width_bottom/2.0) + socket_thickness_bottom, r2=base_total_width/2 + socket_thickness_mid, center=true);								
		}
		
        //start cuts
        
	 	//extra cut - HACK
		translate ([0,0,-socket_interface_length -socket_vertical_clearance -2])
		difference(){
			cylinder (d1=s_top+1, d2=s_top, h=socket_interface_length, center=false);	
			cylinder (d1=s_top, d2=s_top-2.5, h=socket_interface_length+1, center=false);	
		}

		//cut interface points out at top - post section
		translate([0,0, -socket_vertical_clearance+.01]){
			translate ([0,0,-socket_interface_length]){
				cylinder (d1=base_total_width + socket_clearance*2, d2=middle_diameter-2+ socket_clearance*2, h=socket_interface_length, center=false);	
				intersection(){
					cylinder (d1=base_total_width+.75, d2=middle_diameter-2+.75, h=socket_interface_length, center=false);	
					translate([-.75,0,0])
					cube([1.5,base_total_width,socket_interface_length]);
				}
			}
			//cut center of socket
			if (socket_ridge_depth > 0 && socket_ridge_spacing > 0){
                //socket_ridge_total = socket_ridge_depth +socket_ridge_spacing;

             //   echo ( socket_ridge_number);
             //   echo ( socket_width_diff );
                for (i=[0:1:socket_ridge_number/2]){  
                    percent = i / socket_ridge_number *2;
                  //  echo (socket_width_diff * percent *2);
//                    echo (percent);
                    for (j=[0:1:1]){  
                       translate ([0,0,-socket_interface_length +1 - socket_depth * percent - (socket_ridge_spacing * j) ])
                        cylinder(h = socket_ridge_spacing+.1, r=socket_width_top/2 + socket_width_diff * percent + (socket_ridge_depth*j), center=false);	
                    //    echo (j);
                    }
                }
            }else{
                translate ([0,0,-socket_interface_length-socket_depth +.01])
                cylinder(h = socket_depth, r2=socket_width_top/2, r1=socket_width_bottom/2, center=false);				
            }
		}

		//String clearance hack
		hull(){
			translate ([-10,-socket_width_top/2 -10.4, 0])
			cube([20, 10, 1]);
			translate ([-10,-socket_width_top/2 - 12.5, -(socket_catch_height + socket_post_height)*2.8])
			cube([20, 10, 1]);
		}

		//scallops
		if (socket_depth_scallop_left > 0){
			sr = socket_depth - socket_depth_scallop_left;
			sr2 = socket_width_bottom*socket_width_scallop;
			union(){
				translate ([-1 * socket_width_bottom/2, 0, -(socket_depth + socket_catch_height + socket_post_height)-1])
				resize([socket_width_bottom,sr2,sr*2 +2])
				sphere (sr);
			}
		}
		if (socket_depth_scallop_right > 0){
			sr = socket_depth - socket_depth_scallop_right;
			sr2 = socket_width_bottom*socket_width_scallop;
			union(){			
				translate ([socket_width_bottom/2, 0, -(socket_depth + socket_catch_height + socket_post_height)-1])
				resize([socket_width_bottom,sr2,sr*2 +2])
				sphere (sr);
			}
		}
		socket_hinge_notch = socket_catch_height/2;

		//Taper
		if(socket_taper > 0){
			sh = socket_width_bottom/2 + socket_thickness_bottom*socket_taper;
			translate([0,0,-socket_depth - socket_width_bottom/4]){
				resize([0,0,sh*3])
				sphere (sh);

				translate([0,socket_thickness_bottom, socket_depth-socket_depth_bottom -(socket_catch_height + socket_post_height+3)  ])  ///hack!!!
				resize([0,0,sh*3])
				sphere (sh);

				if(socket_depth_scallop_left>0){
					difference(){
						translate([0,0, socket_depth-socket_depth_scallop_left -(socket_catch_height + socket_post_height+2)  ])  ///hack!!!
						resize([sh*2+socket_thickness_bottom,sh*1.7,sh*3])
						sphere (sh);

						translate([0,-10,-10])
						cube([sh*4,sh*4,sh*4]);
					}
				}
			}
		}
		if(socket_depth_bottom > 0){
			dd = socket_depth - socket_depth_bottom;
			translate([0,socket_thickness_bottom*3,-socket_depth - (socket_catch_height + socket_post_height) -.1])
			cylinder(d=socket_width_bottom+1, h=dd);
		}

	}
}

module make_linkage(){
	//[0:Plain,1:Hole,2:Peg,3:Loop,4:Cup ]
	union(){
		difference(){
			union(){
				translate([0,0,+linkage_end2_round/2 -linkage_end1_round/2])
				resize([linkage_width,linkage_height,0])
				cylinder(h = linkage_length - linkage_end1_round - linkage_end2_round, d=linkage_width, center=true);	

				if(linkage_end2_round>0){
					translate ([0,0,-linkage_length/2 + linkage_end2_round  ])
					resize([linkage_width,linkage_height,linkage_end2_round*2])
					sphere(10);
				}
				if(linkage_end1_round>0){
					translate ([0,0,linkage_length/2 - linkage_end1_round ])
					resize([linkage_width,linkage_height,linkage_end1_round*2])
					sphere(10);
				}
			}

			//holes	
			if (linkage_end2 == 1){
				translate ([0,0,-linkage_length+linkage_hole_length])
				cylinder(h = linkage_hole_length, r=linkage_hole_radius, center=true);			
			}
			if (linkage_end1 == 1){
				translate ([0,0, linkage_length-linkage_hole_length])
				cylinder(h = linkage_hole_length, r=linkage_hole_radius, center=true);			
			}				

			if (linkage_holethrough_radius > 0){
				cylinder(h = linkage_length+.01, r=linkage_holethrough_radius, center=true);			
			}				

			if(linkage_angle_hole_radius > 0){
				translate([0,linkage_height/2 , linkage_length/2 -linkage_angle_hole_offset])
				rotate([90+linkage_angle_hole_angle,0,0])
				cylinder(h =  linkage_height, r= linkage_angle_hole_radius, center=true);	
			}
		}

		//loops
		if (linkage_end2 == 3){
			translate ([0,0,-linkage_length/2 - linkage_end2_length/2 + linkage_end2_thickness - linkage_end2_offset])
			make_loop(linkage_end2_width, linkage_end2_length, linkage_end2_height, linkage_end2_thickness);
		}
		if (linkage_end1 == 3){
			translate ([0,0,linkage_length/2 + linkage_end1_length/2  - linkage_end1_thickness + linkage_end1_offset ])
			make_loop(linkage_end1_width, linkage_end1_length, linkage_end1_height, linkage_end1_thickness);
		}

		//hooks
		if (linkage_end2 == 5){
			translate ([0,0,-linkage_length/2 + linkage_end2_round/2 + linkage_end2_thickness*1.5- linkage_end2_length/2 + linkage_end2_offset])
			make_hook(linkage_end2_width, linkage_end2_length, linkage_end2_height, linkage_end2_thickness);
		}
		if (linkage_end1 == 5){
			translate ([0,0,linkage_length/2 - linkage_end1_round/2 - linkage_end1_thickness*1.5 + linkage_end1_length/2 -linkage_end1_offset])
			make_hook(linkage_end1_width, linkage_end1_length, linkage_end1_height, linkage_end1_thickness);
		}
	}
}
	
module make_loop(linkage_loop_width,linkage_loop_length,linkage_loop_height, linkage_loop_thickness){
	linkage_loop_extrusion = 2.5*1;
	rotate([90,0,0])
	resize([linkage_loop_width,linkage_loop_length,linkage_loop_height])
	rotate_extrude(convexity = 3, $fn = fnv)
	translate([linkage_loop_extrusion, 0, 0])
	circle(d = linkage_loop_thickness, $fn = fnv);
}

module make_hook(linkage_hook_width, linkage_hook_length, linkage_hookheight, linkage_hook_thickness){
	linkage_loop_extrusion = 2.5*1;
	translate([0,linkage_hookvertical_offset,0])
	rotate([90,0,90])
	difference(){
		resize([linkage_hook_width,linkage_hook_length,linkage_hookheight])
		rotate_extrude(convexity = 3)
		translate([linkage_loop_extrusion, 0, 0])
		circle(d = linkage_hook_thickness);

		translate([linkage_hook_width/2,linkage_hook_length/4 + linkage_hookopening_offset,0])
		rotate([0,0,15])
		difference(){
			cube([linkage_hook_width,5,linkage_hookheight], center=true);

			translate([-1.5,-2.5,0])		
			resize([3,2,linkage_hookheight])
			sphere(1.5);
		}
	}
}
