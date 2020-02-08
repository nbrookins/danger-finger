$fa = 10; 
$fs = 1.5;


difference() {
	union() {
		translate(v = [0, 24, 0]) {
			union() {
				rotate(a = [180, 0, 0]) {
					difference() {
						cylinder(center = true, h = 9.2000000000, r = 4.5000000000);
						difference() {
							cylinder(center = true, h = 5.2000000000, r = 4.5100000000);
							cylinder(center = true, h = 5.2100000000, r = 3.6000000000);
						}
						cylinder(center = true, h = 9.2100000000, r = 1.0700000000);
					}
				}
				rotate(a = [180, 0, 0]) {
					translate(v = [0, 3.6000000000, 0]) {
						difference() {
							hull() {
								translate(v = [4.0000000000, -3.6000000000, 3.0000000000]) {
									rotate(a = [90, 0, 0]) {
										cylinder(h = 0.0100000000, r = 1.6000000000);
									}
								}
								translate(v = [4.0000000000, -3.6000000000, -3.0000000000]) {
									rotate(a = [90, 0, 0]) {
										cylinder(h = 0.0100000000, r = 1.6000000000);
									}
								}
								translate(v = [4.9000000000, -3.6000000000, -3.0100000000]) {
									rotate(a = [90, 0, 0]) {
										cylinder(h = 0.0100000000, r = 1.6000000000);
									}
								}
								translate(v = [4.9000000000, -3.6000000000, 3.0100000000]) {
									rotate(a = [90, 0, 0]) {
										cylinder(h = 0.0100000000, r = 1.6000000000);
									}
								}
								translate(v = [4.0000000000, 0, 2.8000000000]) {
									translate(v = [-0.2000000000, -0.5333333333, 0.8000000000]) {
										sphere(r = 0.8000000000);
									}
								}
								translate(v = [4.0000000000, 0, -2.8000000000]) {
									translate(v = [-0.2000000000, -0.5333333333, -0.8000000000]) {
										sphere(r = 0.8000000000);
									}
								}
								translate(v = [4.9000000000, 0, 2.2500000000]) {
									translate(v = [0.4000000000, -0.5333333333, 0.8000000000]) {
										sphere(r = 0.8000000000);
									}
								}
								translate(v = [4.9000000000, 0, -2.2500000000]) {
									translate(v = [0.4000000000, -0.5333333333, -0.8000000000]) {
										sphere(r = 0.8000000000);
									}
								}
							}
							hull() {
								translate(v = [0, 5.6000000000, 0]) {
									translate(v = [0, 0, -3.0000000000]) {
										rotate_extrude(angle = 360, convexity = 1) {
											offset(r = 1.2000000000) {
												offset(chamfer = false, delta = -1.2000000000) {
													union() {
														square(size = [5.2500000000, 6.0000000000]);
														square(size = [1.2000000000, 6.0000000000]);
													}
												}
											}
										}
									}
								}
								translate(v = [0, -6.4000000000, 0]) {
									translate(v = [0, 0, -3.0000000000]) {
										rotate_extrude(angle = 360, convexity = 1) {
											offset(r = 1.2000000000) {
												offset(chamfer = false, delta = -1.2000000000) {
													union() {
														square(size = [5.2500000000, 6.0000000000]);
														square(size = [1.2000000000, 6.0000000000]);
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
		difference() {
			cylinder(center = true, h = 10.0000000000, r = 5.0000000000);
			difference() {
				cylinder(center = true, h = 6.0000000000, r = 5.0100000000);
				cylinder(center = true, h = 6.0100000000, r = 4.1000000000);
			}
			cylinder(center = true, h = 10.0100000000, r = 1.0700000000);
		}
		hull() {
			translate(v = [0, 24, 0]) {
				translate(v = [3.6500000000, 0, 3.6000000000]) {
					rotate(a = [90, 0, 0]) {
						intersection() {
							cube(center = true, size = [1.7000000000, 2.0000000000, 0.0100000000]);
							resize(newsize = [1.9720000000, 0, 0]) {
								cylinder(center = true, d = 2.3200000000, h = 0.0100000000);
							}
						}
					}
				}
			}
			translate(v = [4.1500000000, 0, 4.0000000000]) {
				rotate(a = [90, 0, 0]) {
					intersection() {
						cube(center = true, size = [1.7000000000, 2.0000000000, 0.0100000000]);
						resize(newsize = [1.9720000000, 0, 0]) {
							cylinder(center = true, d = 2.3200000000, h = 0.0100000000);
						}
					}
				}
			}
		}
		hull() {
			translate(v = [0, 24, 0]) {
				translate(v = [3.6500000000, 0, -3.6000000000]) {
					rotate(a = [90, 0, 0]) {
						intersection() {
							cube(center = true, size = [1.7000000000, 2.0000000000, 0.0100000000]);
							resize(newsize = [1.9720000000, 0, 0]) {
								cylinder(center = true, d = 2.3200000000, h = 0.0100000000);
							}
						}
					}
				}
			}
			translate(v = [4.1500000000, 0, -4.0000000000]) {
				rotate(a = [90, 0, 0]) {
					intersection() {
						cube(center = true, size = [1.7000000000, 2.0000000000, 0.0100000000]);
						resize(newsize = [1.9720000000, 0, 0]) {
							cylinder(center = true, d = 2.3200000000, h = 0.0100000000);
						}
					}
				}
			}
		}
		hull() {
			translate(v = [0, 24, 0]) {
				translate(v = [-2.7500000000, 0, 0]) {
					rotate(a = [90, 0, 0]) {
						intersection() {
							cube(center = true, size = [1.7000000000, 2.6000000000, 0.0100000000]);
							resize(newsize = [1.9720000000, 0, 0]) {
								cylinder(center = true, d = 3.0160000000, h = 0.0100000000);
							}
						}
					}
				}
			}
			translate(v = [-3.2500000000, 0, 0]) {
				rotate(a = [90, 0, 0]) {
					intersection() {
						cube(center = true, size = [1.7000000000, 3.0000000000, 0.0100000000]);
						resize(newsize = [1.9720000000, 0, 0]) {
							cylinder(center = true, d = 3.4800000000, h = 0.0100000000);
						}
					}
				}
			}
		}
		translate(v = [0.5000000000, 12.0000000000, 0]) {
			hull() {
				union() {
					translate(v = [3.5000000000, 0, 0]) {
						intersection() {
							cube(center = true, size = [0.6000000000, 2.0000000000, 7.2000000000]);
							resize(newsize = [0.6960000000, 0, 0]) {
								cylinder(center = true, d = 2.3200000000, h = 7.2000000000);
							}
						}
					}
					translate(v = [3.5000000000, 0, 0]) {
						intersection() {
							cube(center = true, size = [0.6000000000, 2.0000000000, 8.8000000000]);
							resize(newsize = [0.6960000000, 0, 0]) {
								cylinder(center = true, d = 2.3200000000, h = 8.8000000000);
							}
						}
					}
				}
			}
		}
		translate(v = [0, 4.0000000000, 0]) {
			difference() {
				hull() {
					translate(v = [4.5000000000, -4.0000000000, 3.4000000000]) {
						rotate(a = [90, 0, 0]) {
							cylinder(h = 0.0100000000, r = 1.6000000000);
						}
					}
					translate(v = [4.5000000000, -4.0000000000, -3.4000000000]) {
						rotate(a = [90, 0, 0]) {
							cylinder(h = 0.0100000000, r = 1.6000000000);
						}
					}
					translate(v = [5.4000000000, -4.0000000000, -3.4100000000]) {
						rotate(a = [90, 0, 0]) {
							cylinder(h = 0.0100000000, r = 1.6000000000);
						}
					}
					translate(v = [5.4000000000, -4.0000000000, 3.4100000000]) {
						rotate(a = [90, 0, 0]) {
							cylinder(h = 0.0100000000, r = 1.6000000000);
						}
					}
					translate(v = [4.5000000000, 0, 3.2000000000]) {
						translate(v = [-0.2000000000, -0.5333333333, 0.8000000000]) {
							sphere(r = 0.8000000000);
						}
					}
					translate(v = [4.5000000000, 0, -3.2000000000]) {
						translate(v = [-0.2000000000, -0.5333333333, -0.8000000000]) {
							sphere(r = 0.8000000000);
						}
					}
					translate(v = [5.4000000000, 0, 2.6500000000]) {
						translate(v = [0.4000000000, -0.5333333333, 0.8000000000]) {
							sphere(r = 0.8000000000);
						}
					}
					translate(v = [5.4000000000, 0, -2.6500000000]) {
						translate(v = [0.4000000000, -0.5333333333, -0.8000000000]) {
							sphere(r = 0.8000000000);
						}
					}
				}
				hull() {
					translate(v = [0, 2, 0]) {
						translate(v = [0, 0, -3.4000000000]) {
							rotate_extrude(angle = 360, convexity = 1) {
								offset(r = 1.2000000000) {
									offset(chamfer = false, delta = -1.2000000000) {
										union() {
											square(size = [5.7500000000, 6.8000000000]);
											square(size = [1.2000000000, 6.8000000000]);
										}
									}
								}
							}
						}
					}
					translate(v = [0, -10, 0]) {
						translate(v = [0, 0, -3.4000000000]) {
							rotate_extrude(angle = 360, convexity = 1) {
								offset(r = 1.2000000000) {
									offset(chamfer = false, delta = -1.2000000000) {
										union() {
											square(size = [5.7500000000, 6.8000000000]);
											square(size = [1.2000000000, 6.8000000000]);
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	translate(v = [0, 24, 0]) {
		union() {
			translate(v = [0, 0, 6.5900000000]) {
				cylinder(center = true, h = 4, r = 4.7000000000);
			}
			translate(v = [0, 0, -6.5900000000]) {
				cylinder(center = true, h = 4, r = 4.7000000000);
			}
		}
	}
	union() {
		translate(v = [0, 0, 6.9900000000]) {
			cylinder(center = true, h = 4, r = 5.2000000000);
		}
		translate(v = [0, 0, -6.9900000000]) {
			cylinder(center = true, h = 4, r = 5.2000000000);
		}
	}
}