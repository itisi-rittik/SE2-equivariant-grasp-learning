import os

import pybullet as pb
import numpy as np
import numpy.random as npr

import helping_hands_rl_envs
from helping_hands_rl_envs.simulators.pybullet.objects.cube import Cube
from helping_hands_rl_envs.simulators.pybullet.objects.cylinder import Cylinder
from helping_hands_rl_envs.simulators.pybullet.objects.brick import Brick
from helping_hands_rl_envs.simulators.pybullet.objects.grasp_net_obj import GraspNetObject
from helping_hands_rl_envs.simulators.pybullet.objects.triangle import Triangle
from helping_hands_rl_envs.simulators.pybullet.objects.roof import Roof
from helping_hands_rl_envs.simulators.pybullet.objects.random_object import RandomObject
from helping_hands_rl_envs.simulators.pybullet.objects.random_brick import RandomBrick
from helping_hands_rl_envs.simulators.pybullet.objects.cup import Cup
from helping_hands_rl_envs.simulators.pybullet.objects.bowl import Bowl
from helping_hands_rl_envs.simulators.pybullet.objects.plate import Plate
from helping_hands_rl_envs.simulators.pybullet.objects.test_tube import TestTube
from helping_hands_rl_envs.simulators.pybullet.objects.swab import Swab
from helping_hands_rl_envs.simulators.pybullet.objects.random_block import RandomBlock
from helping_hands_rl_envs.simulators.pybullet.objects.random_household_object import RandomHouseHoldObject
from helping_hands_rl_envs.simulators.pybullet.objects.random_household_object_200 import RandomHouseHoldObject200
from helping_hands_rl_envs.simulators.pybullet.objects.spoon import Spoon

def generateCube(pos, rot, scale):
  ''''''
  return Cube(pos, rot, scale)

def generateBrick(pos, rot, scale):
  return Brick(pos, rot, scale)

def generateCylinder(pos, rot, scale):
  return Cylinder(pos, rot, scale)

def generateTriangle(pos, rot, scale):
  return Triangle(pos, rot, scale)

def generateRoof(pos, rot, scale):
  return Roof(pos, rot, scale)

def generateCup(pos, rot, scale):
  return Cup(pos, rot, scale)

def generateBowl(pos, rot, scale):
  return Bowl(pos, rot, scale)

def generatePlate(pos, rot, scale, model_id):
  return Plate(pos, rot, scale, model_id)

def generateTestTube(pos, rot, scale, model_id):
  return TestTube(pos, rot, scale, model_id)

def generateSwab(pos, rot, scale, model_id):
  return Swab(pos, rot, scale, model_id)

def generateRandomObj(pos, rot, scale, z_scale=1):
  return RandomObject(pos, rot, scale, z_scale)

def generateRandomBrick(pos, rot, x_scale, y_scale, z_scale):
  return RandomBrick(pos, rot, x_scale, y_scale, z_scale)

def generateRandomBlock(pos, rot, scale):
  return RandomBlock(pos, rot, scale)

def generateRandomHouseHoldObj(pos, rot, scale, index):
  return RandomHouseHoldObject(pos, rot, scale, index)

def generateRandomHouseHoldObj200(pos, rot, scale, index):
  return RandomHouseHoldObject200(pos, rot, scale, index)

def generateGraspNetObject(pos, rot, scale, index):
  return GraspNetObject(pos, rot, scale, index)

def generateSpoon(pos, rot, scale):
  return Spoon(pos, rot, scale)