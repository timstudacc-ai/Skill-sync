---
name: ros-forum-post-drafter
description: Drafts high-quality support posts for ROS/NAV2 robotics forums. Specialized for a user building a NAV2/ROS2 hexapod (legged robot). Use when the user needs to ask a question about tf trees, robot_localization, URDFs, costmaps, sensor fusion, or general ROS2/NAV2 issues.
---
# ROS Forum Post Drafter

Help the user write posts for ROS forums (e.g., ROS Discourse, Robotics Stack Exchange) that get answered. A good robotics support post makes the problem reproducible, shows the author's prior investigation (logs, tf trees, topic echoes), and gives responders concrete details (frames, parameters).

## User Context (Hexapod Progress)
The user is a beginner-to-intermediate robotics developer building a legged robot ("hexapod") with NAV2 and ROS2. They have already made progress with:
- **Nav2 Bringup**: Basic navigation setup, handling `cmd_vel` and `goal_pose` topics.
- **Costmaps**: Tuning inflation radius, global/local costmap layers, and working on 3D LIDAR ground segmentation for height-aware costmaps.
- **Controllers**: Experimented with Regulated Pure Pursuit (RPP) and DWB controllers.
- **Gazebo & URDF**: Integrated `robot_state_publisher`, modified URDFs with Gazebo reference blocks for sensors, and troubleshooted topic namespaces (e.g., `/points` suffix).
- **Sensor Fusion & SLAM**: Working with `robot_localization`, resolving conflicts with the Gazebo bridge, and troubleshooting 3D LiDAR scan-to-2D SLAM conversions.
- **Current active tasks**: Investigating the difference between `odom -> base_link` and `base_footprint`, and synchronizing SLAM with robot_localization.

## Workflow

### 1. Gather context
Collect from the user (or infer, flagging assumptions):
- Exact symptom and error message(s) - verbatim, not paraphrased.
- Hardware/Software: ROS2 distro (e.g., Jazzy/Rolling), NAV2 version, Gazebo version.
- Current robot state: URDF/SDF configurations, relevant `tf` transforms (e.g., `odom` -> `base_link`, `base_footprint`), or ROS parameter configurations (`nav2_params.yaml`).
- Which topics are involved and what `ros2 topic echo` shows.
- What has already been ruled out.

If information is missing, ask before writing. Never invent version numbers, error messages, or tf frame names.

### 2. Investigate before writing
- Ensure the problem makes sense in the context of ROS2/NAV2.
- Form precise hypotheses based on evidence (e.g., "the tf tree is missing a static transform between base_footprint and base_link").

### 3. Draft the post
Write it as a **continuous, first-person narrative**—one roboticist describing a problem to another. 
- **Title**: Specific and searchable (e.g., "robot_localization conflicts with Gazebo bridge on ROS2 Jazzy").
- **Opening**: A greeting, setup ("I'm developing a legged hexapod robot using ROS2 and NAV2..."), and the precise symptom.
- **Evidence**: Explain what was already checked. (e.g., "I verified my URDF has the correct Gazebo reference blocks"). Name what is provably working.
- **Configuration/Code**: Fenced code blocks for minimal YAML snippets (e.g., `nav2_params.yaml`), URDF blocks, launch scripts, or `tf` tree outputs. Highlight failing lines.
- **Hypotheses**: A short paragraph of reasoning.
- **The Question**: One explicit, clear question addressed to the community at the end.

**Voice rules:**
- Default to paragraphs over bulleted lists.
- Do not scaffold with robotic headings like "Context", "Symptom", "What I have already verified". Let the flow carry the reader.
- First-person, plain words. "I am seeing X when I launch Y."
- Keep register addresses, frame names (e.g., `base_link`), hex values, and topics inline as code.

### 4. Present and refine
Show the draft, list the assumptions you made, and note what the user should verify (e.g., specific parameter values or exact error logs) before posting.