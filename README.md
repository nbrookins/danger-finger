# danger-finger
Source code for the DangerCreations danger-finger, a DIY 3D-printable prosthetic finger device.

This is a pre-release, in progress.  Use at own risk.  Latest stable version is available at: http://www.thingiverse.com/thing:1340624

You'll need to install Python3, and then once you have Python and Pip, do "pip3 install SolidPython"
then simply run "python3 utility.py" to compile the project.  It will output a .scad file, depending on flags and configuration.  By default, it will output all objects to a *preview.scad file.

To view the output install OpenScad from openscad.org, and open the scad file.  It can auto-preview, so that each time you compile the Pytyhon, you'll get an automatic preview.  

Lastly, RENDER the scad and then export an STL file for your printer.  In the future a web-interface and auto-render script will be provided for automating this part of the process.

-----------------------------------------------------------------------------------

The project is undergoing a major rewrite, from OpenSCAD to Python 3 + SolidPython, a drastic improvement in reliable configuration to various shapes and sizes and needs as well as making the codebase easier to maintain and update.

For more information about how to build or have a prosthetic finger built, visit: http://dangercreations.com/prosthetics
