# This file is part of the vis-orbitN distribution (https://github.com/japhir/vis-orbitN).
# Copyright (c) 2023 Ilja J. Kocken
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Visualize orbitN",
    "author": "Ilja Kocken",
    "version": (0, 0, 1),
    "blender": (3, 5, 1),
    "location": "3D Viewport > Sidebar > vis-orbitN",
    "description": "Functions to visualize orbitN output in 3D/4D space.",
    "category": "Development",
}

import bpy

import mathutils
import numpy as np
import math
import pyorb

from math import tau, pi, sin, cos

from bpybb.color import hex_color_to_rgba

#######################################################################
#                       parse the input file!                         #
#######################################################################

def get_files(exp = "modern-highres/",
              infile = "orbitN-coord.inp",
              outext = ".dat",
              basedir = "/home/japhir/SurfDrive/Postdoc1/prj/2023-05-08_orbitN/orbitN-0.4.0/sim/"):
    """
    make path and file names out of directories and experiments
    """
    path = basedir + exp + "/"
    # read in planet masses, relative to the sun's mass
    inputfile = path + infile
    basename = "orbitN-"
    num_files = 10
    outputs = [basename + str(i) + outext for i in range(0, num_files)]
    return(path, inputfile, outputs)

# note that this is getting it from exp above, but it doesn't matter since we
# always use the same inputs
def get_inp(inputfile):
    """
    Parse input file, return body mass, initial position, and initial
    velocities
    """
    # Read in the file
    with open(inputfile) as f:
        lines = (line.strip() for line in f if line.strip())
        # The sun is not listed in the input file, we add it here as element 0
        names = ["Sun"]
        masses = [1]
        # xyz location and velocity
        inits = [[0,0,0], [0,0,0]]
        for line in lines:
            if line.startswith('#'):
                names.append(line.lstrip('# '))
                continue
            if line.endswith('\\'):
                line = line[:-1].strip()
            nums = [float(num) for num in line.split()]
            if len(nums) == 1:
                masses.append(nums[0])
            elif len(nums) == 3:
                inits.append(nums)
    init_pos = inits[::2] # get every other line of length 3 for the position
    init_velocity = inits[::1] # and the rest for the velocity
    return names, masses, init_pos, init_velocity

#######################################################################
# read in the planet's positions and velocities for each timestep t   #
#######################################################################

