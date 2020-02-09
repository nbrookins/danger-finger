$fa = 4; 
$fs = 0.4;


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