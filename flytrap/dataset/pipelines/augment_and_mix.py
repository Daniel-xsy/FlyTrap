# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Reference implementation of AugMix's data augmentation method in numpy."""
from .augmentations import augmentations
import numpy as np
from PIL import Image
from ...builder import PIPELINES


# def normalize(image):
#   """Normalize input image channel-wise to zero mean and unit variance."""
#   image = image.transpose(2, 0, 1)  # Switch to channel-first
#   mean, std = np.array(MEAN), np.array(STD)
#   image = (image - mean[:, None, None]) / std[:, None, None]
#   return image.transpose(1, 2, 0)


def apply_op(image, op, severity):
  image = np.clip(image * 255., 0, 255).astype(np.uint8)
  pil_img = Image.fromarray(image)  # Convert to PIL.Image
  pil_img = op(pil_img, severity)
  return np.asarray(pil_img) / 255.


@PIPELINES.register_module()
class AugMix:
  """Warpper for AugMix augmentations."""
  def __init__(self, severity=3, width=3, depth=-1, alpha=1., img_keys=None):
    self.severity = severity
    self.width = width
    self.depth = depth
    self.alpha = alpha
    self.img_keys = img_keys

  def __call__(self, results):
    for key in self.img_keys:
      image = results[key]
      mixed = augment_and_mix(image, self.severity, self.width, self.depth, self.alpha)
      results[key] = mixed
    return results


def augment_and_mix(image, severity=3, width=3, depth=-1, alpha=1.):
  """Perform AugMix augmentations and compute mixture.

  Args:
    image: Raw input image as float32 np.ndarray of shape (h, w, c)
    severity: Severity of underlying augmentation operators (between 1 to 10).
    width: Width of augmentation chain
    depth: Depth of augmentation chain. -1 enables stochastic depth uniformly
      from [1, 3]
    alpha: Probability coefficient for Beta and Dirichlet distributions.

  Returns:
    mixed: Augmented and mixed image.
  """
  ws = np.float32(
      np.random.dirichlet([alpha] * width))
  m = np.float32(np.random.beta(alpha, alpha))

  mix = np.zeros_like(image)
  for i in range(width):
    image_aug = image.copy()
    d = depth if depth > 0 else np.random.randint(1, 4)
    for _ in range(d):
      op = np.random.choice(augmentations)
      image_aug = apply_op(image_aug, op, severity)
    # Preprocessing commutes since all coefficients are convex
    mix += ws[i] * image_aug

  mixed = (1 - m) * image + m * mix
  return mixed
