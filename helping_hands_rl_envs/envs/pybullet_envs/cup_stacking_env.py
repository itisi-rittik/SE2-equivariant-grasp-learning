import numpy as np
from helping_hands_rl_envs.envs.pybullet_envs.pybullet_env import PyBulletEnv
from helping_hands_rl_envs.simulators import constants
from helping_hands_rl_envs.simulators.constants import NoValidPositionException

class CupStackingEnv(PyBulletEnv):
  def __init__(self, config):
    super(CupStackingEnv, self).__init__(config)

  def reset(self):
    ''''''
    while True:
      self.resetPybulletEnv()
      try:
        pos1 = [[0.3, 0, 0]]
        pos2 = [[0.3, 0, 0.1]]
        self._generateShapes(constants.CUP, 1, pos=pos1, random_orientation=self.random_orientation, scale=0.6)
        self._generateShapes(constants.CUP, 1, pos=pos2, random_orientation=self.random_orientation, scale=0.6)
        pass
      except NoValidPositionException as e:
        continue
      else:
        break
    return self._getObservation()

  def _checkTermination(self):
    ''''''
    return self._checkStack()

def createCupStackingEnv(config):
  return CupStackingEnv(config)

if __name__ == '__main__':
  workspace = np.asarray([[0.3, 0.7],
                          [-0.2, 0.2],
                          [0, 0.40]])
  env_config = {'workspace': workspace, 'max_steps': 10, 'obs_size': 128, 'render': True, 'fast_mode': True,
                'seed': 0, 'action_sequence': 'pxyzr', 'num_objects': 2, 'random_orientation': False,
                'reward_type': 'step_left', 'simulate_grasp': True, 'perfect_grasp': False, 'robot': 'kuka',
                'workspace_check': 'point', 'physics_mode': 'slow', 'hard_reset_freq': 1000}
  env = CupStackingEnv(env_config)
  while True:
    s, in_hand, obs = env.reset()