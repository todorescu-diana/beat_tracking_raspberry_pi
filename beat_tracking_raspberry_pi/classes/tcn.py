from keras.layers import Conv1D, Activation, SpatialDropout1D
import keras

from constants.constants import ACTIVATION, CONV_NUM_FILTERS, DROPOUT_RATE, TCN_DILATIONS, TCN_KERNEL_SIZE


def residual_block(x, i, activation, num_filters, kernel_size, padding, dropout_rate=0, name=''):
    name = name + '_dilation_%d' % i

    # residual
    res_x = Conv1D(num_filters, 1, padding='same', name=name + '_1x1_conv_residual')(x)
    # dilated convolutions, with dilation rates of i and 2i
    conv_1 = Conv1D(
        filters=num_filters,
        kernel_size=kernel_size,
        dilation_rate=i,
        padding=padding,
        name=name + '_dilated_conv_1',
    )(x)
    conv_2 = Conv1D(
        filters=num_filters,
        kernel_size=kernel_size,
        dilation_rate=i * 2,
        padding=padding,
        name=name + '_dilated_conv_2',
    )(x)
    # concatenate the output of the two dilations
    concat = keras.layers.concatenate([conv_1, conv_2], name=name + '_concat')

    x = Activation(activation, name=name + '_activation')(concat)
    x = SpatialDropout1D(dropout_rate, name=name + '_spatial_dropout_%f' % dropout_rate)(x)
    # 1x1 conv. to obtain a representation with the same size as the residual
    x = Conv1D(num_filters, 1, padding='same', name=name + '_1x1_conv')(x)
    # add the residual to the processed data
    return keras.layers.add([res_x, x], name=name + '_merge_residual')


class TCN:
    def __init__(
            self,
            num_filters=CONV_NUM_FILTERS,
            kernel_size=TCN_KERNEL_SIZE,
            dilations=TCN_DILATIONS,
            activation=ACTIVATION,
            padding='same',
            dropout_rate=DROPOUT_RATE,
            name='tcn'
    ):
        self.name = name
        self.dropout_rate = dropout_rate
        self.activation = activation
        self.dilations = dilations
        self.kernel_size = kernel_size
        self.num_filters = num_filters
        self.padding = padding

        if padding != 'causal' and padding != 'same':
            raise ValueError("Only 'causal' or 'same' padding are compatible for this layer.")

    def __call__(self, inputs):
        x = inputs
        for i in self.dilations:
            # feed the output of the previous layer into the next layer
            # increase dilation rate for each consecutive layer
            x = residual_block(
                x, i, self.activation, self.num_filters, self.kernel_size, self.padding, self.dropout_rate, name=self.name
            )
        x = Activation(self.activation, name=self.name + '_activation')(x)

        return x