

module tip(){
				hull(){
				translate([0,0,tip_cover_base_length])
				resize ([tip_top_width,0,0])
				sphere(tip_top_width/2);

				translate([0,0,0.1])
				cylinder (h=tip_cover_base_length, d1=tip_cover_width, d2=tip_top_width );//+ tip_post_clearance*2
			}
}

module nail(){
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
}
//functions and model sections -- modify at own risk
module make_tipcover (){
    diame = tip_ridge_width + tip_post_clearance;
	difference(){
		intersection(){
			//plain rounded tip
			tip();

			//cut out fingernail -
			nail();

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
					}
				}
			}
		}

        //HACK - copy of fingernail stuff for inside cut out.
		//translate([0,-10,0])
       difference(){
		 resize([tip_top_width-1.0,0,0])
        	intersection(){
                translate([0,-1.8,-1.8])
				difference(){
				tip();
				//HACK
				translate([0,-3.5,0])
				cube([tip_cover_width, 1, tip_cover_length]);
				}
				translate([0,1.3,-1.8])
                nail();
            }
			//cut bottom of cut
            translate([0,0,-14 + tip_ridge_height*2+  tip_post_height])
           cylinder (h=14, d=tip_post_width*2);
			//trim top of cut
           translate([0,0,tip_cover_length-1.5])
           cylinder (h=5, d=tip_post_width*2);
		   //trim front of cut
		   //HACK 2 constant
		   translate([ 0, -tip_ridge_width/2 +2, tip_cover_length/2])
		   cube([tip_cover_width, 2, tip_cover_length], center=true);
        }

		//cut out post area
		union(){

			difference(){
				union(){
					//bottom of post
					cylinder (h=tip_post_height+1, d=tip_post_width);
					//move up a little, make bottom nice and snug
					translate([0,0, tip_post_height+tip_post_clearance]){
						//post ridge cutout
						cylinder (h=tip_ridge_height, d=diame);	//+tip_post_clearance
						//transition
						translate([0,0, tip_ridge_height -.01 ])
						cylinder (h=tip_ridge_height, d1=tip_ridge_width -1, d2=tip_pocket_width);
					}
				}
				translate([0,diame/2 +.2,tip_ridge_height+  tip_post_height+tip_post_clearance])
				cube([diame, tip_ridge_height, tip_ridge_height*2], center=true);
			}

			//laser hole
			translate([0,0, tip_post_height])
			cylinder (h=tip_length, r=tip_accessory_radius);
		}
	}
}

