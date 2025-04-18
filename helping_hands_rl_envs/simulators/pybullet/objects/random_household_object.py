import sys
sys.path.append('..')

import pybullet as pb
import numpy as np
import os
import glob
import re

import helping_hands_rl_envs
from helping_hands_rl_envs.simulators.pybullet.objects.pybullet_object import PybulletObject
from helping_hands_rl_envs.simulators import constants

root_dir = os.path.dirname(helping_hands_rl_envs.__file__)
urdf_pattern = os.path.join(root_dir, constants.URDF_PATH, 'random_household_object/*/*.urdf')
found_object_directories = glob.glob(urdf_pattern)
total_num_objects = len(found_object_directories)

class RandomHouseHoldObject(PybulletObject):
  def __init__(self, pos, rot, scale, index=-1):
    # for i, urdf in enumerate(found_object_directories):
    #   pb.loadURDF(urdf, basePosition=[0.1+i//4*0.15, 0.1+i%4*0.15, 0.05], baseOrientation=(0, 0, 0, 1), globalScaling=scale)

    if index >= 0:
      urdf_filepath = found_object_directories[index]
    else:
      urdf_filepath = found_object_directories[np.random.choice(np.arange(total_num_objects), 1)[0]]
    object_id = pb.loadURDF(urdf_filepath, basePosition=pos, baseOrientation=rot, globalScaling=scale)

    super(RandomHouseHoldObject, self).__init__(constants.RANDOM, object_id)
