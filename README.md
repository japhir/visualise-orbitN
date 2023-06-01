# visualize orbitN output in Blender

orbitN is a symplectic integrator for near-Keplerian planetary systems. This
allows us to calculate how the solar system may have evolved over geological
time scales, and to interrogate Earth's eccentricity in the geologic past. See
Zeebe 2023 for the paper that describes the model. orbitN will be available for
free on https://github.com/rezeebe/orbitN under the GPL-3 license.

[Blender](https://www.blender.org/) is a free (libre) 3D software that's used
in movies and games. Here we use Blender's python API to visualize orbitN
output in 3D.

<!-- TODO: insert gif of orbital elements here -->

# Installation

- install orbitN <!-- link to Richard's video/website -->
- run some example experiments in the subdirectory sim
- convert cartesian output to keplerian elements using `xv2elm`
- install Blender (I'm using 3.5.1)
- install python dependencies:
 - numpy
 - mathutils
 - math
 - pyorb to convert between cartesian and keplerian elements
   https://danielk.developer.irf.se/pyorb/index.html
 - bpybb to convert between hexadecimal colours and blender's linear RGB
   https://github.com/CGArtPython/bpy_building_blocks (or copy the colour
   conversion over)

# Getting Started

Download `vizualize_orbitN.py` by opening it on GitHub, then clicking the
Download Raw File button in the top-right (or git clone this repository).

In Blender, click the top panel's "Scripting" to change the layout.
Go to Text > Open > select the newly downloaded file.

Change the directory in the function definition of `get_files` so it points to
your orbitN sim directory. Navigate to the bottom of the file, where we invoke
the functions.

Uncomment the desired function call and hit the Run Script button (play arrow
at the top).

# Available functions

At the bottom of the script, the following function invocations are available:

- `make_meshes` draws vertices (points) for each of the rows in the data. It
  also gives the points vertex attributes so that one can use e.g. geometry
  nodes to tweak the mesh and have access to the age as well as the velocity
  vector.
  - setting `make_planets` to `True` draws spheres for the 8 planets and Pluto, with the
    planet's sizes * 1000.
  - `animate_planets` lets the planets move with time. This is slow and only
    useful for high-resolution modern simulations (otherwise it will jump
    around too much.)
  - `exp` simulation subdirectory where the orbitN model output
    can be found.
  - `tmax` the maximum age in kyr to subset the data to, rounded up to the
    nearest one in the data.
  - `dt` is the timestep in kyr, rounded down to the nearest value in the data.
  - `outext` is the file extension of the orbitN output files. This is `.dat`
    for cartesian coordinates and `.elm.dat` for the converted keplerian
    elements.
- `make_animated_orbits` draws an orbit ellipse for each row in the data for a
  new frame using the grease pencil. This is relatively fast, but don't run it
  for much more than 3 Myr.
- `make_eccentricity_curve` draws a simple eccentricity curve for the Earth
  based on the data. Includes a planet that moves along the curve with time.

```python
make_meshes(exp = "modern-highres", make_planets = True, animate_planets = True)
# drawing the points is pretty fast
# animating the planets is slow

make_meshes(exp = "solsys-keplerian", tmax = 405, dt = 1, outext = ".dat", make_planets = False, animate_planets = False)
# this is pretty fast, but for the full 60 Myr output that includes values
# every 400 years it takes about a minute to load in and is fast after.

make_animated_orbits(exp = "solsys-keplerian", tmax = 405, dt = 0.8, outext = ".elm.dat")
# this pretty fast unless you set tmax to much more than, e.g., 3 Myr

make_eccentricity_curve(exp = "solsys-keplerian", tmax = 405, dt = .8, outext = ".elm.dat", make_planet = True)
# this is pretty fast
```

# References

Zeebe (2023) Astronomical Journal. orbitN: A symplectic integrator for planetary
systems dominated by a central mass -- Insight into long-term solar system
chaos