module make_mid_tip(){
    hinge_cutout = tip_base_length - (tip_base_length-hinge_outer_diameter/2) + hinge_side_clearance;
	difference () {
		//mainsection
		union(){
			//main section
			//hinge circles
			rotate([0,90,0])
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

		rotate([0,90,0]){
			//hinge pins
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
				make_hinges();

				difference(){
					//body
					hull(){
						translate([0,0,-hinge_bend_padding])
                        resize([middle_diameter_width,0,0])
						cylinder (h=hull_cyl_height, d=middle_diameter);

                        translate([0,0,tip_base_length-hull_cyl_height])
						cylinder (h=hull_cyl_height, d=tip_cover_width + 0.2);
						//expiriment
						translate ([0, hinge_outer_diameter/2-.5, 1.25])
						cube ([ middle_width+2.5+hinge_side_clearance*2, 1, 2.5 ],center=true);	//sloppy 2.5mm
					}
					//bottom trim
					translate ([-middle_width, hinge_outer_diameter/2, -2])
					cube ([ middle_width*2, hinge_diameter/2, hinge_diameter*2 ],center=false);
                    if ( skeleton == 1){
                       translate([-middle_width/2,-10,1.5 ])
                        cube([middle_width,10,tip_base_length -3.2]);
                    }
				}
				//post
				translate([0,0,tip_base_length])
				cylinder (h=tip_post_height, d=tip_post_width-tip_clearance);
				//ridge

				translate([0,0,tip_base_length + tip_post_height])
				difference(){
					cylinder (h=tip_ridge_height, d=tip_ridge_width-tip_clearance);

					translate([0, tip_ridge_width/2 + tip_ridge_height -tip_clearance/2 - (tip_ridge_width-tip_post_width)/2,  tip_post_height - tip_ridge_height/2 - 0.0001 ])
					cube([hinge_outer_width, tip_ridge_height*2, tip_ridge_height + 0.0004], center=true);
				}

				//tensioner block
				if (tip_tensioner_screw_radius > 0){
					translate([
                    //-tip_ridge_width/2 + tip_tensioner_width*.82
                    -tip_tensioner_width/2
                    , 0
                    , tip_base_length + tip_post_height +tip_ridge_height +tip_tensioner_height/2 - 0.001]){

					create_tip_tensioner();

					}
				}
			}
			//area to cut
			union(){
				hull(){
					//back cut
					rotate([0,90,0]) {
						cylinder (d=hinge_outer_diameter+0.001, h=middle_width+hinge_side_clearance*2, center=true);
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
					get_plug_cutout();

					//TODO - rounding on outer edge
				}

				//angle elastic hole
				hull(){
					translate([1.3, 0 , tip_core_length])
                    cube([tunnel_radius * 1.2 + 1 ,tunnel_radius * 2.0, 1.5], center=true);
                    ss= middle_width/2.5;
                   	translate([0,-(hinge_diameter/2 ) +(ss) - tunnel_radius*1.5 ,0])
					sphere(ss);

                    translate([0,hinge_diameter/3, 0])
					sphere(tunnel_radius * 2);
				}
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
module make_hinges(){

	intersection(){
					rotate([0,90,0])
						//hinge circle  hinge_diameter+hinge_end_clearance*3
                     cylinder (d=hinge_outer_diameter, h=hinge_outer_width , center=true);
					if(hinge_rounding>0){

			hull()
					for(i=[-1:2:1])
						translate([i*(middle_width/2 +hinge_thickness),0,0])
						//resize([hinge_outer_width*hinge_rounding, 0,0])//hinge_outer_width])
						sphere(hinge_diameter*hinge_rounding*0.1);
					}
	}
}

module create_tip_tensioner(){
    rotate([0,0,90])
    difference(){
		//main block
        intersection(){
		cube([tip_tensioner_length, tip_tensioner_width, tip_tensioner_height], true);
        cylinder (h = tip_tensioner_height, d = tip_tensioner_length*1.05, center=true);
        }
		//cut out nut shape
        hull(){
            translate([0,tensioner_nut_thickness/1.6,0]){
                rotate([90,30,0])
                cylinder(h=tensioner_nut_thickness, d=tensioner_nut_diam, $fn=6);
                translate([0,0,5])
                rotate([90,30,0])
                cylinder(h=tensioner_nut_thickness, d=tensioner_nut_diam, $fn=6);
            }
        }
         translate([0,0, -tip_tensioner_height/2 + tensioner_nut_diam/2 + 0.1 ])
        rotate([90,00,0])
        cylinder (d=tensioner_bolt_diam, h=tip_tensioner_length, center=true);
    }
}

module make_washer_clamp(){
		translate([4,0,1])
		rotate([0,0,90]){
			intersection(){
	difference(){
			cube([tip_tensioner_length + 2, tip_tensioner_width/2 + 1.75
			, tip_tensioner_height], true);

			translate([0, tip_tensioner_width/4+ 0.0001,0.0001])
			cube([tip_tensioner_length + 0.25
			, tip_tensioner_width/2 + 0.25
			, tip_tensioner_height+0.0003], true);

			translate([0,0, -tip_tensioner_height/2 + tensioner_nut_diam/2.5 + 0.1 ])
			rotate([90,00,0])
			cylinder (d=tensioner_bolt_diam, h=tip_tensioner_length, center=true);
		}
					resize([tip_tensioner_length*1.6,tip_tensioner_width*1.6,0])
			cylinder (d=tip_tensioner_length, h=tip_tensioner_length, center=true);

			}
	}
 }

module make_middle(){
	difference(){
		union(){
			difference(){
				//main section
				union(){
					//main middle cylinder
                    difference(){
                        resize([middle_diameter_width,0,0])
					cylinder (h=total_middle_length, d=middle_diameter, center=true);

                        translate([0,hinge_diameter/2+tunnel_radius,0])
                       cube([middle_diameter,middle_diameter,total_middle_length],center=true);

                    //trim bottom
                     translate ([0, hinge_diameter, 0 ])
				cube([middle_width +.1, hinge_diameter, middle_length*1.5 ], center=true);
		               //top midle
                    translate ([0, -(hinge_diameter/2) , 0 ])
					cube([middle_width +.1, hinge_diameter, middle_length-hinge_diameter * 0.9 ], center=true);
                        for (i=[-1:2:1])
                        translate([i * (middle_width+.01), 0, 0])
					cube([middle_width, hinge_diameter*2,total_middle_length+.02], center=true);

                    }

					hinge_circles();

                        //top struts
                      for (i=[-1:2:1])
                      translate([ i*(middle_width/2 - middle_strut_width/2 -tunnel_clearance ),  -(hinge_diameter/2 ),0 ])
                    make_strut();

                        //bottom struts
                    for (i=[-1:2:1])
                      translate([ i*(middle_width/2 - middle_strut_width/2 -tunnel_clearance ),
                       (hinge_diameter/2- middle_strut_width/2 - hinge_indent_depth)+.0001,0 ])
                    make_strut();
				}

				//top elastic holefrom base
                for (j=[-1:2:1])
                hull(){
                    for (i=[-1:2:1])
                        translate([ i*  -(tunnel_radius+tunnel_clearance), top_tunnel_height, j*(middle_length/2 +8) ])
                        cylinder (r=tunnel_radius, h=16, center=true);
                    translate([0,top_tunnel_height ,0])
                    resize([0.01,0,0])
                    sphere(tunnel_radius+.3);
                }

				//hinge indent

                for (i=[-1:2:1])
				rotate([0,90,0]) {
					translate([i*-middle_length/2,0,0]) {
						difference(){
							cylinder (r=hinge_diameter/2+.1, h=hinge_indent_width, center=true);
                        cylinder (r=hinge_diameter/2- hinge_indent_depth, h=hinge_indent_width+.1, center=true); //HACK constant
						translate([i*middle_length/4,0,0])// + tunnel_radius - tunnel_clearance,0])
					cube ([middle_length/2, hinge_diameter-hinge_indent_depth*2 - 0.0001, 10], center=true);
						}
					}
					//flat indent for bottom
					translate([0,hinge_diameter/2,0])// + tunnel_radius - tunnel_clearance,0])
					cube ([middle_length,hinge_indent_depth*2,hinge_indent_width], center=true);
				}
			}

			if(middle_sides == 0)
			make_bumper();

            //lateral struts
               //top
			   st_len = middle_width-middle_strut_width/2-tunnel_clearance/2-.05;
             translate([ 0, -hinge_diameter/2 + middle_strut_width/2,
             -middle_strut_width/2])
            rotate([0,90,0])
            make_strut(length=st_len);
			//bottom
			 translate([ 0, hinge_diameter/2 - middle_strut_width/2 + 0.25,
             middle_strut_width/2])
            rotate([0,90,0])
            make_strut(length=st_len);

		}

		//hinge pins
		rotate([0,90,0]) {
			for (i=[-1:2:1])
			translate([i*middle_length/2,0,0])
			cylinder (r=hinge_pin_radius, h=middle_width*2, center=true);
		}
	}
}

module hinge_circles(){
						//hinge circles
					rotate([0,90,0])
					for (i=[-1:2:1])
					translate([i*middle_length/2,0,0])
					cylinder (d=hinge_diameter, h=middle_width, center=true);

}

module make_strut(length=middle_length){
    intersection(){
    cube([middle_strut_width,middle_strut_width,length],center=true);
        cylinder(d=middle_strut_width*1.3, h=length,center=true );
    }
}

module make_bumper(){
	union(){
		//resize([20,0,0])
		intersection(){

			cylinder (h=bumper_length, d=hinge_outer_width, center=true);

			difference(){
				resize([0,middle_diameter,0])
				cylinder (h=bumper_length, d=middle_diameter_width, center=true);
				//cut middle
				cube([bumper_width, bumper_height, bumper_length +.1], center=true);

//TODO - for children
#resize([middle_diameter_width, hinge_outer_diameter,hinge_outer_diameter])
//hull()
hinge_circles();
				hull(){
					//center cut
					resize([0,hinge_diameter*1.2,0])
					cylinder(d=middle_width-.25,h=middle_length,center=true);
					//top hole
                    for (i=[-1:2:1])
					translate([i*(tunnel_radius+tunnel_clearance), -(hinge_diameter/2 + tunnel_radius - tunnel_clearance*1.3), 0])
					cylinder (r=tunnel_radius, h=middle_length+hinge_diameter, center=true);
					//bottom tendon hole
					translate([0,hinge_diameter/2 ,0])
					cylinder (r=tunnel_radius, h=middle_length+hinge_diameter, center=true);
				}
			}

		hull(){
				resize([hinge_outer_width + hinge_plug_bulge, middle_diameter_width ,
				bumper_length*bumper_length_round  ])
				sphere( middle_diameter, center=true);

				difference(){
					cylinder (h=bumper_length, d=middle_diameter +.25, center=true);
				*	translate([0,tunnel_radius+tunnel_clearance,0])
					cube([middle_diameter+2,middle_diameter,bumper_length +.1], center=true);
				}
			}

					translate([0,-hinge_outer_diameter/2-1.5,0])
		cube([middle_length,hinge_outer_diameter*2,middle_diameter_width], center=true);

		}
	}
}

module make_plug(edge_clearance=0, depth_clearance=0, bulge=0, cutout=[0,0]){
	hh=hinge_plug_thickness;
	dd=hinge_plug_diameter - hinge_plug_ridge_height*2 + edge_clearance*2; //(hinge_plug_diameter-hinge_plug_clearance)*1;

	difference(){
		union(){
			if(bulge > 0){
				translate([0,0,hinge_plug_thickness/2 - .001 ])
				resize([0,0,bulge*2])
				sphere(dd/2);
			}
			//main plug
			translate([0,0, -depth_clearance/2+0.001 ])
			cylinder(d2=dd, d1=hinge_plug_diameter+edge_clearance*2, h=hinge_plug_thickness , center=true);
			//inside clearance
		    translate([0,0, - (hinge_plug_thickness + depth_clearance/2 )/2 +.0001])
            cylinder(d=hinge_plug_diameter+edge_clearance*2, h=depth_clearance/2 , center=true);
			//outside clearance
		  translate([0,0,  (hinge_plug_thickness - depth_clearance/2 )/2 +.0001])
            cylinder(d=dd, h=depth_clearance/2 , center=true);
		}
		translate([0,0, ( -hh/2 +cutout[0]/2) ])
		cylinder(d=cutout[1], h=cutout[0]+.01, center=true);
	}
}

module make_base(){
	union(){
		//cut center
		difference (){
			//mainsection
			union(){
                difference(){
				make_hinges();

                //trim extra at bottom
                  translate([0,0,-hinge_outer_diameter/2 - base_extra_length/2 +0.0001 + hinge_bend_padding] )
                   cylinder (d=hinge_outer_width*2, h=abs(base_extra_length+2), center=true);
            }

					//main cylinder
				translate([0,0,-base_body_length+hinge_bend_padding])
				intersection(){
                    hull(){
                    resize([middle_diameter_width,0,0])
                        translate([0,0,base_body_length + hinge_bend_padding -0.0001] )
					cylinder (d=middle_diameter, h=hull_cyl_height, center=false);

					translate([0,base_tendon_offset,0])
                    cylinder (d=base_total_width, h=hull_cyl_height, center=false);
                    }

					//test = base_total_width/2 - hinge_diameter;

					//rounded front
					hull(){
				//	translate([0, -hinge_outer_width*.53 ,0])
				//	cylinder (d=hinge_outer_width*2 , h=.5, center=true);
					translate([0,-1.6 ,0])
					cube([hinge_outer_width,hinge_outer_width,0.5], center=true);

					translate([0, -hinge_outer_width*.5 + hinge_diameter/2, base_body_length+1])
					//cylinder (d=hinge_outer_width*2 , h=.1, center=true);
					cube([hinge_outer_width,hinge_outer_width,0.1], center=true);
					}
				}

				//Socket interface
				translate([0,0,-(base_body_length -hinge_bend_padding  +socket_interface_length -0.5001)]) {
					cylinder (d1=socket_interface_bottom,
					d2=socket_interface_top,
					h=socket_interface_length - 0.5, center=false);
					//flattened bottom
					translate([0,0,-0.5])
					cylinder (d=socket_interface_bottom,h=0.5, center=false);

					//orientation slot
			*		intersection(){
						cylinder (d1=base_total_width + socket_slot_depth_bottom,
						 d2=middle_diameter-2 + socket_slot_depth_top, h=socket_interface_length, center=false);
						translate([-socket_slot_width/2,0,0])
						cube([socket_slot_width, base_total_width, socket_interface_length]);
					}
				}
			}
//base_breather
            translate([0,0,-base_length])
            cylinder (d=base_breather_diameter, h=base_length, center=false);

			inside_hinge_cut();

			//pin
			rotate([0,90,0]){
				cylinder(h = middle_width*3, r=hinge_pin_radius, center=true);
				// cut dips around hole for axle nuts
                get_plug_cutout();
			}

		 tendon_factor = .9;

           * if (skeleton == 1){
                slot_len = base_body_length + hinge_bend_padding- tunnel_clearance*3;
                translate([0,-10,-slot_len/2 + hinge_bend_padding- tunnel_clearance ])
                cube([middle_width/2, 20, slot_len ], center=true);
            }

			//tendon hole
		//	if(!skeleton)
			hull(){
				translate([0, hinge_diameter/2,// + tunnel_radius - tunnel_clearance*2) +2.5 ,
                            - tunnel_radius*2 - tunnel_clearance])
				sphere (tunnel_radius * tendon_factor);

			translate([0, -base_hump, -base_body_length + tunnel_radius + tunnel_clearance*1.5])
				resize([3.5,0,0])
				sphere (tunnel_radius* tendon_factor);

               translate([0,-(hinge_diameter/2 + tunnel_radius - tunnel_clearance*2) +8 ,
                            -hinge_diameter/2 +.2])
				sphere (tunnel_radius* tendon_factor);
			}

			//elastic hole
            hull(){
				//join hinge side tunnels
				for (i=[-1:2:1])
					if (!skeleton){
						translate([i*(tunnel_radius*2), top_tunnel_height, tunnel_radius   ])
						sphere (tunnel_radius * 1.25);
					}else{
						translate([i*(tunnel_radius*2), top_tunnel_height ,0])
						cylinder(d=tunnel_radius*1.8,h=tunnel_radius*2,center=true);
						//*	sphere (tunnel_radius * 1.2);
					}
			}
			//main taunnels
			for (i=[-1:2:1]){
				hull(){
					*translate([i*(tunnel_radius*2), top_tunnel_height ,-2])
					sphere (tunnel_radius );

					translate([i*(tunnel_radius*2), top_tunnel_height , skeleton ? -tunnel_radius*2 : tunnel_radius ])
				sphere (tunnel_radius * skeleton ? 1.5 : 1.2 );

					translate([i*(tunnel_radius *2.8 ),-hinge_diameter/2 -tunnel_radius ,-base_body_length -tunnel_radius*2  ])
					sphere (tunnel_radius );
				}
				//join stump side tunnels
				hull()
					for (i=[-1:2:1])
						translate([i*(tunnel_radius *2.8 ),-hinge_diameter/2-tunnel_radius ,-base_body_length -tunnel_radius*3 ])
						sphere (tunnel_radius*1.1);
					}

			//stump indent
			translate ([0,0,(-base_length -stump_indent) +stump_indent_offset -2.5]) //socket_catch_height*2
			sphere (stump_indent);//, $fn=fast?80:fn_accurate);
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

module inside_hinge_cut(){
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
						translate([hinge_diameter/2 +1.25, hinge_diameter*1.5, 0]) //add 1 to drop it a bit
						//cylinder (d=hinge_outer_diameter, h=middle_width+hinge_side_clearance*2, center=true);
						cube([.1,.1,middle_width+hinge_side_clearance*2], center=true);
					}
				}
				//flat interface
				translate ([0,-hinge_diameter/2 , 2.5+ hinge_bend_padding ])
				cube([middle_width+hinge_side_clearance*2+.001, 5, 4], true);
			}

}

module get_plug_cutout(){
        for (i=[-1:2:1]){
        translate([0,0,i * hinge_outer_width/2]){
               rotate( [i==-1?180:0,0,0])
                translate([0,0, -(hinge_plug_thickness  - 0.001)/2 ])
                make_plug(edge_clearance=hinge_plug_clearance, depth_clearance=hinge_plug_side_clearance, bulge=.75);

                translate([0, 0, i * (0.999)])
                rotate( [i==1?180:0,0,0])
                cylinder(h = 2, d2=hinge_outer_diameter-1.1, d1=hinge_outer_diameter+1, center=true);
     }
 }
}

module make_socket(){
//			s_top = base_total_width + socket_thickness_top*2;
//		socket_hinge_notch = socket_catch_height/2;
						sl = socket_depth - socket_depth_scallop_left;
	sl2 = socket_width_bottom*socket_width_scallop;
						sr = socket_depth - socket_depth_scallop_right;
			sr2 = socket_width_bottom*socket_width_scallop;
			sh = socket_width_bottom/2 + socket_thickness_bottom*socket_taper;
			dd = socket_depth - socket_depth_bottom;

	difference(){
		//main socket body
		cutout_length = socket_interface_length +socket_interface_clearance_top +0.0002;
		union(){
			translate ([0,0,-socket_interface_length-socket_vertical_clearance])
			difference(){
				//top portion
				cylinder (
					d1= socket_width_top +  socket_thickness_mid*2//base_total_width + socket_thickness_top*2
					, d2=base_total_width
					, h=socket_interface_length + socket_interface_clearance_top , center=false);
				//inside cutout
				translate([0,0,-0.0001]){
					cylinder (d1=socket_interface_bottom
						, d2=socket_interface_top
						, h=cutout_length - 0.5, center=false);
					translate([0,0, - 0.4999])
					cylinder (d= socket_interface_bottom
						, h=0.5, center=false);
			}

				//trim round outside rim
	*%	translate([0,0,-0.001])
					difference(){
						cylinder(h=socket_interface_length+socket_interface_clearance_top //+1.002
						, d=socket_width_top*2, center=false);
						translate([0,0,-0.0001])
						cylinder(h=socket_interface_length +socket_interface_clearance_top
						, d1=socket_width_top + socket_thickness_mid*2
						, d2=socket_width_top + socket_thickness_mid*2 - socket_interface_taper , center=false);
						}

					//socket interface cut
					translate([0,0,socket_interface_length/2+0.5])
					cylinder(h=socket_interface_length/2
						, d=socket_interface_top + socket_interface_clearance );

				}
			translate ([0,0, - socket_interface_length -socket_vertical_clearance - socket_depth/2 ])
			cylinder(h = socket_depth
			, r1=(socket_width_bottom/2.0) + socket_thickness_bottom
			, r2= socket_width_top /2 +  socket_thickness_mid  //base_total_width/2 + socket_thickness_mid
			, center=true);
		}

        //start cuts
	 	//extra cut - HACK
	*#	translate ([0,0,-socket_interface_length ])
		difference(){
			cylinder (d1=s_top+1, d2=s_top, h=socket_interface_length, center=false);
			cylinder (d1=base_total_width + socket_thickness_top, d2=base_total_width, h=socket_interface_length+socket_interface_clearance_top, center=false);
		}

		//cut interface points out at top - post section
		translate([0,0, -socket_vertical_clearance+.01]){

		*intersection(){
				cylinder (d1=base_total_width +socket_slot_depth_bottom, d2=middle_diameter-2 +socket_slot_depth_top, h=socket_interface_length, center=false);
				translate([-(socket_slot_width+.1)/2,0,0])
				cube([socket_slot_width+.1,base_total_width,socket_interface_length]);
			}

			//cut center of socket
			if (socket_ridge_depth > 0 && socket_ridge_spacing > 0){
                socket_ridge_total = socket_ridge_depth +socket_ridge_spacing;
                for (i=[0:1:socket_ridge_number/2]){
                 percent = i / socket_ridge_number *2;
                    for (j=[0:1:1]){
                     translate ([0,0,-socket_interface_length  - socket_depth * percent - (socket_ridge_spacing * j) ])
                       cylinder(h = socket_ridge_spacing+.1, r=socket_width_top/2 + socket_width_diff * percent + (socket_ridge_depth*j), center=false);
                    }
                }
            }else{
                translate ([0,0,-socket_interface_length-socket_depth +.01])
                cylinder(h = socket_depth, r2=socket_width_top/2, r1=socket_width_bottom/2, center=false);
            }
		}
//HACK HACK HACKS  post, catch go away
		//String clearance hack
		hull(){
			translate ([-10,-socket_width_top/2 -10.5, 0])
			cube([20, 10, 1]);
			translate ([-10,-socket_width_top/2 - 12, -(socket_catch_height  + socket_post_height)*2.8])
			cube([20, 10, 1]);
		}

		//scallops
		if (socket_depth_scallop_left > 0){

			union(){
				translate ([-1 * socket_width_bottom/2, 0, -(socket_depth + socket_catch_height + socket_post_height)-1])
				resize([socket_width_bottom,sl2,sl*2 +2])
				sphere (sl);
			}
		}
		if (socket_depth_scallop_right > 0){
			union(){
				translate ([socket_width_bottom/2, 0, -(socket_depth + socket_catch_height + socket_post_height)-1])
				resize([socket_width_bottom,sr2,sr*2 +2])
				sphere (sr);
			}
		}

		//Taper
		if(socket_taper > 0){

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

			translate([0,socket_thickness_bottom*3,-socket_depth - (socket_catch_height + socket_post_height) -.1])
			cylinder(d=socket_width_bottom+1, h=dd);
		}
//echo (bl=base_body_length);
//TODO fix
translate([0,0,base_body_length])
		inside_hinge_cut();
	}
}

module make_linkage(){
	//[0:Plain,1:Hole,2:inloop,3:Loop,4:Cup ]
	//rotate([0,0,180])
	difference(){
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

            //skeleton mode
            if ( skeleton == 1) {
            num = linkage_length / (slot_len + slot_spacing);
            for(i=[-num/2+1 : 1 : num/2-2])
            translate([0,0, i*(slot_len + slot_spacing) ])//- slot_spacing])
            rotate([90,0,0])
            hull(){
                make_hole(width=slot_width);
                translate([0,slot_len - slot_width*2,0])
                make_hole(width=slot_width);
            }
        }

			//holes
			if (linkage_end2 == 1){
				translate ([0,0,-linkage_length+linkage_hole_length])
				make_hole();
			}
			if (linkage_end1 == 1){
				translate ([0,-0.15, linkage_length-linkage_hole_length])
				make_hole();
			}


                    		//loops
		if (linkage_end2 == 2){

		}
		if (linkage_end1 == 2){
			translate ([0,0,linkage_length/2  ])//+ linkage_end1_length/2  - linkage_end1_thickness + linkage_end1_offset
			make_inloop();
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

	translate([0,linkage_height/2+1  - linkage_bottom_trim,0])
	cube([linkage_width, 2, linkage_length*2], center=true);
}

}

module make_inloop(){
    loop_len = 3;
    center_diam = linkage_width/2.5;
// #   translate([0,-4,0])
    union(){
        translate([0,0,-loop_len/2 +0.001])
	make_hole(length= loop_len);

    translate([0,0,-linkage_width/2 -loop_len + 0.75]){

           rotate([0,90,0])
            translate([ center_diam *.9,0,0])
			resize([3,0,0])
        make_hole(length= linkage_width + 0.0001);


    difference(){
        intersection(){
//            resize([linkage_width,0,linkage_width])
            rotate([90,0,0])
            cylinder(h=linkage_hole_radius*1.75, d=linkage_width, center=true);
            cylinder(h=linkage_length, d=linkage_width - tunnel_clearance*2, center=true);
        }
        rotate([90,0,0])
        cylinder(h=linkage_hole_radius*1.75+0.0001, d=center_diam, center=true);
    }
}}
}
module make_hole(length=linkage_hole_length, width=linkage_hole_radius){
	intersection(){
		cylinder(h = length, r=width, center=true);
		cube([width*1.75, width*1.75,length], center=true);
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

			translate([-1.65,-2.5,0])
			resize([2,2,linkage_hookheight])
			sphere(1.75);
		}
	}
	translate([0,-linkage_height/2.9,0])
	intersection(){
	cube([linkage_hook_width,linkage_height/4,linkage_hook_length/2], center=true);
	resize([0,linkage_height/4,0])
	translate([0,1,0])
	cylinder(d=linkage_hook_width, h=linkage_hook_length, center=true);
	}
}