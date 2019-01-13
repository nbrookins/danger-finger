// Knick's finger v4
// Copyright 2014-2019 Nicholas Brookins and Danger Creations, LLC
// http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
//
// Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
// Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0

ver = "4.0.05";
//Choose which part to create.  Best practice is to set all settings, and then generate each part, one by one.  The middle and bumper sections are only used with 2 knuckles.
part = 4; //[ 6:Tip Cover, 5:Tip Knuckle, 4:Middle Segment, 7:Middle Bumper, 3:Base Knuckle, 8:Finger Socket, 9:Hinge Plugs, 10: Wrist Linkage, 11: WasherClamp]
//How many knuckles/hinges to create.  In single knuckle mode, do not create the middle or bumper parts, they are not used and will cause an error.
knuckles = 2; // [1,2]
//Enable to preview all parts together!  KEEP THIS OFF in order to create individual printable parts.
preview = 0; //[0:Print Mode, 1:Preview Mode (dont print!)]
 //Advanced: build parts more crudely, but much more quickly - for twiddling.  print mode automatically turns this off
fast = 0;
// rotate the base and tip parts, to see how the hinges interact with the middle section.  Only relevant when previewing.  0 for straight, and up to 95 for fully bent.
rotatetest = 0; //[0:95]
//remove additional skin areas to make a skelatal finger
skeleton = 1;
//explode parts apart to see them individually better.  Only relevant when previewing.
explode = 0; //[0,1]
//preview ith cutaway to show insides
make_cutaway = 0;



echo (str("*** DangerCreations Finger v", ver, " ***"));
echo ("Params: ", part=part, kn=knuckles, prev=preview, rot=rotatetest, ske=skeleton, expl=explode, cut=make_cutaway);
//Default parameters
include <danger-finger-defaults.scad>;
//user specific configuration
//include <user-config.scad>;
//auto-generated values, boilerplate
include <danger-finger-parts.scad>;

// ****************************************************************
// *** Auto config variables ***

tip_ridge_flat = (tip_ridge_width - tip_post_width);

hinge_outer_width = middle_width + hinge_side_clearance * 2
	+ hinge_thickness * 2 + hinge_plug_thickness * 2
	+ washer_depth_outside*2 + hinge_plug_side_clearance * 2;

bumper_height = hinge_diameter - tunnel_clearance -  tunnel_radius     /2;
				bumper_width = middle_width-2+tunnel_clearance;
//									i = bumper_split < 0 ? -1 : 1;

middle_length = middle_section_length - hinge_diameter;

socket_width_top = socket_circumference_distal / PI;
//NB: 17
socket_width_bottom = socket_circumference_proximal / PI;
//NB: 22
socket_ridge_number = ceil(socket_depth/socket_ridge_spacing) +1;
socket_width_diff =  socket_width_bottom/2 - socket_width_top/2;

tip_cover_width = middle_diameter_width + tip_width; //[13.5 : 30]
tip_top_width = tip_cover_width - 1.0;
base_total_width = middle_diameter + base_width;
fprint_ridge_area = tip_cover_width/1.0;

//how far to explode
explode_distance = explode ? 12 : 0;

//radius of wire for a tunnel from tip to base
wire_radius = .5 *0;

//the width of the hinge indent
hinge_indent_width = middle_width*.65;

//base_hinge_end_clearance = .5 *1;
hinge_outer_diameter = hinge_diameter + hinge_end_clearance;

base_length = hinge_outer_diameter + base_extra_length;  //HACK???
base_body_length = base_length -hinge_outer_diameter/2;//- socket_catch_height - socket_post_height;

tip_base_length = (knuckles==2)? hinge_outer_diameter/2 + 1  :  hinge_outer_diameter/2 + 2;
tip_core_length = tip_base_length + tip_post_height + tip_ridge_height;//hinge_diameter/2
tip_cover_length = tip_length - tip_base_length;
tip_cover_base_length = tip_cover_length - tip_cover_width/2;

tip_pocket_width = tip_post_width;
tip_pocket_depth = (tip_cover_base_length*.75);

tip_tensioner_slot_width = tunnel_radius*1.6;

//length of bottom part
top_tunnel_height = -(hinge_diameter/2 + tunnel_radius - tunnel_clearance);

base_hump = socket_width_top/2 + socket_thickness_top/2 +base_tunnel_height;

tip_min_bottom = tip_post_height + tip_ridge_height+hinge_end_clearance*3;
fn_temp = tip_fingernail_ratio * tip_length;
tip_fn_length = (tip_cover_length-fn_temp >= tip_min_bottom) ? fn_temp : tip_cover_length-tip_min_bottom;

