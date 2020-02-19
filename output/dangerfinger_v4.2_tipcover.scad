$fa = 4; 
$fs = 0.4;


rotate(a = [0, 0, 90]) {
	color(c = "blue") {
		hull() {
			union() {
				translate(v = [0, 35.0000000000, 0]) {
					rotate(a = [90, 90, 0]) {
						cylinder(h = 5.5000000000, r = 7.4802823253);
					}
				}
				translate(v = [-2.4934274418, 42.0131451165, 0]) {
					resize(newsize = [8.9763387904, 0, 13.4645081856]) {
						sphere(r = 4.9868548835);
					}
				}
			}
		}
	}
}