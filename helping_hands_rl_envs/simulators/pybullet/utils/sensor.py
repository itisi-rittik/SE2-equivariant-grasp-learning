import pybullet as pb
import numpy as np
import cupy as cp

class Sensor(object):
  def __init__(self, cam_pos, cam_up_vector, target_pos, target_size, near, far):
    self.view_matrix = pb.computeViewMatrix(
      cameraEyePosition=cam_pos,
      cameraUpVector=cam_up_vector,
      cameraTargetPosition=target_pos,
    )

    self.near = near
    self.far = far
    self.fov = np.degrees(2 * np.arctan((target_size / 2) / self.far))
    self.proj_matrix = pb.computeProjectionMatrixFOV(self.fov, 1, self.near, self.far)

  def getHeightmap(self, size):
    image_arr = pb.getCameraImage(width=size, height=size,
                                  viewMatrix=self.view_matrix,
                                  projectionMatrix=self.proj_matrix,
                                  renderer=pb.ER_TINY_RENDERER)
    depth_img = np.array(image_arr[3])
    depth = self.far * self.near / (self.far - (self.far - self.near) * depth_img)

    return np.abs(depth - np.max(depth)).reshape(size, size)

  def getPointCloud(self, size, to_numpy=True):
    image_arr = pb.getCameraImage(width=size, height=size,
                                  viewMatrix=self.view_matrix,
                                  projectionMatrix=self.proj_matrix,
                                  renderer=pb.ER_TINY_RENDERER)
    depthImg = cp.asarray(image_arr[3])

    # https://stackoverflow.com/questions/59128880/getting-world-coordinates-from-opengl-depth-buffer
    projectionMatrix = cp.asarray(self.proj_matrix).reshape([4,4],order='F')
    viewMatrix = cp.asarray(self.view_matrix).reshape([4,4],order='F')
    tran_pix_world = cp.linalg.inv(cp.matmul(projectionMatrix, viewMatrix))
    pixel_pos = cp.mgrid[0:size, 0:size]
    pixel_pos = pixel_pos/(size/2) - 1
    pixel_pos = cp.moveaxis(pixel_pos, 1, 2)
    pixel_pos[1] = -pixel_pos[1]
    zs = 2*depthImg.reshape(1, size, size) - 1
    pixel_pos = cp.concatenate((pixel_pos, zs))
    pixel_pos = pixel_pos.reshape(3, -1)
    augment = cp.ones((1, pixel_pos.shape[1]))
    pixel_pos = cp.concatenate((pixel_pos, augment), axis=0)
    position = cp.matmul(tran_pix_world, pixel_pos)
    pc = position / position[3]
    points = pc.T[:, :3]

    if to_numpy:
      points = cp.asnumpy(points)
    return points