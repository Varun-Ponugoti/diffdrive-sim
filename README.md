# Differential-Drive Robot with Gazebo Simulation & SLAM

A ROS 2 package for a simple four-wheeled differential-drive robot equipped with a lidar and an RGB camera. The robot is simulated in Gazebo Classic inside an obstacle world, and uses [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) to build a map of the environment and localize within it.

<!-- Add a screenshot or GIF of the robot in Gazebo / RViz here -->
<!-- ![demo](docs/demo.gif) -->

## Features

- Robot model written in modular **xacro** (chassis, wheels, caster, lidar, camera)
- **Gazebo Classic** simulation with differential-drive, lidar, and camera plugins
- **SLAM** with slam_toolbox in mapping or localization mode
- A pre-built map of the obstacle world (`obstacleworld.*`) ready for localization
- A single launch file that brings up the whole stack: robot state publisher, Gazebo, robot spawn, SLAM, RViz, and keyboard teleop

## Repository Structure

```
.
├── obstacleworld.data          # Serialized slam_toolbox map (localization)
├── obstacleworld.posegraph     # Serialized slam_toolbox pose graph
├── obstacleworld.pgm           # Occupancy grid image of the map
├── obstacleworld.yaml          # Map metadata (resolution, origin, thresholds)
├── README.md
└── src
    └── robo
        ├── CMakeLists.txt
        ├── package.xml
        ├── config
        │   ├── mapper_params_online_async.yaml   # slam_toolbox parameters
        │   ├── robo_sim.rviz                     # RViz config for simulation
        │   └── robot.rviz                        # RViz config for the robot model
        ├── description
        │   ├── robot.urdf.xacro      # Top-level robot description
        │   ├── robot_core.xacro      # Chassis, wheels, caster
        │   ├── inertial_macros.xacro # Inertia helper macros
        │   ├── gazebo_control.xacro  # Diff-drive plugin
        │   ├── lidar.xacro           # Lidar link + ray sensor plugin
        │   └── camera.xacro          # Camera link + camera plugin
        ├── launch
        │   ├── launch.py             # Full-stack launch
        │   └── rsp.launch.py         # Robot state publisher only
        └── worlds
            ├── obstacle.world        # Gazebo world with obstacles
            └── obstacles
```

## Robot Specifications

| Component | Details |
|---|---|
| Chassis | 0.30 × 0.30 × 0.15 m box, 0.5 kg |
| Drive wheels | 2 × cylinder, radius 0.05 m, width 0.04 m |
| Wheel separation | 0.35 m |
| Caster | Low-friction sphere, radius 0.05 m |
| Lidar | 360 samples over 360°, 10 Hz, range 0.3–12 m |
| Camera | 640 × 480 RGB, 10 Hz, ~62° horizontal FOV |

## Prerequisites

- Ubuntu 22.04 with **ROS 2 Humble** (other distros with Gazebo Classic should work with minor changes)
- Gazebo Classic (Gazebo 11)

Install the required ROS packages:

```bash
sudo apt install \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher \
  ros-humble-slam-toolbox \
  ros-humble-rviz2 \
  ros-humble-teleop-twist-keyboard \
  xterm
```

`xterm` is needed because the full-stack launch file opens teleop in its own terminal window.

## Installation

```bash
git clone https://github.com/Varun-Ponugoti/diffdrive-sim.git .
cd ~/diffdrive-sim
colcon build --symlink-install
source install/setup.bash
```

