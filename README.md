# danger-finger
Source code for the DangerCreations danger-finger, a DIY 3D-printable prosthetic finger device.

This is a pre-release, in progress.  Use at own risk.  Latest stable version is available at: http://www.thingiverse.com/thing:1340624

You'll need to install Python3, and then once you have Python and Pip, do "pip3 install -r ./requirements.txt"
then simply run "python3 utility.py" to compile the project.  It will output a .scad file for each part as well as a composite "all".  If you add the -r flag ("python3 utility.py -r"), it will attempt to locate OpenSCAD on your machine, and render the SCAD files into STL.  Alternatively you can do this manually with each required scad file by performing RENDER and Export STL in OpenSCAD app.

-----------------------------------------------------------------------------------

The project is undergoing a major rewrite, from OpenSCAD to Python 3 + SolidPython2, a drastic improvement in reliable configuration to various shapes and sizes and needs as well as making the codebase easier to maintain and update.

For more information about how to build or have a prosthetic finger built, visit: http://dangercreations.com/prosthetics

**Docs**: [Parameters](docs/PARAMETERS.md) · [Product requirements and design decisions](docs/PRODUCT.md)

**Web tests**: `make test-web` runs e2e against a fresh server. `make verify-web-ui` starts the server (Docker or local); the server builds SCAD + preview PNGs to `output/` at startup, then captures `output/viewer-screenshot.png`. Use `make build` first for Docker (avoids macOS OpenSCAD issues). For inspect only with an already-running app: `make inspect-ui` (writes `output/ui-inspect.txt`). Requires `pip install -r requirements-dev.txt`, `python -m playwright install chromium`, and OpenSCAD.

**Auto-run on commit** (optional): To run web tests automatically when you commit changes under `web/`, install the hook: `cp scripts/pre-commit-web-test.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`.

**OpenSCAD troubleshooting (macOS Apple Silicon)**:
- *"Incompatible processor... neon crc32"* or *"CGLChoosePixelFormat() failed"* — Run the server via Docker: `make build` then `make verify-web-ui`. The server runs in Docker and builds SCAD+PNGs at startup, avoiding macOS OpenSCAD/Qt issues.

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

