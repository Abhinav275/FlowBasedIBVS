# import tensorflow.compat.v1 as tf
# tf.disable_v2_behavior()
from ..net import Net, Mode
from ..flownet_c.flownet_c import FlowNetC
from ..flownet_s.flownet_s import FlowNetS
from ..flow_warp import flow_warp
import tensorflow as tf
physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

class FlowNetCS(Net):

    def __init__(self, mode=Mode.TRAIN, debug=False):
        self.net_c = FlowNetC(mode, debug)
        self.net_s = FlowNetS(mode, debug)
        super(FlowNetCS, self).__init__(mode=mode, debug=debug)

    def model(self, inputs, training_schedule, trainable=True):
        with tf.compat.v1.variable_scope('FlowNetCS'):
            # Forward pass through FlowNetC with weights frozen
            net_c_predictions = self.net_c.model(inputs, training_schedule, trainable=False)

            # Perform flow warping (to move image B closer to image A based on flow prediction)
            warped = flow_warp(inputs['input_b'], net_c_predictions['flow'])

            # Compute brightness error: sqrt(sum (input_a - warped)^2 over channels)
            brightness_error = inputs['input_a'] - warped
            brightness_error = tf.square(brightness_error)
            brightness_error = tf.compat.v1.reduce_sum(brightness_error, keep_dims=True, axis=3)
            brightness_error = tf.sqrt(brightness_error)

            # Gather all inputs to FlowNetS
            inputs_to_s = {
                'input_a': inputs['input_a'],
                'input_b': inputs['input_b'],
                'warped': warped,
                'flow': net_c_predictions['flow'] * 0.05,
                'brightness_error': brightness_error,
            }

            return self.net_s.model(inputs_to_s, training_schedule, trainable=trainable)

    def loss(self, flow, predictions):
        return self.net_s.loss(flow, predictions)
