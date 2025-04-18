import os
import copy
import math
import numpy as np
import numpy.random as npr
from collections import deque
from abc import abstractmethod

import pybullet as pb
import pybullet_data

import helping_hands_rl_envs
import time

from helping_hands_rl_envs.simulators.pybullet.utils import pybullet_util
from helping_hands_rl_envs.simulators import constants
from helping_hands_rl_envs.simulators.pybullet.utils import object_generation
from helping_hands_rl_envs.simulators.pybullet.utils import transformations

class RobotBase:
  def __init__(self):
    self.root_dir = os.path.dirname(helping_hands_rl_envs.__file__)
    self.id = None
    self.num_joints = None
    self.arm_joint_names = list()
    self.arm_joint_indices = list()
    self.home_positions = None
    self.home_positions_joint = None
    self.end_effector_index = None
    self.holding_obj = None
    self.gripper_closed = False
    self.state = {
      'holding_obj': self.holding_obj,
      'gripper_closed': self.gripper_closed
    }

    self.position_gain = 0.02
    self.adjust_gripper_after_lift = False

  def saveState(self):
    self.state = {
      'holding_obj': self.holding_obj,
      'gripper_closed': self.gripper_closed
    }

  def restoreState(self):
    self.holding_obj = self.state['holding_obj']
    self.gripper_closed = self.state['gripper_closed']
    if self.gripper_closed:
      self.closeGripper(max_it=0)
    else:
      self.openGripper()

  def getPickedObj(self, objects):
    if not objects:
      return None
    for obj in objects:
      if len(pb.getContactPoints(self.id, obj.object_id)) >= 2:
          return obj
        # finger_link10, finger_link13 = 0, 0  # more realistic but SR drop
        # for point in pb.getContactPoints(self.id, obj.object_id):
        #   if point[3] == 10:
        #     finger_link10 += 1
        #   elif point[3] == 13:
        #     finger_link13 += 1
        # if finger_link10 > 0 and finger_link13 > 0:
        #   return obj

    return None

    # end_pos = self._getEndEffectorPosition()
    # sorted_obj = sorted(objects, key=lambda o: np.linalg.norm(end_pos-o.getGraspPosition()))
    # obj_pos = sorted_obj[0].getGraspPosition()
    # if np.linalg.norm(end_pos[:-1]-obj_pos[:-1]) < 0.05 and np.abs(end_pos[-1]-obj_pos[-1]) < 0.025:
    #   return sorted_obj[0]

  def pick(self, pos, rot, offset, dynamic=True, objects=None, simulate_grasp=True, top_down_approach=False):
    ''''''
    # Setup pre-grasp pos and default orientation
    self.openGripper()
    pre_pos = copy.copy(pos)
    if top_down_approach:
      # approach the object top-down
      pre_pos[2] += offset
    else:
      # approach the object along the z direction of the ee
      m = np.array(pb.getMatrixFromQuaternion(rot)).reshape(3, 3)
      pre_pos += m[:, 2] * offset

    pre_rot = rot

    # Move to pre-grasp pose and then grasp pose
    self.moveTo(pre_pos, pre_rot, dynamic)
    if simulate_grasp:
      self.moveTo(pos, rot, True, pos_th=1e-3, rot_th=1e-3)

      # Close gripper, if fully closed (nothing grasped), open gripper
      gripper_fully_closed = self.closeGripper()
      if gripper_fully_closed:
        self.openGripper()

      # Adjust gripper command after moving to pre pose. This will create more chance for a grasp, but while moving to
      # pre pose the gripper will shift around.
      if self.adjust_gripper_after_lift:
        self.moveTo(pre_pos, pre_rot, True)
        self.adjustGripperCommand()
      # Adjust gripper command before moving to pre pose. This will make the gripper more stable while moving to the pre
      # pose, but will reduce the chance for a grasp, especially in the cluttered scene.
      else:
        self.adjustGripperCommand()
        self.moveTo(pre_pos, pre_rot, True)

      for i in range(100):
        pb.stepSimulation()
    else:
      self.moveTo(pos, rot, dynamic)

    self.holding_obj = self.getPickedObj(objects)
    self.moveToJ(self.home_positions_joint, dynamic)
    self.checkGripperClosed()

  def place(self, pos, rot, offset, dynamic=True, simulate_grasp=True, top_down_approach=False):
    ''''''
    # Setup pre-grasp pos and default orientation
    pre_pos = copy.copy(pos)
    if top_down_approach:
      # approach the object top-down
      pre_pos[2] += offset
    else:
      # approach the object along the z direction of the ee
      m = np.array(pb.getMatrixFromQuaternion(rot)).reshape(3, 3)
      pre_pos += m[:, 2] * offset

    pre_rot = rot

    # Move to pre-grasp pose and then grasp pose
    self.moveTo(pre_pos, pre_rot, dynamic)
    if simulate_grasp:
      self.moveTo(pos, rot, True, pos_th=1e-3, rot_th=1e-3)
    else:
      self.moveTo(pos, rot, dynamic, pos_th=1e-3, rot_th=1e-3)

    # Grasp object and lift up to pre pose
    self.openGripper()
    self.holding_obj = None
    self.moveTo(pre_pos, pre_rot, dynamic)
    self.moveToJ(self.home_positions_joint, dynamic)

  def push(self, pos, rot, offset, dynamic=True):
    goal_pos = copy.copy(pos)
    m = np.array(pb.getMatrixFromQuaternion(rot)).reshape(3, 3)
    goal_pos += m[:, 1] * offset

    pre_pos = copy.copy(pos)
    m = np.array(pb.getMatrixFromQuaternion(rot)).reshape(3, 3)
    pre_pos -= m[:, 1] * 0.1

    self.closeGripper(primative=constants.PULL_PRIMATIVE)
    self.moveTo(pre_pos, rot, dynamic)
    self.moveTo(pos, rot, True)
    self.moveTo(goal_pos, rot, True)
    self.openGripper()
    self.moveToJ(self.home_positions_joint, dynamic)

  def pull(self, pos, rot, offset, dynamic=True):
    pre_pos = copy.copy(pos)
    m = np.array(pb.getMatrixFromQuaternion(rot)).reshape(3, 3)
    pre_pos += m[:, 2] * offset
    self.moveTo(pre_pos, rot, dynamic)
    # for mid in np.arange(0, offset, 0.05)[1:]:
    #   self.moveTo(pre_pos - m[:, 2] * mid, rot, True)
    self.moveTo(pos, rot, True)
    self.closeGripper(primative=constants.PULL_PRIMATIVE)
    # for mid in np.arange(0, offset, 0.05)[1:]:
    #   self.moveTo(pos + m[:, 2] * mid, rot, True)
    self.moveTo(pre_pos, rot, True)
    self.openGripper()
    self.moveToJ(self.home_positions_joint, dynamic)

  def roundPull(self, pos, rot, offset, radius, left=True, dynamic=True):
    pre_pos = copy.copy(pos)
    m = np.eye(4)
    m[:3, :3] = np.array(pb.getMatrixFromQuaternion(rot)).reshape(3, 3)
    pre_pos += m[:3, 2] * offset
    waypoint_theta = np.linspace(0, np.pi/2, 10)
    waypoint_pos = []
    waypoint_rot = []
    for theta in waypoint_theta:
      dx = -np.sin(theta) * radius
      if left:
        dy = (1 - np.cos(theta)) * radius
      else:
        dy = -(1 - np.cos(theta)) * radius
      waypoint_pos.append((pos[0] + dx, pos[1] + dy, pos[2]))
      if left:
        m_prime = m.dot(transformations.euler_matrix(0, theta, 0))
        # m_prime = m.dot(transformations.euler_matrix(0, 0, 0))
      else:
        m_prime = m.dot(transformations.euler_matrix(0, -theta, 0))
      waypoint_rot.append(transformations.quaternion_from_matrix(m_prime))

    self.moveTo(pre_pos, rot, dynamic)
    self.moveTo(pos, rot, True)
    self.closeGripper(primative=constants.PULL_PRIMATIVE)
    for i in range(len(waypoint_theta)):
      self.moveTo(waypoint_pos[i], waypoint_rot[i], True)

    self.openGripper()
    self.moveToJ(self.home_positions_joint, dynamic)



  def moveTo(self, pos, rot, dynamic=True, pos_th=1e-3, rot_th=1e-3):
    if dynamic or not self.holding_obj:
      self._moveToCartesianPose(pos, rot, dynamic, pos_th, rot_th)
    else:
      self._teleportArmWithObj(pos, rot)

  def moveToJ(self, pose, dynamic=True):
    if dynamic or not self.holding_obj:
      self._moveToJointPose(pose, dynamic)
    else:
      self._teleportArmWithObjJointPose(pose)

  @abstractmethod
  def openGripper(self):
    raise NotImplementedError

  @abstractmethod
  def closeGripper(self, max_it=100, primative=constants.PICK_PRIMATIVE):
    raise NotImplementedError

  @abstractmethod
  def checkGripperClosed(self):
    raise NotImplementedError

  def _moveToJointPose(self, target_pose, dynamic=True, max_it=1000):
    if dynamic:
      self._sendPositionCommand(target_pose)
      past_joint_pos = deque(maxlen=5)
      joint_state = pb.getJointStates(self.id, self.arm_joint_indices)
      joint_pos = list(zip(*joint_state))[0]
      n_it = 0
      while not np.allclose(joint_pos, target_pose, atol=1e-2) and n_it < max_it:
        pb.stepSimulation()
        n_it += 1
        # Check to see if the arm can't move any close to the desired joint position
        if len(past_joint_pos) == 5 and np.allclose(past_joint_pos[-1], past_joint_pos, atol=1e-3):
          break
        past_joint_pos.append(joint_pos)
        joint_state = pb.getJointStates(self.id, self.arm_joint_indices)
        joint_pos = list(zip(*joint_state))[0]

    else:
      self._setJointPoses(target_pose)

  def _moveToCartesianPose(self, pos, rot, dynamic=True, pos_th=1e-3, rot_th=1e-3):
    close_enough = False
    outer_it = 0
    max_outer_it = 10
    max_inner_it = 100

    while not close_enough and outer_it < max_outer_it:
      ik_solve = self._calculateIK(pos, rot)
      self._moveToJointPose(ik_solve, dynamic, max_inner_it)

      ls = pb.getLinkState(self.id, self.end_effector_index)
      new_pos = list(ls[4])
      new_rot = list(ls[5])
      close_enough = np.allclose(np.array(new_pos), pos, atol=pos_th) and \
                     np.allclose(np.array(new_rot), rot, atol=rot_th)
      # close_enough = np.allclose(np.array(new_pos + new_rot), np.array(list(pos) + list(rot)), atol=threshold)
      outer_it += 1

  @abstractmethod
  def _calculateIK(self, pos, rot):
    raise NotImplementedError

  def _teleportArmWithObj(self, pos, rot):
    if not self.holding_obj:
      self._moveToCartesianPose(pos, rot, False)
      return

    end_pos = self._getEndEffectorPosition()
    end_rot = self._getEndEffectorRotation()
    obj_pos, obj_rot = self.holding_obj.getPose()
    oTend = pybullet_util.getMatrix(end_pos, end_rot)
    oTobj = pybullet_util.getMatrix(obj_pos, obj_rot)
    endTobj = np.linalg.inv(oTend).dot(oTobj)

    self._moveToCartesianPose(pos, rot, False)
    end_pos_ = self._getEndEffectorPosition()
    end_rot_ = self._getEndEffectorRotation()
    oTend_ = pybullet_util.getMatrix(end_pos_, end_rot_)
    oTobj_ = oTend_.dot(endTobj)
    obj_pos_ = oTobj_[:3, -1]
    obj_rot_ = transformations.quaternion_from_matrix(oTobj_)

    self.holding_obj.resetPose(obj_pos_, obj_rot_)

  def getEndToHoldingObj(self):
    if not self.holding_obj:
      return np.zeros((4, 4))
    end_pos = self._getEndEffectorPosition()
    end_rot = self._getEndEffectorRotation()
    obj_pos, obj_rot = self.holding_obj.getPose()
    oTend = pybullet_util.getMatrix(end_pos, end_rot)
    oTobj = pybullet_util.getMatrix(obj_pos, obj_rot)
    endTobj = np.linalg.inv(oTend).dot(oTobj)
    return endTobj

  def _teleportArmWithObjJointPose(self, joint_pose):
    if not self.holding_obj:
      self._moveToJointPose(joint_pose, False)
      return

    end_pos = self._getEndEffectorPosition()
    end_rot = self._getEndEffectorRotation()
    obj_pos, obj_rot = self.holding_obj.getPose()
    oTend = pybullet_util.getMatrix(end_pos, end_rot)
    oTobj = pybullet_util.getMatrix(obj_pos, obj_rot)
    endTobj = np.linalg.inv(oTend).dot(oTobj)

    self._moveToJointPose(joint_pose, False)
    end_pos_ = self._getEndEffectorPosition()
    end_rot_ = self._getEndEffectorRotation()
    oTend_ = pybullet_util.getMatrix(end_pos_, end_rot_)
    oTobj_ = oTend_.dot(endTobj)
    obj_pos_ = oTobj_[:3, -1]
    obj_rot_ = transformations.quaternion_from_matrix(oTobj_)

    self.holding_obj.resetPose(obj_pos_, obj_rot_)

  def _getEndEffectorPosition(self):
    ''''''
    state = pb.getLinkState(self.id, self.end_effector_index)
    return np.array(state[4])

  def _getEndEffectorRotation(self):
    state = pb.getLinkState(self.id, self.end_effector_index)
    return np.array(state[5])

  @abstractmethod
  def _getGripperJointPosition(self):
    raise NotImplementedError

  @abstractmethod
  def _sendPositionCommand(self, commands):
    raise NotImplementedError

  @abstractmethod
  def adjustGripperCommand(self):
    raise NotImplementedError

  def _setJointPoses(self, q_poses):
    ''''''
    for i in range(len(q_poses)):
      motor = self.arm_joint_indices[i]
      pb.resetJointState(self.id, motor, q_poses[i])

    self._sendPositionCommand(q_poses)

  def plotEndEffectorFrame(self):
    line_id1 = pb.addUserDebugLine(self._getEndEffectorPosition(),
                                  self._getEndEffectorPosition() + 0.1 * transformations.quaternion_matrix(
                                    self._getEndEffectorRotation())[:3, 0], (1, 0, 0))
    line_id2 = pb.addUserDebugLine(self._getEndEffectorPosition(),
                                  self._getEndEffectorPosition() + 0.1 * transformations.quaternion_matrix(
                                    self._getEndEffectorRotation())[:3, 1], (0, 1, 0))
    line_id3 = pb.addUserDebugLine(self._getEndEffectorPosition(),
                                  self._getEndEffectorPosition() + 0.1 * transformations.quaternion_matrix(
                                    self._getEndEffectorRotation())[:3, 2], (0, 0, 1))
    return line_id1, line_id2, line_id3