total_middle_length = middle_length + hinge_bend_padding*2;

middle_strut_width = 2.0;
hull_cyl_height = 0.25;
socket_interface_flare = 2.750;
socket_interface_neck = -1;

socket_interface_top = base_total_width - socket_thickness_top*2 + socket_interface_neck;
socket_interface_bottom = base_total_width - socket_thickness_top*2 + socket_interface_flare;//base_total_width + socket_slot_depth_bottom;

bumper_length = (knuckles==1) ? (tip_base_length )
	: total_middle_length - hinge_diameter +hinge_bend_padding;//(middle_length - hinge_diameter) +hinge_end_clearance*2;

//echo (sit=socket_interface_top, sib=socket_interface_bottom, btw=base_total_width);
//$fn=fnv;
$fa = (fast) ? 18 : 3;
$fs = (fast) ? 2 : 0.5;

echo ("Accuracy: ", fn=$fn, fs=$fs, fa=$fa);
// *******************************************
//  MAIN Function - entry point
//
module main(){
    difference(){
        if(preview == 1)
            generate_preview();
        else
            generate_print();

        if(make_cutaway==1)
            translate([-20,0,0])
            cube([40,100,200], center=true);
    }
}

module generate_print(){
        union(){
		//Base section
		if (part== 3 || part==0)
			translate([(part==0)?-20:0, (part==0)?15:0, 0])
			make_base();

		//Linkage
		if (part== 10 || part==0)
			translate([0,(part==0)?32:0,0])//[( 0, (part==0)?-20:0, 0])
			rotate([90,180,90])
			make_linkage();

		//hinge Plugs
		if (part == 9 || part==0)
		for (a = [0:3]) {
			translate([-(hinge_plug_diameter+1)*a -20, 0, 0])
			make_plug(bulge=hinge_plug_bulge);
		}

		//Middle section
		if(part== 4 || part==0)
		//2 knuckles
		if (knuckles == 2 ){
			translate([(part==0)?-20:0, (part==0)?-20:0, 0])
			rotate([-90, 0 ,90])
			make_middle();
		}else{
			linear_extrude(height=1)
			text("Not Used");
		}

		//Bumper for middle section
		if (part== 7 || part==0)
		if (knuckles == 2 ){
			translate([ (part==0)?20:0,(part==0)?20:0,0 ])
			make_bumper();
		}else{
			linear_extrude(height=1)
			text("Not Used");
		}

		//2 Segment Tip with hinge
		if (part== 5 || part==0)
		if (knuckles == 2 ){
			translate([(part==0)?10:0, (part==0)?-20:0, 10])
			rotate([-90,0,0])
			make_tip();
		} else {	//1 knuckle
			//1 segment tip (no hinge)
			rotate([180,0,0])
			make_mid_tip();
		}

		//washer clamp
		if (part==11 || part==0)
			//translate([0,(part==0)?32:0,0])//[( 0, (part==0)?-20:0, 0])
			//rotate([90,180,90])
			make_washer_clamp();

		//Socket
		if (part==8 || part==0)
		difference(){
			rotate([0,180,0])
			make_socket();
		}
		//Tip cover
		if (part==6 || part==0)
			translate([ (part==0)?30:0 ,0,0])
			make_tipcover();
    }
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
%						translate ([0, (explode_distance*2), middle_length/2  + (explode_distance)])
						make_bumper();
					}
				}

				//Socket
				translate([0,0,-base_body_length - (explode_distance) ])
				make_socket();

				translate([-20,-0,-0])
				make_linkage();

				offst = (hinge_outer_width + explode_distance) / 2 - hinge_plug_thickness/2 -hinge_plug_bulge/8;
				//hinge covers for preview
				rotate([0,90,0])
				for (i=[-1:2:1])
				translate([0,0,offst*i]){
					//base plugs
					rotate([0,i==-1?180:0,0])
					make_plug(bulge=hinge_plug_bulge);
					if (knuckles == 2){
						//tip plugs
						rotate([0,0,-(rotatetest>0? rotatetest :0)])
						translate([-(middle_length + explode_distance*2),0,0])
						rotate([0,i==-1?180:0,0])
						make_plug(bulge=hinge_plug_bulge);
					}
				}

				//TIP for for preview
				if (knuckles == 2){
					//2 Segment Tip with hinge
					rotate([-(rotatetest>0? rotatetest :0) ,0,0])
					translate([0,0,middle_length ])
					rotate([-(rotatetest>0? rotatetest :0),0,0]){
						//tip
						translate([0,0, (explode_distance*2)]){
						make_tip();
						make_washer_clamp();
						}
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


//make magic happen
main();

