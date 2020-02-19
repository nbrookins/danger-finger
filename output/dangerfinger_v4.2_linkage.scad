$fa = 4; 
$fs = 0.4;


rotate(a = [0, 0, 90]) {
	difference() {
		union() {
			rotate(a = [90, 90, 0]) {
				intersection() {
					resize(newsize = [7.0500000000, 4.4000000000, 0]) {
						translate(v = [0, 0, -35.0000000000]) {
							rotate_extrude(angle = 360, convexity = 1) {
								offset(r = 1.5000000000) {
									offset(chamfer = false, delta = -1.5000000000) {
										union() {
											square(size = [3.4000000000, 70]);
											square(size = [1.5000000000, 70]);
										}
									}
								}
							}
						}
					}
					cube(center = true, size = [6.8000000000, 4.4000000000, 70]);
				}
			}
			translate(v = [0.8000000000, -37.5000000000, 0]) {
				difference() {
					translate(v = [0, 0.6250000000, 0]) {
						resize(newsize = [6.0000000000, 11.0000000000, 6.8000000000]) {
							rotate(a = [0, 0, 160]) {
								rotate_extrude(angle = 300, convexity = 3) {
									hull() {
										translate(v = [1.5000000000, -3.4000000000, 0]) {
											circle(d = 1.2500000000);
										}
										translate(v = [1.5000000000, 3.4000000000, 0]) {
											circle(d = 1.2500000000);
										}
									}
								}
							}
						}
					}
					translate(v = [0, -0.2000000000, 0]) {
						difference() {
							translate(v = [-2, 1.8750000000, 0]) {
								cube(center = true, size = [2.5000000000, 2.5000000000, 6.8100000000]);
							}
							translate(v = [-2.1656050955, -2.0000000000, 0]) {
								resize(newsize = [5.2800000000, 0, 10.2000000000]) {
									sphere(r = 3.5789473684);
								}
							}
						}
					}
				}
			}
			hull() {
				union() {
					difference() {
						rotate(a = [90, 90, 0]) {
							intersection() {
								resize(newsize = [7.0500000000, 4.4000000000, 0]) {
									translate(v = [0, 0, -35.0000000000]) {
										rotate_extrude(angle = 360, convexity = 1) {
											offset(r = 1.5000000000) {
												offset(chamfer = false, delta = -1.5000000000) {
													union() {
														square(size = [3.4000000000, 70]);
														square(size = [1.5000000000, 70]);
													}
												}
											}
										}
									}
								}
								cube(center = true, size = [6.8000000000, 4.4000000000, 70]);
							}
						}
						translate(v = [0, 72.0000000000]) {
							cube(center = true, size = [20, 200, 20]);
						}
					}
					difference() {
						translate(v = [0.8000000000, -37.5000000000, 0]) {
							difference() {
								translate(v = [0, 0.6250000000, 0]) {
									resize(newsize = [6.0000000000, 11.0000000000, 6.8000000000]) {
										rotate(a = [0, 0, 160]) {
											rotate_extrude(angle = 300, convexity = 3) {
												hull() {
													translate(v = [1.5000000000, -3.4000000000, 0]) {
														circle(d = 1.2500000000);
													}
													translate(v = [1.5000000000, 3.4000000000, 0]) {
														circle(d = 1.2500000000);
													}
												}
											}
										}
									}
								}
								translate(v = [0, -0.2000000000, 0]) {
									difference() {
										translate(v = [-2, 1.8750000000, 0]) {
											cube(center = true, size = [2.5000000000, 2.5000000000, 6.8100000000]);
										}
										translate(v = [-2.1656050955, -2.0000000000, 0]) {
											resize(newsize = [5.2800000000, 0, 10.2000000000]) {
												sphere(r = 3.5789473684);
											}
										}
									}
								}
							}
						}
						translate(v = [0, -44.0000000000]) {
							cube(center = true, size = [20, 20, 20]);
						}
					}
				}
			}
		}
		resize(newsize = [1.6923076923, 0, 0]) {
			translate(v = [0, 35.0100000000, 0]) {
				rotate(a = [90, 90, 0]) {
					cylinder(h = 23.3333333333, r = 1.1000000000);
				}
			}
		}
		union() {
			translate(v = [0, 23.3333333333, 0]) {
				resize(newsize = [1.3750000000, 0, 0]) {
					cylinder(center = true, h = 7.8000000000, r = 1.1000000000);
				}
			}
			translate(v = [0, 26.3333333333, 0]) {
				resize(newsize = [1.3750000000, 0, 0]) {
					cylinder(center = true, h = 7.8000000000, r = 1.1000000000);
				}
			}
			translate(v = [0, 26.3333333333, -3.5789473684]) {
				rotate(a = [90, 90, 0]) {
					cylinder(h = 3, r = 0.6875000000);
				}
			}
			translate(v = [0, 26.3333333333, 3.5789473684]) {
				rotate(a = [90, 90, 0]) {
					cylinder(h = 3, r = 0.6875000000);
				}
			}
		}
	}
}