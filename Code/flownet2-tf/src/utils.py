import tensorflow as tf
# import tensorflow.compat.v1 as tf
# tf.disable_v2_behavior()
physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

# Thanks, https://github.com/tensorflow/tensorflow/issues/4079
def LeakyReLU(x, leak=0.1, name="lrelu"):
    with tf.compat.v1.variable_scope(name):
        return (0.5 * (1.0 + leak)) * x + (0.5 * (1.0 - leak)) * abs(x)


def average_endpoint_error(labels, predictions):
    """
    Given labels and predictions of size (N, H, W, 2), calculates average endpoint error:
        sqrt[sum_across_channels{(X - Y)^2}]
    """
    num_samples = predictions.shape.as_list()[0]
    with tf.name_scope(None, "average_endpoint_error", (predictions, labels)) as scope:
        predictions = tf.to_float(predictions)
        labels = tf.to_float(labels)
        predictions.get_shape().assert_is_compatible_with(labels.get_shape())

        squared_difference = tf.square(tf.subtract(predictions, labels))
        # sum across channels: sum[(X - Y)^2] -> N, H, W, 1
        loss = tf.reduce_sum(squared_difference, 3, keep_dims=True)
        loss = tf.sqrt(loss)
        return tf.reduce_sum(loss) / num_samples


def pad(tensor, num=1):
    """
    Pads the given tensor along the height and width dimensions with `num` 0s on each side
    """
    return tf.pad(tensor, [[0, 0], [num, num], [num, num], [0, 0]], "CONSTANT")


def antipad(tensor, num=1):
    """
    Performs a crop. "padding" for a deconvolutional layer (conv2d tranpose) removes
    padding from the output rather than adding it to the input.
    """
    batch, h, w, c = tensor.shape.as_list()
    return tf.slice(tensor, begin=[0, num, num, 0], size=[batch, h - 2 * num, w - 2 * num, c])
