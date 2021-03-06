import theano
from theano import tensor
from blocks.model import Model
from blocks.select import Selector
from blocks.bricks import Random
from blocks.serialization import load
from blocks.graph import ComputationGraph
from blocks.utils import shared_floatx

def get_image_encoder_function(model):
    selector = Selector(model.top_bricks)
    encoder_convnet, = selector.select('/encoder_convnet').bricks
    encoder_mlp, = selector.select('/encoder_mlp').bricks

    print('Building computation graph...')
    x = tensor.tensor4('features')
    phi = encoder_mlp.apply(encoder_convnet.apply(x).flatten(ndim=2))
    nlat = encoder_mlp.output_dim // 2
    mu_phi = phi[:, :nlat]
    log_sigma_phi = phi[:, nlat:]
    epsilon = Random().theano_rng.normal(size=mu_phi.shape, dtype=mu_phi.dtype)
    z = mu_phi + epsilon * tensor.exp(log_sigma_phi)
    computation_graph = ComputationGraph([x, z])

    print('Compiling reconstruction function...')
    encoder_function = theano.function(
        computation_graph.inputs, computation_graph.outputs)
    return encoder_function

def get_decoder_function(model):
    selector = Selector(model.top_bricks)
    decoder_mlp, = selector.select('/decoder_mlp').bricks
    decoder_convnet, = selector.select('/decoder_convnet').bricks

    print('Building computation graph...')
    z = tensor.matrix()
    mu_theta = decoder_convnet.apply(
        decoder_mlp.apply(z).reshape(
            (-1,) + decoder_convnet.get_dim('input_')))
    computation_graph = ComputationGraph([z, mu_theta])

    print('Compiling sampling function...')
    decoder_function = theano.function(
        computation_graph.inputs, computation_graph.outputs)

    return decoder_function

class DiscGenModel:
    def __init__(self, filename=None, model=None):
        self.encoder_function = None
        self.sampling_function = None
        if model is not None:
            self.model = model
        else:
            try:
                self.model = Model(load(filename).algorithm.cost)
            except AttributeError:
                # newer version of blocks
                with open(filename, 'rb') as src:
                    self.model = Model(load(src).algorithm.cost)

    def encode_images(self, images):
        if self.encoder_function is None:
            self.encoder_function = get_image_encoder_function(self.model)
        # print('Encoding...')
        examples, latents = self.encoder_function(images)
        return latents

    def get_zdim(self):
        selector = Selector(self.model.top_bricks)
        decoder_mlp, = selector.select('/decoder_mlp').bricks
        return decoder_mlp.input_dim

    def sample_at(self, z):
        if self.sampling_function is None:
            self.sampling_function = get_decoder_function(self.model)
        z_float = theano._asarray(z, dtype=theano.config.floatX)
        # print('Sampling...')
        latents, samples = self.sampling_function(z_float)
        # print(samples.shape)
        return samples
