$fa = 6; 
$fs = 1;


union() {
	color(c = "blue") {
		union() {
			difference() {
				translate(v = [0, -4.5100000000, 0]) {
					rotate(a = [90, 0, 0]) {
						cylinder(h = 5.2000000000, r1 = 9.3718317562, r2 = 10.1718317562);
					}
				}
				translate(v = [0, -4.4900000000, 0]) {
					rotate(a = [90, 0, 0]) {
						union() {
							cylinder(h = 5.3000000000, r1 = 7.5718317562, r2 = 8.6718317562);
							translate(v = [0, 0, 4.6900000000]) {
								cylinder(h = 0.5000000000, r = 8.6718317562);
							}
						}
					}
				}
			}
			translate(v = [0, -9.7100000000, 0]) {
				rotate(a = [90, 0, 0]) {
					union() {
						cylinder(h = 4, r1 = 10.1718317562, r2 = 10.8718317562);
						translate(v = [0, 0, 4]) {
							cylinder(h = 22.0000000000, r1 = 10.8718317562, r2 = 11.3676064717);
						}
					}
				}
			}
		}
	}
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
	translate(v = [0, 24, 0]) {
		union() {
			difference() {
				union() {
					hull() {
						union() {
							difference() {
								translate(v = [0, 5.5000000000, 0]) {
									rotate(a = [90, 0, 0]) {
										cylinder(center = false, h = 0.1000000000, r = 7.4802823253);
									}
								}
								translate(v = [-7.5000000000, 5.2500000000, 0]) {
									cube(center = true, size = [9.0000000000, 1, 16.0000000000]);
								}
							}
							difference() {
								union() {
									translate(v = [0, 0, -8.0000000000]) {
										rotate_extrude(angle = 360, convexity = 1) {
											offset(r = 1.5000000000) {
												offset(chamfer = false, delta = -1.5000000000) {
													union() {
														square(size = [4.5000000000, 16.0000000000]);
														square(size = [1.5000000000, 16.0000000000]);
													}
												}
											}
										}
									}
									difference() {
										cylinder(center = true, h = 13.4000000000, r = 1.8200000000);
										cylinder(center = true, h = 9.1000000000, r = 2.8200000000);
										cylinder(center = true, h = 16.0100000000, r = 1.0700000000);
									}
								}
								cylinder(center = true, h = 16.0100000000, r = 1.0700000000);
								cylinder(center = true, h = 9.6000000000, r = 4.9000000000);
							}
						}
					}
					hull() {
						union() {
							translate(v = [0, 3.6000000000, 0]) {
								difference() {
									hull() {
										translate(v = [4.0000000000, -3.6000000000, 5.5500000000]) {
											translate(v = [-0.2000000000, -0.5333333333, 0.8000000000]) {
												sphere(r = 0.8000000000);
											}
										}
										translate(v = [4.0000000000, -3.6000000000, -5.5500000000]) {
											translate(v = [-0.2000000000, -0.5333333333, -0.8000000000]) {
												sphere(r = 0.8000000000);
											}
										}
										translate(v = [4.9000000000, -3.6000000000, -3.0000000000]) {
											rotate(a = [90, 0, 0]) {
												cylinder(h = 0.0100000000, r = 1.6000000000);
											}
										}
										translate(v = [4.9000000000, -3.6000000000, 3.0000000000]) {
											rotate(a = [90, 0, 0]) {
												cylinder(h = 0.0100000000, r = 1.6000000000);
											}
										}
									}
									hull() {
										translate(v = [0, 2, 0]) {
											translate(v = [0, 0, -5.0000000000]) {
												rotate_extrude(angle = 360, convexity = 1) {
													offset(r = 1.2000000000) {
														offset(chamfer = false, delta = -1.2000000000) {
															union() {
																square(size = [3.5000000000, 10.0000000000]);
																square(size = [1.2000000000, 10.0000000000]);
															}
														}
													}
												}
											}
										}
										translate(v = [0, -10, 0]) {
											translate(v = [0, 0, -5.0000000000]) {
												rotate_extrude(angle = 360, convexity = 1) {
													offset(r = 1.2000000000) {
														offset(chamfer = false, delta = -1.2000000000) {
															union() {
																square(size = [5.2500000000, 10.0000000000]);
																square(size = [1.2000000000, 10.0000000000]);
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
								translate(v = [0, 5.5000000000, 0]) {
									rotate(a = [90, 0, 0]) {
										cylinder(center = false, h = 0.1000000000, r = 7.4802823253);
									}
								}
								translate(v = [-7.5000000000, 5.2500000000, 0]) {
									cube(center = true, size = [9.0000000000, 1, 16.0000000000]);
								}
							}
						}
					}
					translate(v = [0, 6.4900000000, 0]) {
						rotate(a = [90, 0, 0]) {
							union() {
								cylinder(center = true, h = 2.0000000000, r = 5.3552823253);
								translate(v = [0, 0, -1.6900000000]) {
									cylinder(center = true, h = 1.5500000000, r = 6.2302823253);
								}
							}
						}
					}
					union() {
						translate(v = [-2.7052823253, 11.3000000000, 1.6000000000]) {
							rotate(a = [0, 20, 0]) {
								difference() {
									union() {
										translate(v = [0, 0.8500000000, 0]) {
											resize(newsize = [2.5000000000, 0, 0]) {
												rotate(a = [90, 0, 0]) {
													translate(v = [0, 0, 0]) {
														rotate_extrude(angle = 360, convexity = 1) {
															offset(r = 0.2000000000) {
																offset(chamfer = false, delta = -0.2000000000) {
																	union() {
																		square(size = [2.0000000000, 1.8000000000]);
																		square(size = [0.2000000000, 1.8000000000]);
																	}
																}
															}
														}
													}
												}
											}
										}
										translate(v = [0, -0.7000000000, 0]) {
											resize(newsize = [2.5000000000, 0, 2.6666666667]) {
												rotate(a = [90, 0, 0]) {
													cylinder(center = false, h = 1.9000000000, r = 2.0000000000);
												}
											}
										}
									}
									translate(v = [0, 0.5500000000, 0]) {
										cube(center = true, size = [2.6000000000, 3.3000000000, 0.5000000000]);
									}
								}
							}
						}
						translate(v = [-2.7052823253, 11.3000000000, -1.6000000000]) {
							rotate(a = [0, -20, 0]) {
								difference() {
									union() {
										translate(v = [0, 0.8500000000, 0]) {
											resize(newsize = [2.5000000000, 0, 0]) {
												rotate(a = [90, 0, 0]) {
													translate(v = [0, 0, 0]) {
														rotate_extrude(angle = 360, convexity = 1) {
															offset(r = 0.2000000000) {
																offset(chamfer = false, delta = -0.2000000000) {
																	union() {
																		square(size = [2.0000000000, 1.8000000000]);
																		square(size = [0.2000000000, 1.8000000000]);
																	}
																}
															}
														}
													}
												}
											}
										}
										translate(v = [0, -0.7000000000, 0]) {
											resize(newsize = [2.5000000000, 0, 2.6666666667]) {
												rotate(a = [90, 0, 0]) {
													cylinder(center = false, h = 1.9000000000, r = 2.0000000000);
												}
											}
										}
									}
									translate(v = [0, 0.5500000000, 0]) {
										cube(center = true, size = [2.6000000000, 3.3000000000, 0.5000000000]);
									}
								}
							}
						}
						translate(v = [-0.0552823253, 11.3000000000, 3.0000000000]) {
							rotate(a = [0, 75, 0]) {
								difference() {
									union() {
										translate(v = [0, 0.8500000000, 0]) {
											resize(newsize = [2.5000000000, 0, 0]) {
												rotate(a = [90, 0, 0]) {
													translate(v = [0, 0, 0]) {
														rotate_extrude(angle = 360, convexity = 1) {
															offset(r = 0.2000000000) {
																offset(chamfer = false, delta = -0.2000000000) {
																	union() {
																		square(size = [2.0000000000, 1.8000000000]);
																		square(size = [0.2000000000, 1.8000000000]);
																	}
																}
															}
														}
													}
												}
											}
										}
										translate(v = [0, -0.7000000000, 0]) {
											resize(newsize = [2.5000000000, 0, 2.6666666667]) {
												rotate(a = [90, 0, 0]) {
													cylinder(center = false, h = 1.9000000000, r = 2.0000000000);
												}
											}
										}
									}
									translate(v = [0, 0.5500000000, 0]) {
										cube(center = true, size = [2.6000000000, 3.3000000000, 0.5000000000]);
									}
								}
							}
						}
						translate(v = [-0.0552823253, 11.3000000000, -3.0000000000]) {
							rotate(a = [0, -75, 0]) {
								difference() {
									union() {
										translate(v = [0, 0.8500000000, 0]) {
											resize(newsize = [2.5000000000, 0, 0]) {
												rotate(a = [90, 0, 0]) {
													translate(v = [0, 0, 0]) {
														rotate_extrude(angle = 360, convexity = 1) {
															offset(r = 0.2000000000) {
																offset(chamfer = false, delta = -0.2000000000) {
																	union() {
																		square(size = [2.0000000000, 1.8000000000]);
																		square(size = [0.2000000000, 1.8000000000]);
																	}
																}
															}
														}
													}
												}
											}
										}
										translate(v = [0, -0.7000000000, 0]) {
											resize(newsize = [2.5000000000, 0, 2.6666666667]) {
												rotate(a = [90, 0, 0]) {
													cylinder(center = false, h = 1.9000000000, r = 2.0000000000);
												}
											}
										}
									}
									translate(v = [0, 0.5500000000, 0]) {
										cube(center = true, size = [2.6000000000, 3.3000000000, 0.5000000000]);
									}
								}
							}
						}
					}
				}
				union() {
					translate(v = [0, 0, 1.0000000000]) {
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
					translate(v = [0, 0, -1.0000000000]) {
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
					}
				}
				translate(v = [0, 9.0000000000, 0]) {
					rotate(a = [90, 0, 0]) {
						cylinder(center = true, h = 20, r = 1.6500000000);
					}
				}
				union() {
					cylinder(center = true, h = 9.6000000000, r = 4.9000000000);
					cylinder(center = true, h = 16.0100000000, r = 1.0700000000);
				}
				translate(v = [-2.8276411627, 2.8899000000, 0]) {
					rotate(a = [0, 90, 0]) {
						intersection() {
							cube(center = true, size = [5.2000000000, 5.2000000000, 5.6552823253]);
							resize(newsize = [6.6040000000, 0, 0]) {
								cylinder(center = true, d = 6.6040000000, h = 5.6552823253);
							}
						}
					}
				}
				resize(newsize = [0, 0, 9.6000000000]) {
					translate(v = [0, 9.0000000000, 0]) {
						translate(v = [0, -10, 0]) {
							translate(v = [0, 0, -5.0000000000]) {
								rotate_extrude(angle = 360, convexity = 1) {
									offset(r = 1.2000000000) {
										offset(chamfer = false, delta = -1.2000000000) {
											union() {
												square(size = [5.2500000000, 10.0000000000]);
												square(size = [1.2000000000, 10.0000000000]);
											}
										}
									}
								}
							}
						}
					}
				}
				translate(v = [-1, 0, 0]) {
					cylinder(center = true, h = 9.6000000000, r = 4.9000000000);
				}
			}
			difference() {
				cylinder(center = true, h = 13.4000000000, r = 1.8200000000);
				cylinder(center = true, h = 9.1000000000, r = 2.8200000000);
				cylinder(center = true, h = 16.0100000000, r = 1.0700000000);
			}
		}
	}
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
	translate(v = [18.0000000000, -48, 0]) {
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
	union() {
		translate(v = [0, 0, -8.3600000000]) {
			color(c = [0, 0, 1]) {
				rotate(a = [0, 0, 90]) {
					union() {
						translate(v = [0, 0, -0.1125000000]) {
							cylinder(center = true, h = 0.9750000000, r1 = 2.9000000000, r2 = 3.2000000000);
						}
						translate(v = [0, 0, 0.4775000000]) {
							cylinder(center = true, h = 0.2250000000, r = 3.2000000000);
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
							translate(v = [0, 0, -0.1125000000]) {
								cylinder(center = true, h = 0.9750000000, r1 = 2.9000000000, r2 = 3.2000000000);
							}
							translate(v = [0, 0, 0.4775000000]) {
								cylinder(center = true, h = 0.2250000000, r = 3.2000000000);
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
							translate(v = [0, 0, -0.1125000000]) {
								cylinder(center = true, h = 0.9750000000, r1 = 2.9000000000, r2 = 3.2000000000);
							}
							translate(v = [0, 0, 0.4775000000]) {
								cylinder(center = true, h = 0.2250000000, r = 3.2000000000);
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
								translate(v = [0, 0, -0.1125000000]) {
									cylinder(center = true, h = 0.9750000000, r1 = 2.9000000000, r2 = 3.2000000000);
								}
								translate(v = [0, 0, 0.4775000000]) {
									cylinder(center = true, h = 0.2250000000, r = 3.2000000000);
								}
							}
						}
					}
				}
			}
		}
	}
}