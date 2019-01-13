// title      : Danger Finger
// author     : Nick Brookins
// license    : MIT License
// revision   : 0.001
// tags       :
// file       : finger.jscad

core_width = 8; //min 6? at 5, middle of tunnel needs to shrink, bumber cutouts larger
core_radius = core_width *0.95;

inter_length = 15;

inner_hinge_inset = 0.85;
inner_hinge_inset_border = 1;

tunnel_height_factor = 2.2;

tunnel_inset = 0.8;
tunnel_radius = 1.0;
tunnel_opening_radius = tunnel_radius *1.25;
tunnel_height = tunnel_radius*tunnel_height_factor;
split_width = 0.03;
core_height = core_radius *2 - tunnel_height*2;

hinge_thickness = 1.25;
hinge_clearance = 0.25;

hinge_pin_radius = 1.01;

bumper_inter_length = inter_length - tunnel_inset*6;
end_vert_offset = (core_radius-core_height/2) - tunnel_height;

function hinge_pin (){
    return cylinder ({r:hinge_pin_radius, h: core_width*2, center:true, fn: 128 });
}

function seg_intermediate(){
    rect = rotate([90,90,0],cylinder({r: core_radius, h: inter_length, fn: 128, center: true}));

    //attach ends with inset cutouts
   inset_width = core_width-inner_hinge_inset_border*2;

   inset_cyl = difference(
        cylinder({r:core_height/2, h:inset_width, fn:128, center: true}),
        cylinder({r:core_height/2-inner_hinge_inset, h:inset_width, fn:128, center: true}));

    end_cyl = rotate( [0,90,0],
        difference(cylinder({r: core_height/2, h: core_width, fn: 128, center: true}),
            inset_cyl));

    end_dist = translate([0,-inter_length/2, end_vert_offset], end_cyl);
    end_prox = translate([0, inter_length/2, end_vert_offset],end_cyl);

    //trim sides and bottom
    trim_top = translate ([0,0, core_width/2 + (core_height-core_radius) + tunnel_height ],
        cube ({size:[core_width, bumper_inter_length, core_width+inner_hinge_inset*2], center:true}));

    trim_bottom = translate ([0,0, -core_width/2 - (core_height-core_radius) - tunnel_height ],
        union(
            cube ({size:[core_width-inner_hinge_inset_border*2, inter_length*2, core_width+inner_hinge_inset*2], center:true})
            ,
            cube ({size:[core_width, inter_length*2, core_width], center:true})
            ));

    trim_side_offset = core_width/2 + core_radius/2 -0.001;
    trim_side_cube = cube ({size:[core_radius, inter_length*2, core_height*2 ], center:true});
    trim_side = union(translate ([trim_side_offset,0, 0 ], trim_side_cube),
        translate ([-trim_side_offset,0, 0 ], trim_side_cube));

    inter_core = difference(
                union(rect, end_dist, end_prox),
                trim_bottom, trim_side, trim_top);

    pins = rotate([0,90,0],
            union( translate([0,inter_length/2,0], hinge_pin()),
        translate([0,-inter_length/2,0], hinge_pin())));

    //Tunnels
    tunnel_cyl = rotate([90,90,0],
        cylinder({r:tunnel_radius, h:inter_length*2, fn:128, center:true }));

    tunnel_offset= tunnel_radius + tunnel_inset/2;
    tunnel_loffset = inter_length/2 - tunnel_radius/4;
    tunnel_sph =  sphere({r:tunnel_opening_radius});

    tunnels = union(
        translate([-tunnel_offset, -tunnel_loffset, core_height/2 - inner_hinge_inset + tunnel_radius], tunnel_cyl,tunnel_sph),
        translate([tunnel_offset, tunnel_loffset, core_height/2 - inner_hinge_inset + tunnel_radius], tunnel_cyl, tunnel_sph));

    //tunnel_hull = hull(translate([-tunnel_offset, -tunnel_loffset, core_height/2 - inner_hinge_inset + tunnel_radius], tunnel_cyl,tunnel_sph),
     //   translate([tunnel_offset, tunnel_loffset, core_height/2 - inner_hinge_inset + tunnel_radius], tunnel_cyl, tunnel_sph));

    //#middle cutout
    cut_len = (inter_length-core_height)/2.5;
    cutout_cube = cube({size:[core_width, cut_len, core_height-inner_hinge_inset*5 ],center: true});
    cutout = union(
        translate([0,-cut_len/2-tunnel_inset/2,0], cutout_cube)
        ,
        translate([0,cut_len/2+tunnel_inset/2,0], cutout_cube)
        );

    cutout_bot = translate([0,0,-core_height/2+inner_hinge_inset/2],
        cube({size:[core_width,
        inter_length-core_height+tunnel_inset, inner_hinge_inset],center:true}));

    return difference(
        inter_core,
        pins, tunnels
        //,
        //cutout,
    //    cutout_bot//, slice
    );

}

