from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # -----------------------------
    # Paths
    # -----------------------------
    robo_pkg = get_package_share_directory('robo')

    world_path = '/home/varun/proj/src/robo/worlds/obstacle.world'

    slam_params = os.path.join(
        robo_pkg,
        'config',
        'mapper_params_online_async.yaml'
    )

    # -----------------------------
    # 1. Robot state publisher
    # ros2 launch robo rsp.launch.py use_sim_time:=true
    # -----------------------------
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robo_pkg, 'launch', 'rsp.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'true'
        }.items()
    )

    # -----------------------------
    # 2. Gazebo
    # ros2 launch gazebo_ros gazebo.launch.py world:=...
    # -----------------------------
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            )
        ),
        launch_arguments={
            'world': world_path
        }.items()
    )

    # -----------------------------
    # 3. Spawn robot
    # ros2 run gazebo_ros spawn_entity.py -topic robot_description -entity robot
    # -----------------------------
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'robot'
        ],
        output='screen'
    )

    # -----------------------------
    # 4. SLAM toolbox
    # ros2 launch slam_toolbox online_async_launch.py ...
    # -----------------------------
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('slam_toolbox'),
                'launch',
                'online_async_launch.py'
            )
        ),
        launch_arguments={
            'params_file': slam_params,
            'use_sim_time': 'true'
        }.items()
    )

    # -----------------------------
    # 5. RViz2
    # rviz2
    # -----------------------------
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen'
    )

    # -----------------------------
    # 6. Teleop keyboard
    # ros2 run teleop_twist_keyboard teleop_twist_keyboard
    # -----------------------------
    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        prefix='xterm -e',
        output='screen'
    )

    return LaunchDescription([
        rsp,
        gazebo,
        spawn_robot,
        slam,
        rviz,
        teleop
    ])
