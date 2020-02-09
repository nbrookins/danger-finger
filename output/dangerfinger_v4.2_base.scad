$fa = 4; 
$fs = 0.4;


union() {
	difference() {
		union() {
			difference() {
				union() {
					hull() {
						union() {
							translate(v = [0, -4.0000000000, 0]) {
								rotate(a = [90, 0, 0]) {
									cylinder(center = false, h = 0.5000000000, r = 9.3718317562);
								}
							}
							difference() {
								union() {
									translate(v = [0, 0, -9.0000000000]) {
										rotate_extrude(angle = 360, convexity = 1) {
											offset(r = 1.5000000000) {
												offset(chamfer = false, delta = -1.5000000000) {
													union() {
														square(size = [5.0000000000, 18.0000000000]);
														square(size = [1.5000000000, 18.0000000000]);
													}
												}
											}
										}
									}
									difference() {
										cylinder(center = true, h = 15.4000000000, r = 1.8200000000);
										cylinder(center = true, h = 9.9000000000, r = 2.8200000000);
										cylinder(center = true, h = 18.0100000000, r = 1.0700000000);
									}
								}
								cylinder(center = true, h = 18.0100000000, r = 1.0700000000);
								hull() {
									cylinder(center = true, h = 10.4000000000, r = 5.4000000000);
									translate(v = [-10, 0.7500000000, 0]) {
										cylinder(center = true, h = 10.4000000000, r = 5.4000000000);
									}
								}
							}
						}
					}
					hull() {
						union() {
							difference() {
								hull() {
									translate(v = [4.5000000000, 0, 6.5500000000]) {
										translate(v = [-0.2000000000, -0.5333333333, 0.8000000000]) {
											sphere(r = 0.8000000000);
										}
									}
									translate(v = [4.5000000000, 0, -6.5500000000]) {
										translate(v = [-0.2000000000, -0.5333333333, -0.8000000000]) {
											sphere(r = 0.8000000000);
										}
									}
									translate(v = [5.4000000000, 0, 3.4000000000]) {
										rotate(a = [90, 0, 0]) {
											cylinder(h = 0.0100000000, r = 1.6000000000);
										}
									}
									translate(v = [5.4000000000, 0, -3.4000000000]) {
										rotate(a = [90, 0, 0]) {
											cylinder(h = 0.0100000000, r = 1.6000000000);
										}
									}
								}
								hull() {
									translate(v = [0, 2, 0]) {
										translate(v = [0, 0, -5.2000000000]) {
											rotate_extrude(angle = 360, convexity = 1) {
												offset(r = 1.2000000000) {
													offset(chamfer = false, delta = -1.2000000000) {
														union() {
															square(size = [5.7500000000, 10.4000000000]);
															square(size = [1.2000000000, 10.4000000000]);
														}
													}
												}
											}
										}
									}
									translate(v = [0, -10, 0]) {
										translate(v = [0, 0, -5.2000000000]) {
											rotate_extrude(angle = 360, convexity = 1) {
												offset(r = 1.2000000000) {
													offset(chamfer = false, delta = -1.2000000000) {
														union() {
															square(size = [5.7500000000, 10.4000000000]);
															square(size = [1.2000000000, 10.4000000000]);
														}
													}
												}
											}
										}
									}
								}
							}
							translate(v = [0, -4.0000000000, 0]) {
								rotate(a = [90, 0, 0]) {
									cylinder(center = false, h = 0.5000000000, r = 9.3718317562);
								}
							}
						}
					}
				}
				translate(v = [0, 0, -8.3600000000]) {
					color(c = [0, 0, 1]) {
						rotate(a = [0, 0, 90]) {
							union() {
								translate(v = [0, 0, -0.1625000000]) {
									cylinder(center = true, h = 0.9750000000, r1 = 3.0000000000, r2 = 3.3000000000);
								}
								translate(v = [0, 0, 0.4775000000]) {
									cylinder(center = true, h = 0.3250000000, r = 3.3000000000);
								}
							}
						}
					}
				}
				rotate(a = [0, 180, 0]) {
					translate(v = [0, 0, -8.3600000000]) {
						color(c = [0, 0, 1]) {
							rotate(a = [0, 0, 90]) {
								union() {
									translate(v = [0, 0, -0.1625000000]) {
										cylinder(center = true, h = 0.9750000000, r1 = 3.0000000000, r2 = 3.3000000000);
									}
									translate(v = [0, 0, 0.4775000000]) {
										cylinder(center = true, h = 0.3250000000, r = 3.3000000000);
									}
								}
							}
						}
					}
				}
				translate(v = [0, 24, 0]) {
					translate(v = [0, 0, 7.2500000000]) {
						color(c = [0, 0, 1]) {
							rotate(a = [0, 0, 90]) {
								union() {
									translate(v = [0, 0, -0.1625000000]) {
										cylinder(center = true, h = 0.9750000000, r1 = 3.0000000000, r2 = 3.3000000000);
									}
									translate(v = [0, 0, 0.4775000000]) {
										cylinder(center = true, h = 0.3250000000, r = 3.3000000000);
									}
								}
							}
						}
					}
				}
				translate(v = [0, 24, 0]) {
					translate(v = [0, 0, -7.3400000000]) {
						rotate(a = [0, 180, 0]) {
							color(c = [0, 0, 1]) {
								rotate(a = [0, 0, 90]) {
									union() {
										translate(v = [0, 0, -0.1625000000]) {
											cylinder(center = true, h = 0.9750000000, r1 = 3.0000000000, r2 = 3.3000000000);
										}
										translate(v = [0, 0, 0.4775000000]) {
											cylinder(center = true, h = 0.3250000000, r = 3.3000000000);
										}
									}
								}
							}
						}
					}
				}
				union() {
					translate(v = [0, 0, 13.9900000000]) {
						cylinder(center = true, h = 10.0000000000, r = 3.5000000000);
					}
					translate(v = [0, 0, -13.9900000000]) {
						cylinder(center = true, h = 10.0000000000, r = 3.5000000000);
					}
				}
			}
			translate(v = [0, -4.4900000000, 0]) {
				rotate(a = [90, 0, 0]) {
					difference() {
						union() {
							cylinder(h = 4.7000000000, r1 = 7.2718317562, r2 = 8.3718317562);
							translate(v = [0, 0, 4.6900000000]) {
								cylinder(h = 0.5000000000, r = 8.3718317562);
							}
						}
						translate(v = [0, 0, 0.0100000000]) {
							translate(v = [0, 0, 4.9500000000]) {
								union() {
									resize(newsize = [0, 0, 7.9000000000]) {
										sphere(r = 7.6218317562);
									}
									translate(v = [0, 0, 0.0100000000]) {
										cylinder(h = 3.9500000000, r = 7.6218317562);
									}
								}
							}
						}
					}
				}
			}
		}
		translate(v = [0.8000000000, 0, 0]) {
			union() {
				hull() {
					cylinder(center = true, h = 10.4000000000, r = 5.4000000000);
					translate(v = [-10, 0.7500000000, 0]) {
						cylinder(center = true, h = 10.4000000000, r = 5.4000000000);
					}
				}
				cylinder(center = true, h = 18.0100000000, r = 1.0700000000);
			}
		}
		hull() {
			translate(v = [10.8718317562, -2.8000000000, 0]) {
				resize(newsize = [0, 0, 2.2000000000]) {
					rotate(a = [0, 90, 0]) {
						cylinder(center = true, h = 0.1000000000, r = 1.1000000000);
					}
				}
			}
			translate(v = [-2.7179579391, -3.8000000000, 0]) {
				rotate(a = [0, 90, 0]) {
					resize(newsize = [0, 0, 1]) {
						cylinder(center = true, h = 0.1000000000, r = 1.1000000000);
					}
				}
			}
		}
		hull() {
			translate(v = [4.3359158781, 0, 0]) {
				resize(newsize = [0, 0, 2.2000000000]) {
					rotate(a = [90, 0, 0]) {
						cylinder(center = true, h = 0.1000000000, r = 1.1000000000);
					}
				}
			}
			translate(v = [0, -9.2000000000, 2.6400000000]) {
				translate(v = [4.3359158781, 0, 0]) {
					resize(newsize = [0, 0, 2.2000000000]) {
						rotate(a = [90, 0, 0]) {
							cylinder(center = true, h = 0.1000000000, r = 1.1000000000);
						}
					}
				}
			}
		}
		hull() {
			translate(v = [4.3359158781, 0, 0]) {
				resize(newsize = [0, 0, 2.2000000000]) {
					rotate(a = [90, 0, 0]) {
						cylinder(center = true, h = 0.1000000000, r = 1.1000000000);
					}
				}
			}
			translate(v = [0, -9.2000000000, -2.6400000000]) {
				translate(v = [4.3359158781, 0, 0]) {
					resize(newsize = [0, 0, 2.2000000000]) {
						rotate(a = [90, 0, 0]) {
							cylinder(center = true, h = 0.1000000000, r = 1.1000000000);
						}
					}
				}
			}
		}
		translate(v = [0, -10, 0]) {
			rotate(a = [90, 0, 0]) {
				cylinder(center = true, h = 20, r = 2.0800000000);
			}
		}
		resize(newsize = [0, 0, 10.4000000000]) {
			translate(v = [0.2000000000, -2, 0]) {
				translate(v = [0, 2, 0]) {
					translate(v = [0, 0, -5.2000000000]) {
						rotate_extrude(angle = 360, convexity = 1) {
							offset(r = 1.2000000000) {
								offset(chamfer = false, delta = -1.2000000000) {
									union() {
										square(size = [5.7500000000, 10.4000000000]);
										square(size = [1.2000000000, 10.4000000000]);
									}
								}
							}
						}
					}
				}
			}
		}
		cylinder(center = true, h = 10.4000000000, r = 5.4000000000);
	}
	difference() {
		cylinder(center = true, h = 15.4000000000, r = 1.8200000000);
		cylinder(center = true, h = 9.9000000000, r = 2.8200000000);
		cylinder(center = true, h = 18.0100000000, r = 1.0700000000);
	}
}