If you clone into a different location, update the hardcoded paths described in [Configuration](#configuration).

## Usage

### Option 1: Launch everything at once

```bash
ros2 launch robo launch.py
```

This starts the robot state publisher, Gazebo with the obstacle world, spawns the robot, runs slam_toolbox, opens RViz, and opens a teleop window. Click into the xterm window and use the keyboard to drive (`i` forward, `,` back, `j`/`l` turn, `k` stop).

### Option 2: Launch step by step

Run each command in its own terminal, sourcing the workspace in each one first (`source install/setup.bash`).

**1. Robot state publisher**
```bash
ros2 launch robo rsp.launch.py use_sim_time:=true
```

**2. Gazebo with the obstacle world**
```bash
ros2 launch gazebo_ros gazebo.launch.py world:=$(ros2 pkg prefix robo)/share/robo/worlds/obstacle.world
```

**3. Spawn the robot**
```bash
ros2 run gazebo_ros spawn_entity.py -topic robot_description -entity robot
```

**4. slam_toolbox**
```bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=./src/robo/config/mapper_params_online_async.yaml \
  use_sim_time:=true
```
On ROS 2 Foxy, the argument is named `params_file` instead of `slam_params_file`.

**5. Teleop**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**6. RViz**
```bash
rviz2 -d src/robo/config/robo_sim.rviz
```

### Setting up RViz manually

If you start RViz without a config file:

1. Set **Fixed Frame** to `map` (or `odom` if SLAM is not running).
2. Add **RobotModel** and set its description topic to `/robot_description`.
3. Add **LaserScan** and set its topic to `/scan`.
4. Add **Map** and set its topic to `/map`.
5. (Optional) Add **Camera** or **Image** and select the camera's `image_raw` topic (run `ros2 topic list` to find the exact name).

## Mapping vs. Localization

The SLAM mode is set in `config/mapper_params_online_async.yaml`:

```yaml
mode: localization   # or: mapping
map_file_name: /home/varun/proj/obstacleworld
map_start_at_dock: true
```

**To build a new map:** set `mode: mapping` and comment out `map_file_name`. Drive the robot around the world until the map is complete, then save it:

```bash
# Occupancy grid (.pgm + .yaml), e.g. for Nav2
ros2 run nav2_map_server map_saver_cli -f obstacleworld

# Serialized pose graph (.posegraph + .data) for slam_toolbox localization
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: 'obstacleworld'}"
```

You can also save both from the **SlamToolboxPlugin** panel in RViz.

**To localize in an existing map:** set `mode: localization` and point `map_file_name` to the map's path without the file extension. The included `obstacleworld.posegraph` / `.data` files are a ready-made map of `obstacle.world`.

## Topics and Frames

| Topic | Type | Description |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | Velocity commands to the diff-drive plugin |
| `/odom` | `nav_msgs/Odometry` | Wheel odometry from Gazebo |
| `/scan` | `sensor_msgs/LaserScan` | Lidar scans |
| `/map` | `nav_msgs/OccupancyGrid` | Map from slam_toolbox |
| `/robot_description` | `std_msgs/String` | URDF from robot_state_publisher |
| camera `image_raw` | `sensor_msgs/Image` | Camera images |

TF tree:

```
map → odom → base_link ─┬─ base_footprint
                        ├─ chassis ─┬─ laser_frame
                        │           ├─ camera_sensor → camera_light
                        │           └─ caster_wheel
                        ├─ left_wheel
                        └─ right_wheel
```

## Configuration

A few absolute paths are currently hardcoded. Update them for your machine:

| File | Setting |
|---|---|
| `src/robo/launch/launch.py` | `world_path` |
| `src/robo/config/mapper_params_online_async.yaml` | `map_file_name` |

After changing anything in `config/`, `launch/`, `description/`, or `worlds/`, rebuild with `colcon build --symlink-install`. Symlink installs only pick up edits to existing files, not newly added ones.

## Troubleshooting

- **The robot doesn't appear in Gazebo.** Make sure the robot state publisher is running before you spawn the robot, since `spawn_entity.py` reads from `/robot_description`.
- **The map doesn't show up in RViz.** Check that `use_sim_time` is `true` for every node, and that the Fixed Frame is set to `map`.
- **SLAM ignores the config file.** Confirm you're using the right argument name for your ROS distro (`slam_params_file` on Humble, `params_file` on Foxy).
- **The teleop window doesn't open.** Install xterm: `sudo apt install xterm`.

