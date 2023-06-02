# visualise orbitN output in Blender

orbitN is a symplectic integrator for near-Keplerian planetary systems. This
allows us to calculate how the solar system may have evolved over geological
time scales, and to interrogate Earth's eccentricity in the geologic past. See
Zeebe 2023 for the paper that describes the model. orbitN will be available for
free on https://github.com/rezeebe/orbitN under the GPL-3 license.

[Blender](https://www.blender.org/) is a free (libre) 3D software that's used
in movies and games. Here we use Blender's python API to visualise orbitN
output in 3D.

![modern-orbits](https://github.com/japhir/visualise-orbitN/assets/10659193/4301580b-fdf9-429a-8c6e-dac14a3ddd7d)

# Example movies

I've made some example movies! To download them, click on the link and go to
the top right > Download raw file.

[movie of animated modern orbits](movies/modern_orbits_highres.mp4)
This is a video of a simulation into the future, with a timestep of 5 days.
Because the video plays at 24 frames per second, this means that every second,
120 days pass.

[movie of animated orbits for the past 405 kyr](movies/animated_orbits_405kyr_g5.mp4)
This video shows how the orbits dance around over the past 405 thousand years (kyr) from an angle. It also shows what Earth's eccentricity looked like at the time.

[movie of animated orbits for the past 405 kyr from the top](movies/animated_orbits_405kyr_ortho_top.mp4)
The same as the above, but now viewed from the top without any perspective corrections (a so-called orthographic view).

Feel free to use these movies for education or other purposes. They are licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/) (whereas the python code is released under GPL-3.0 or later).

[![License: CC BY-SA 4.0](https://licensebuttons.net/l/by-sa/4.0/80x15.png)](https://creativecommons.org/licenses/by-sa/4.0/)

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

1. Download `visualise_orbitN.py` by opening it on GitHub, then clicking the
   Download Raw File button in the top-right (or git clone this repository).
2. Download `visualise_orbitN.blend` file for the example output that I created.
3. Open `visualise_orbitN.blend` in Blender.
4. In Blender, click the top panel's "Scripting" to change the layout. Go to
   Text > Open > select the newly downloaded file.
5. Change the directory in the function definition of `get_files` so it points
   to your orbitN sim directory. Navigate to the bottom of the file, where we
   invoke the functions.
6. Uncomment the desired function call and hit the Run Script button (play
   arrow at the top).

## Example blend file

This file has some collections with example visualisations:

### modern-highres
I ran orbitN with the 8 planets and pluto for 246.6 years into the future
(close to the orbital period of Pluto) with a timestep of 5 days, just to take
the model for a spin.

NOTE: I had to eliminate the animation for this from the blend file to reduce
its size, so the planets stop moving after 10 frames.

### solsys-keplerian
I ran orbitN with the 8 planets and pluto for 60 million years into the past
with a timestep of 400 years. (This took about 5:28 hours on my laptop!).

NOTE: I had to delete the 2.4 Myr and 60 Myr pointclouds from the blend file to
make the filesize manageable.

### collection naming
- **modern** high resolution model run with moving planets!
- **meshes** all cartesian coordinates in data as vertices (points).
- **orbits** animated orbits as grease pencil objects.
- **eccentricity** simple line tracing out Earth's eccentricity, with a planet
  moving along at the same pace as the orbits.

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

# Getting the Night Sky in the background

This [repository](https://github.com/alcove-design/blender-world-night-sky) has
instructions on how to download the night's sky from NASA and use it as a world
texture HDRI. On the [NASA website](https://svs.gsfc.nasa.gov/3895) it says
that the first map is in "celestial (J2000 geocentric right ascension and
declination)" coordinates, which means that they actually align with our
orbits/planets, which are in an inertial reference frame.

# References

Zeebe (2023) Astronomical Journal. orbitN: A symplectic integrator for planetary
systems dominated by a central mass -- Insight into long-term solar system
chaos
