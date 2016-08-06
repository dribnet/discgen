from __future__ import division, print_function

import os
import shutil
import theano
import theano.tensor as T

from blocks.extensions.saveload import Checkpoint

from sample import generate_latent_grid, grid_from_latents

class SampleCheckpoint(Checkpoint):
    def __init__(self, z_dim, image_size, channels, save_subdir, **kwargs):
        super(SampleCheckpoint, self).__init__(path=None, **kwargs)
        self.image_size = image_size
        self.channels = channels
        self.save_subdir = save_subdir
        self.iteration = 0
        self.epoch_src = "{0}/sample.png".format(save_subdir)
        # self.rows=7
        # self.cols=13
        self.rows=4
        self.cols=7
        # self.z = generate_latent_grid(z_dim, rows=self.rows, cols=self.cols, flat=False, gradient=False, spherical=True, gaussian=False,
        #     anchors=False, anchor_images=None, splash=False, spacing=3, analogy=False)
        # anchors = np.random.normal(loc=0, scale=1, size=( * , z_dim))
        anchors = generate_latent_grid(z_dim, rows=((self.rows // 3) + 1), cols=((self.cols // 3) + 1), flat=False, gradient=False,
            spherical=False, gaussian=False, anchors=None, anchor_images=None, splash=False, spacing=3, analogy=False)
        self.z = generate_latent_grid(z_dim, rows=self.rows, cols=self.cols, flat=False, gradient=False, spherical=True, gaussian=False,
            anchors=anchors, anchor_images=None, splash=True, spacing=3, analogy=False)
        if not os.path.exists(self.save_subdir):
            os.makedirs(self.save_subdir)

    def do(self, callback_name, *args):
        """Sample the model and save images to disk
        """
        grid_from_latents(self.z, self.main_loop.model, rows=self.rows, cols=self.cols, anchor_images=None, tight=False, shoulders=False, save_path=self.epoch_src)
        if os.path.exists(self.epoch_src):
            epoch_dst = "{0}/epoch-{1:03d}.png".format(self.save_subdir, self.iteration)
            self.iteration = self.iteration + 1
            shutil.copy2(self.epoch_src, epoch_dst)
            os.system("convert -delay 5 -loop 1 {0}/epoch-*.png {0}/training.gif".format(self.save_subdir))