def get_data(filename):
    """
    Read in the data from the output file
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
        data = [[float(x) for x in line.strip().split()] for line in lines]
    # take a subset for now, first 7 timesteps
    # data = data[:50]
    return(data)

def subset_data(data, tmax = 405, dt = 0.4):
    """
    Subset data to tmax in timesteps of dt (both in kyr).
    No interpolation, just ceil/int casting.
    """
    assert tmax > 0, f"tmax must be greater than 0 or None: {tmax}"
    assert dt >= 0, f"dt must be greater than 0 or None: {dt}"

    if tmax == math.inf and dt == 0:
        print("no subset")
        return(data)
    # in_sstep -73050 steps
    # dt = -2 days
    # thus dt (2*73050)/365.25 = 400 years per row in output
    years_per_row = abs(data[1][0] - data[0][0]) / 365.25
    desired_row = tmax*1e3 / years_per_row
    desired_res = dt*1e3 / years_per_row
    # subset the data to the desired resolution
    data = data[0:math.ceil(desired_row):int(desired_res)]
    return(data)

def get_planet_colors():
    # I got these by using the eydropper tool with a large radius on a picture of the planet
    # for the sun I made it a bit brighter.
    hex_colors = [
        "#fafbfbff",   # Sun (Yellow)
        "#9d999cff",   # Mercury (Gray)
        "#cdcbcaff",   # Venus (Yellowish-white)
        "#788ba1ff",   # Earth (Blue)
        "#ce7657ff",   # Mars (Reddish-brown)
        "#9d9385ff",   # Jupiter (Orange and white)
        "#938463ff",   # Saturn (Pale yellow)
        "#c6d6e0ff",   # Uranus (Pale blue-green)
        "#7a97c1ff",   # Neptune (Deep blue)
        "#c0b5a6ff"    # Pluto (Brown)
    ]
    # convert colours to linear rgb
    # using bpypp function
    # https://www.youtube.com/watch?v=knc1CGBhJeU
    planet_colors = [hex_color_to_rgba(hex_color[1:7]) for hex_color in hex_colors]
    return(planet_colors)

def get_planet_radii():
    radii_km = [696340, 2439.7, 6051.8, 6371.0, 3389.5, 69911.0, 58232.0, 25362.0, 24622.0, 1188.3]
    radii_au = [size / (pyorb.AU / 1e3) for size in radii_km]
    return(radii_au)

#######################################################################
#               calculate/convert orbital parameters                  #
#######################################################################

def neworbit():
    """
    Create orbit with compatible units and anomaly type for default orbitN output
    """
    # set the units to AU and days, standardized to the solar mass
    G_ast = pyorb.get_G(length='AU', mass='Msol', time='d')
    #print(f'Astronomical gravitation constant: {G_ast} AU^3 Msol^-1 d^-2')
    orb = pyorb.Orbit(
        M0=1.0, G=G_ast,
        # leave this empty to create an empty new orbit so we can assign values after
        # let's use the first row of the orbitN output here
        #a = 9.9999642723902427e-01, # semimajor axis
        #e = 1.6702362219232363e-02, # eccentricity
        #i = 1.8056862902287444e-06, # inclination
        #omega = -6.5230367433606062e-01, # argument of perihelion
        #Omega =  2.4485604537785668e+00, # longitude of the ascending node
        # anom =  ,  # it defaults to true anomaly, which we don't have as output
        degrees = False,
    )
    #orb.mean_anomaly = -4.2844275785890285e-02 # this now sets anom directly
    orb.type = 'mean' # this switches from true anomaly to mean anomaly
    #orb.calculate_cartesian()
    # I've verified that orb.x orb.y orb.z and orb.vx orb.vy and orb.vz are identical to orbitN-3.dat's first row!
    #print(orb)
    #print(f'Orbital period: {orb.period} years')
    #print(f'Orbital speed: {orb.velocity} AU/d')
    return orb

def assign_orbit_data(data):
    """
    Create orbit object that holds orbits for each row of orbitN output
    """
    orb = neworbit() # this has some defaults for the correct reference frame
    orb.allocate(len(data))
    # assign the variables
    orb.a=[col[1] for col in data]      # semimajor axis
    orb.e=[col[2] for col in data]      # eccentricity
    orb.i=[col[3] for col in data]      # inclination # not that this goes from 0 to 2 pi
    orb.omega=[col[4] for col in data]  # ArgPerihelion
    orb.Omega=[col[5] for col in data]  # LongAscNode
    # note that we don't use this!
    #vpi = [col[6] for col in data]     # LongPerihelion
    orb.anom=[col[7] for col in data]   # mean anomaly
    # trigger update manually
    orb.calculate_cartesian()
    return(orb)

def orbit_points(orb, N = int(360/5)):
    """
    For one orbit, sample the ellipse using N points
    """
    # add N new orbits where we only change the anomaly so we can plot it
    orb.add(N - 1)
    # copy the first row over to the remainder
    orb.kepler = orb[0].kepler[:,0][:,None]
    orb.anom = np.linspace(0, math.tau, N)
    orb.calculate_cartesian()
    return(orb)

#######################################################################
#               now do things in blender using the orbit data         #
#######################################################################

def make_collection(exp):
    """
    Make a collection (folder thing on the right) for the experimental folder
    """
    collection = bpy.data.collections.new(exp)
    # Link the collection to the scene
    scene = bpy.context.scene
    scene.collection.children.link(collection)
    return(collection)

def make_mesh(data, meshname, objname, color, material, collection, make_edges = False):
    """
    Draw orbitN data as a mesh with vertices
    """
    # draw the orbits as vertices
    mesh = bpy.data.meshes.new(meshname)
    obj = bpy.data.objects.new(objname, mesh)
    # assign the object colour
    obj.color = color
    # and set the material to our shader material
    obj.active_material = material
    # set initial location
    obj.location = (0, 0, 0)
    # add to the current collection
    collection.objects.link(obj)
    # add the vertices
    mesh.vertices.add(len(data))
    bpy.ops.object.shade_smooth()
    # add the edges (only for modern high-res!!!
    if make_edges:
        mesh.edges.add(len(data) - 1)
    # add attributes with age and speed, we can potentially use these with
    # geometry nodes
    age = mesh.attributes.new(name = "age", type = "FLOAT", domain="POINT")
    speed_u = mesh.attributes.new(name = "speed_u", type = "FLOAT", domain = "POINT")
    speed_v = mesh.attributes.new(name = "speed_v", type = "FLOAT", domain = "POINT")
    speed_w = mesh.attributes.new(name = "speed_w", type = "FLOAT", domain = "POINT")
    # assign each vertex coordinate
    for i, point in enumerate(data):
        # set the positions of the verts
        mesh.vertices[i].co = point[1:4]
        # set the vertex attributes
        mesh.attributes['age'].data[i].value = point[0]
        mesh.attributes['speed_u'].data[i].value = point[4]
        mesh.attributes['speed_v'].data[i].value = point[5]
        mesh.attributes['speed_w'].data[i].value = point[6]
        if make_edges and i > 0:
            mesh.edges[i-1].vertices = [i-1, i]
    return(obj, mesh)


def make_gpencil(data, gpname, objname, collection, matname, type = "orbit", cyclic = True):
    """
    Draw data as a grease pencil object
    """
    # Create a new Grease Pencil object
    gpencil_data = bpy.data.grease_pencils.new(gpname)
    gpencil_object = bpy.data.objects.new(objname, gpencil_data)
    gpencil_data.stroke_thickness_space = 'WORLDSPACE'
    # Link the Grease Pencil object to the scene
    collection.objects.link(gpencil_object)
    # Create a new Grease Pencil layer
    gp_layer = gpencil_data.layers.new("orbit Layer")
    gp_layer.use_lights = False
    # Create a new frame for drawing
    gp_frame = gp_layer.frames.new(0, active = True)
    # Create a new stroke with the points
    gp_stroke = gp_frame.strokes.new()
    # Set the stroke properties
    gp_stroke.line_width = 18
    gp_stroke.start_cap_mode = 'FLAT'
    gp_stroke.end_cap_mode = 'FLAT'
    gp_stroke.use_cyclic = cyclic
    gp_stroke.points.add(len(data))
    for i, point in enumerate(data):
        if type == "orbit":
            gp_stroke.points[i].co = data[i].cartesian[0:3]
        elif type == "eccentricity":
            # one blender unit is 1 kyr, and eccentricity is multiplied by 10
            gp_stroke.points[i].co = [i*0.001, 0.0, data.e[i]*10]
        elif type == "mesh":
            gp_stroke.points[i].co = point[1:4]
    # find existing material in scene
    mat = bpy.data.materials[matname]
    gpencil_object.data.materials.append(mat)
    return(gpencil_object, gpencil_data, gp_layer, gp_frame, gp_stroke)

def make_planet(position, radius, emptyname, spherename, material, color, collection):
    """
    Draw a sphere with the desired radius. Also create an empty and potentially animate it
    """
    # create an empty to track the planet's position
    empty = bpy.data.objects.new(emptyname, None)
    empty.location = position
    # bpy.context.scene.collection.objects.link(empty)
    collection.objects.link(empty)
    empty.hide_viewport = True
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius)
    sphere = bpy.context.object
    # set initial location
    sphere.location = (0, 0, 0)
    # collection.objects.link(sphere) # this doesn't work somehow...
    sphere.name = spherename
    sphere.parent = empty
    sphere.color = color
    # find the existing material
    sphere.active_material = material
    bpy.ops.object.shade_smooth()
    return empty

def animate_planet(data, empty):
    """
    Add keyframes to the sphere's location for each frame in the animation
    """
    for i in range(len(data)):
        frame = i + 1
        time = data[i][0]
        loc = mathutils.Vector(data[i][1:4])
        empty.location = loc
        empty.keyframe_insert(data_path="location", frame=frame)
    # Set the end frame of the animation
    bpy.context.scene.frame_end = len(data)

def make_meshes(exp, tmax, dt, outext = ".dat", make_planets = False, animate_planets = False):
    """
    Takes an experiment folder in your default directory and draws
    a mesh with vertices for xyz locations and a planet at 1000x, potentially animating
    along the track.
    """
    collection = make_collection(exp)
    path, inputfile, outputs = get_files(exp, outext = outext)
    names, masses, init_pos, init_velocity = get_inp(inputfile)
    # planet radii in AU
    radii_au = get_planet_radii()
    symbols = ['☉', '☿', '♀', '⊕', '♂', '♃', '♄', '♅', '♆', '♇']
    # planet size multiplier
    mult = 1e3
    # I've created a single material, for which the simple shader just passes
    # the object color to its diffuse color
    planet_mat = bpy.data.materials['Material']
    planet_colors = get_planet_colors()

    for j in range(0, 10):
        filename = path + outputs[j]
        data = get_data(filename)
        data = subset_data(data, tmax = tmax, dt = dt)
        # no need to subset modern
        make_mesh(data, meshname = names[j], objname = str(j) + "_orbit_" + names[j], color = planet_colors[j],
                  material = planet_mat, collection = collection, make_edges = False)
        if make_planets:
            # NOTE: planet bodies are not created within the collection somehow
            plan = make_planet(position = data[0][1:4], # initial position
                        radius = mult * radii_au[j],
                        emptyname = str(j) + "_body_position_" + names[j],
                        spherename = str(j) + "_body_sphere_" + names[j],
                        material = planet_mat,
                        color = planet_colors[j],
                        collection = collection)
            if (animate_planets):
                animate_planet(data, empty = plan)

def make_orbit_gpencil(data, gpname, objname, matname, collection, N = int(360/5)):
    """
    Make a gpencil object with an ellipse, update every frame for each row in data
    """
    orb = assign_orbit_data(data)
    # make a gpencil and return the layer, frame, stroke
    gpo, gpd, gp_layer, gp_frame, gp_stroke = make_gpencil(
        data = orbit_points(orb[0], N = N),
        gpname = gpname,
        objname = objname,
        matname = matname,
        collection = collection,
        type = "orbit")
    # animate the orbits for the remaining frames
    animate_orbit(data, orb, gp_layer, gp_frame, gp_stroke)

def animate_orbit(data, orb, gp_layer, gp_frame, gp_stroke, N = int(360/5)):
    """
    Assuming that frame 0 has the initial object, update it for the subsequent frames
    """
    # animate it so we get some example orbits without duplicating the grease pencil object too much
    for f, dat in enumerate(data):
        if f == 0: # the first frame already exists
            continue
        # calculate the xyz coords that trace the full orbit from kepler
        # add N new orbits where we only change the anomaly so we can plot it
        orbsmp_loop = orbit_points(orb[f], N = N)
        # Create a new frame and clear it
        gp_frame = gp_layer.frames.new(f, active = True)
        gp_frame.clear()
        # Create a new stroke with the points
        gp_stroke = gp_frame.strokes.new()
        # Set the stroke properties
        gp_stroke.line_width = 18
        gp_stroke.use_cyclic = True
        # set the point positions to the new cartesian coordinates
        gp_stroke.points.add(count=N)
        for i, value in enumerate(orbsmp_loop):
            gp_stroke.points[i].co = orbsmp_loop.cartesian[:,i][0:3]# assign xyz coords of orb to these and we're set!

def make_animated_orbits(exp, tmax = 5, dt = .4, outext = ".elm.dat"):
    """
    Takes an experiment folder in your default directory and
    draws an ellipse in 3d space that animates over time
    """
    collection = make_collection(exp)
    path, inputfile, outputs = get_files(exp, outext = outext)
    names, masses, init_pos, init_velocity = get_inp(inputfile)
    for j in range(1, 10):
        filename = path + outputs[j]
        data = get_data(filename)
        data = subset_data(data, tmax, dt)
        # create a gpencil that animates over frames
        make_orbit_gpencil(data,
            gpname = str(j) + "_gpencil_" + names[j],
            objname = str(j) + "_orbit_" + names[j],
            matname = str(j) + "_material_" + names[j] + "_MANUAL",
            collection = collection)
        # Set the end frame of the animation
        bpy.context.scene.frame_end = len(data)

def make_eccentricity_curve(exp, tmax = 405, dt = 0.8, outext = ".elm.dat"):
    """
    Draw the Earth's eccentricity as a function of time
    """
    collection = make_collection(exp)
    path, inputfile, outputs = get_files(exp, outext = outext)
    names, masses, init_pos, init_velocity = get_inp(inputfile)
    j = 3 # just for the Earth
    filename = path + outputs[j]
    data = get_data(filename)
    data = subset_data(data, tmax = tmax, dt = dt)
    orb = assign_orbit_data(data)
    make_gpencil(orb,
                 gpname = str(j) + "_gpencil_" + names[j],
                 objname = str(j) + "_orbit_" + names[j],
                 matname = str(j) + "_material_" + names[j] + "_MANUAL",
                 collection = collection, type = "eccentricity", cyclic = False)
    ecc = make_planet(position = [0*0.001, 0.0, orb.e[0]*10],
                radius = 1e3 * get_planet_radii()[j],
                emptyname = str(j) + "_eccentricity_" + names[j],
                spherename = str(j) + "_ecc_body_" + names[j],
                material = bpy.data.materials['Material'],
                color = get_planet_colors()[j],
                collection = collection)
    planet_pos = []
    for i, o in enumerate(orb.e):
        planet_pos.append([0.0, i * 0.001, 0.0, orb.e[i]*10])
    animate_planet(planet_pos, ecc)


#######################################################################
#                           draw modern runs                          #
#######################################################################

# modern orbits, 247 years in timesteps of 5 days
#make_meshes(exp = "modern-highres", make_planets = True, animate_planets = True)

#######################################################################
#                now draw keplerian element output!                   #
#######################################################################

#make_meshes(exp = "solsys-keplerian", tmax = 405, dt = 1,
#            outext = ".dat", make_planets = False, animate_planets = False)

#make_meshes(exp = "solsys-keplerian", tmax = 60e3, dt = .4,
#            outext = ".dat", make_planets = False, animate_planets = False)

#make_meshes(exp = "solsys-keplerian", tmax = 2.4e3, dt = .4,
#            outext = ".dat", make_planets = False, animate_planets = False)

# draw animating grease pencil orbits using the orbital elements
# just for t = 0
#make_animated_orbits(exp = "solsys-keplerian", tmax = .4, dt = 0.4, outext = ".elm.dat")
#make_animated_orbits(exp = "solsys-keplerian", tmax = 405, dt = 0.8, outext = ".elm.dat")
#make_animated_orbits(exp = "solsys-keplerian", tmax = 2.4e3, dt = 0.8, outext = ".elm.dat")

# draw an eccentricity curve vs time (1 frame * 0.001 on x, 0 on y, eccentricity * 10 on z
#make_eccentricity_curve(exp = "solsys-keplerian", tmax = 405, dt = .8, outext = ".elm.dat")
#make_eccentricity_curve(exp = "solsys-keplerian", tmax = 2.4e3, dt = .8, outext = ".elm.dat")



### create a text object that says the current timestep
### NOTE: I did this using geometry nodes in stead, based on the timestep in the output of 400 days per step
### simple conversion: 1 frame = 400 days, current frame / 400 * 365.25 * 1e-3 to get kyr
##bpy.ops.object.text_add()
##txt=bpy.context.active_object
### add to the current collection
##collection.objects.link(txt)
## animate the text value with the age

##for i, dat in enumerate(data):
##    frame = i + 1
##    time = -data[i][0]/365.25*1e-3
##    txt.keyframe_insert(data_path="body", frame = frame)
##    txt.data.body=str(round(time)) + " thousand years ago"


# SOMEDAY/MAYBE: conver this into a blender addon
# see e.g. https://www.youtube.com/watch?v=0_QskeU8CPo
# would need to define a new class for each major function that I'd like to call

# #######################################################################
# #                       add a menu in blender                         #
# #######################################################################

# class VIEW3D_PT_orbitN_panel(bpy.types.Panel):  # class naming convention ‘CATEGORY_PT_name’

#     # where to add the panel in the UI
#     bl_space_type = "VIEW_3D"  # 3D Viewport area (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items)
#     bl_region_type = "UI"  # Sidebar region (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items)

#     bl_category = "orbitN"  # found in the Sidebar
#     bl_label = "visualize orbitN"  # found at the top of the Panel

#     def draw(self, context):
#         """define the layout of the panel"""
#         row = self.layout.row()
#         row.operator("make_meshes(exp = 'modern-highres', make_planets = True, animate_planets = True)",
#                      text="Make modern run meshes <animating planet position is SLOW>!")
#         row = self.layout.row()
#         row.operator("make_meshes(exp = 'solsys-keplerian', tmax = 405, dt = 1, outext = '.dat', make_planets = False, animate_planets = False)",
#                      text="Make solsys-keplerian 405 kyr meshes")
#         row = self.layout.row()
#         row.operator("make_meshes(exp = 'solsys-keplerian', tmax = 2.4e3, dt = .4, outext = '.dat', make_planets = False, animate_planets = False)",
#                      text="Make solsys-keplerian 2.4 Myr meshes")
#         row = self.layout.row()
#         row.operator("make_meshes(exp = 'solsys-keplerian', tmax = 60e3, dt = .4, outext = '.dat', make_planets = False, animate_planets = False)",
#                      text="Make solsys-keplerian 60 Myr meshes <SLOWish>!")
#         row = self.layout.row()
#         row.operator("make_animated_orbits(exp = 'solsys-keplerian', tmax = .4, dt = 0.4, outext = '.elm.dat')",
#                      text = "Make animated orbits for solsys-keplerian at t = 0")
#         row = self.layout.row()
#         row.operator("make_animated_orbits(exp = 'solsys-keplerian', tmax = 405, dt = 0.8, outext = '.elm.dat')",
#                      text = "Make animated orbits for solsys-keplerian for 405 kyr <SLOWish>!")
#         row = self.layout.row()
#         row.operator("make_animated_orbits(exp = 'solsys-keplerian', tmax = 2.4e3, dt = 0.8, outext = '.elm.dat')",
#                      text = "Make animated orbits for solsys-keplerian for 2.3 Myr <SLOW>!")
#         row = self.layout.row()
#         row.operator("make_eccentricity_curve(exp = 'solsys-keplerian', tmax = 405, dt = .8, outext = '.elm.dat')",
#                      text = "Make eccentricity curve for solsys-keplerian for 405 kyr")
#         row = self.layout.row()
#         row.operator("make_eccentricity_curve(exp = 'solsys-keplerian', tmax = 2.4e3, dt = .8, outext = '.elm.dat')",
#                      text = "Make eccentricity curve for solsys-keplerian for 2.4 Myr")

# def register():
#     bpy.utils.register_class(VIEW3D_PT_orbitN_panel)

# def unregister():
#     bpy.utils.unregister_class(VIEW3D_PT_orbitN_panel)

# if __name__ == "__main__":
#     register()
