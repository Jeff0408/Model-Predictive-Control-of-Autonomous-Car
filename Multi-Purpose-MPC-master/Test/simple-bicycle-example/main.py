from reference_path import ReferencePath
from map import Map, Obstacle
from model import simple_bycicle_model
from MPC import MPC
import pdb
import sys
import time
import do_mpc
import numpy as np
import matplotlib.pyplot as plt
from casadi import *
from casadi.tools import *
sys.path.append('../../')


""" User settings: """
show_animation = True
store_results = False

# Load map file
map = Map(file_path='maps/sim_map.png', origin=[-1, -2],
          resolution=0.005)

# Specify waypoints
wp_x = [-0.75, -0.25, -0.25, 0.25, 0.25, 1.25, 1.25, 0.75, 0.75, 1.25,
        1.25, -0.75, -0.75, -0.25]
wp_y = [-1.5, -1.5, -0.5, -0.5, -1.5, -1.5, -1, -1, -0.5, -0.5, 0, 0,
        -1.5, -1.5]

# Specify path resolution
path_resolution = 0.05  # m / wp

# Create smoothed reference path
reference_path = ReferencePath(map, wp_x, wp_y, path_resolution,
                               smoothing_distance=5, max_width=0.23,
                               circular=True)

# Add obstacles
use_obstacles = True
if use_obstacles:
    obs1 = Obstacle(cx=0.0, cy=0.0, radius=0.05)
    obs2 = Obstacle(cx=-0.8, cy=-0.5, radius=0.08)
    obs3 = Obstacle(cx=-0.7, cy=-1.5, radius=0.05)
    obs4 = Obstacle(cx=-0.3, cy=-1.0, radius=0.08)
    obs5 = Obstacle(cx=0.27, cy=-1.0, radius=0.05)
    obs6 = Obstacle(cx=0.78, cy=-1.47, radius=0.05)
    obs7 = Obstacle(cx=0.73, cy=-0.9, radius=0.07)
    obs8 = Obstacle(cx=1.2, cy=0.0, radius=0.08)
    obs9 = Obstacle(cx=0.67, cy=-0.05, radius=0.06)
    map.add_obstacles([obs1, obs2, obs3, obs4, obs5, obs6, obs7,
                       obs8, obs9])


"""
Get configured do-mpc modules:
"""
# model setup
vehicle = simple_bycicle_model(length=0.12, width=0.06,
                               reference_path=reference_path, Ts=0.05)
vehicle.model_setup()
model = vehicle.model

controller = MPC(vehicle)
mpc = controller.mpc

# Compute speed profile
ay_max = 4.0  # m/s^2
a_min = -0.1  # m/s^2
a_max = 0.5  # m/s^2
SpeedProfileConstraints = {'a_min': a_min, 'a_max': a_max,
                           'v_min': 0.0, 'v_max': 1.0, 'ay_max': ay_max}
vehicle.reference_path.compute_speed_profile(SpeedProfileConstraints)

"""
Set initial state
"""
x0 = np.array([wp_x[0], wp_y[1], 0, 0, 0, 0])
mpc.x0 = x0

# Use initial state to set the initial guess.
mpc.set_initial_guess()


"""
Run MPC main loop:
"""

##############
# Simulation #
##############

# Set simulation time to zero
t = 0.0

# Logging containers
x_log = [wp_x[0]]
y_log = [wp_y[0]]
v_log = [0.0]

# Until arrival at end of path
#vehicle.s < reference_path.length
while 1:

    # Get control signals
    u = controller.get_control(x0)

    # Simulate car
    vehicle.drive()

    print(mpc.data['_x'])
    states = mpc.data['_x'][0]
    x, y, psi, vel = states[0], states[1], states[2], states[3]

    # Log car state
    x_log.append(x)
    y_log.append(y)
    v_log.append(vel)

    # Increment simulation time
    t += vehicle.Ts

    # Plot path and drivable area
    reference_path.show()

    # Plot car
    controller.show()

    # Plot MPC prediction
    controller.show_prediction()

    # Set figure title
#     plt.title('MPC Simulation: acc(t): {:.2f}, delta(t): {:.2f}, Duration: '
#               '{:.2f} s'.format(u[0], u[1], t))
    plt.axis('off')
    plt.pause(0.001)

input('Press any key to exit.')