function bumper_intermediate(){
    slug =
     rotate([90,90,0],
            intersection(
                cylinder({r: core_radius, h: bumper_inter_length, fn: 128, center: true}),
                translate([-tunnel_radius*0.75, 0, 0],cylinder({r: core_radius, h: bumper_inter_length, fn: 128, center: true})),
                scale([1.2, 0.8, 1], cylinder({r: core_radius, h: bumper_inter_length, fn: 128, center: true}))));
   // */
    hinge_bumper_clearance = 1.1;

     end_cyl = rotate( [0,90,0],
        cylinder({r: core_height/2 * hinge_bumper_clearance,
            h: core_width*2, fn: 128, center: true}));

    end_dist = translate([0,-inter_length/2, end_vert_offset], end_cyl);
    end_prox = translate([0, inter_length/2, end_vert_offset],end_cyl);

    tunnel_cyl2 = rotate([90,90,0],
        cylinder({r:tunnel_radius*1.5,
            h:inter_length*2, fn:128, center:true }));

    tunnel_lower = translate([0, 0, -(core_height/2 - inner_hinge_inset )],
        tunnel_cyl2);

    tunnel_hull = translate([0,0,tunnel_height+0.5],
        rotate([90,90,0],
            cylinder({r: core_width/2-0.3,
                h: bumper_inter_length, fn: 128, center: true})));

    splt = color("Red",translate([0, 0, -(core_height/2 - inner_hinge_inset +tunnel_radius*2)],
        cube({size:[split_width, inter_length,2], center:true})));

    hinge_bottom_buffer = core_height / 2.0;

    //todo - duplicate this
    trim_bottom = union(
        cube ({size:[core_width, hinge_bottom_buffer, core_width], center:true}),
        translate ([0, 0, -tunnel_height],
            cube ({size:[core_width*2, hinge_bottom_buffer, core_width], center:true})));

    trim_bottom1 = translate ([0,
            -(inter_length/2 - hinge_bottom_buffer/2),
            -core_width/2 - (core_height/2) +tunnel_height],
            trim_bottom);

    trim_bottom2 = translate ([0,
            inter_length/2 - hinge_bottom_buffer/2,
            -core_width/2 - (core_height/2) +tunnel_height],
            trim_bottom);

    return difference(slug, trim_bottom1, trim_bottom2,
            end_dist, end_prox, tunnel_hull, tunnels,
            tunnel_lower, splt, inter_core);
}

function seg_distal(){
    core_cyl =  translate([0,inter_length/2,0],
                    rotate( [0,90,0],
                    cylinder({r: core_height/2 + hinge_clearance,
                    h: core_width + hinge_clearance*2, fn: 128, center: true}
                    )));

    hinge_cyl = translate([0,inter_length/2,0],
                    rotate( [0,90,0],
                    cylinder({r: core_height/2,
                    h: core_width + (hinge_thickness + hinge_clearance)*2, fn: 128, center: true}
                    )));

    hinge_core= translate([0,inter_length/2,0],
                    rotate( [90,0,0],
                    cylinder({r: core_radius,
                    h: core_height/2, fn: 128, center: true}
                    )));

    distal_length = 8;

    slug =
    translate([0,inter_length/2 + distal_length/2,0],
     rotate([90,90,0],
            intersection(
                cylinder({r: core_radius, h: distal_length, fn: 128, center: true}),
                translate([-tunnel_radius*0.75, 0, 0],
                cylinder({r: core_radius, h: distal_length, fn: 128, center: true})),
                scale([1.2, 0.8, 1],
                    cylinder({r: core_radius, h: distal_length, fn: 128, center: true}
                        )))));


    distal = union(hinge_cyl,slug);

    return difference(distal, core_cyl);
}

function main() {
    inter = color("Gray", seg_intermediate());
    bumper = color("LightGray", bumper_intermediate());
    distal = color("LightGray", seg_distal());

    return union(
       // color("Red", trim_bottom2),
        inter,
        distal,
        bumper
        );
        //*/
}

