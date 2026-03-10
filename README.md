# danger-finger
Source code for the DangerCreations danger-finger, a DIY 3D-printable prosthetic finger device.

This is a pre-release, in progress.  Use at own risk.  Latest stable version is available at: http://www.thingiverse.com/thing:1340624

You'll need to install Python3, and then once you have Python and Pip, do "pip3 install -r ./requirements.txt"
then simply run "python3 utility.py" to compile the project.  It will output a .scad file for each part as well as a compostite "all".  If you add the -r flag ("python3 utility.py -r"), it will attempt to locate OpenSCAD on your machine, and render the SCAD files into STL.  alterntately you can do this manually with each required scad file by performing RENDER and Export STL in OpenSCAD app.

-----------------------------------------------------------------------------------

The project is undergoing a major rewrite, from OpenSCAD to Python 3 + SolidPython2, a drastic improvement in reliable configuration to various shapes and sizes and needs as well as making the codebase easier to maintain and update.

For more information about how to build or have a prosthetic finger built, visit: http://dangercreations.com/prosthetics

#vscode and python extension
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
pip3 install -r ./requirements.txt
brew install docker
make

Run tests
--------

Install pytest if you don't have it already:

    pip3 install pytest

Run tests with:

    pytest -q

