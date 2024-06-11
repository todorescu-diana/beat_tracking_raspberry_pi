import sys
import keras.backend as K
from keras import Model
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, EarlyStopping, CSVLogger
from keras.layers import (
    Activation,
    Dense,
    Input,
    Conv2D,
    MaxPooling2D,
    Reshape,
    Dropout
)
from keras.optimizers import Adam
from matplotlib import pyplot as plt
from classes.tcn import TCN
from utils.utils import get_detected_beats_dbn
from constants.constants import CSV_LOSSES_PATH, INPUT_SHAPE, ACTIVATION_1, NUM_FILTERS_TCN_1, KERNEL_SIZE_TCN_1, NUM_FILTERS_2, \
    DROPOUT_RATE_2, NUM_DILATIONS_TCN_2, NUM_EPOCHS, plot_colors
import io
import numpy as np
from contextlib import redirect_stdout

# pad features
def cnn_pad(data, pad_frames):
    """Pad the data by repeating the first and last frame N times."""
    pad_start = np.repeat(data[:1], pad_frames, axis=0)
    pad_stop = np.repeat(data[-1:], pad_frames, axis=0)
    return np.concatenate((pad_start, data, pad_stop))


def build_model(input_shape=INPUT_SHAPE, num_conv_filters=NUM_FILTERS_2, activation=ACTIVATION_1,
                dropout_rate=DROPOUT_RATE_2, tcn_num_filters=NUM_FILTERS_TCN_1, tcn_kernel_size=KERNEL_SIZE_TCN_1,
                tcn_num_dilations=NUM_DILATIONS_TCN_2):
    # Input layer
    input_layer = Input(batch_shape=input_shape)

    # stack of 3 conv layers, each conv, activation, max. pooling & dropout
    conv_1 = Conv2D(num_conv_filters, (3, 3), padding='valid', name='conv_1_conv')(input_layer)
    conv_1 = Activation(activation, name='conv_1_activation')(conv_1)
    conv_1 = MaxPooling2D((1, 3), name='conv_1_max_pooling')(conv_1)
    conv_1 = Dropout(dropout_rate, name='conv_1_dropout')(conv_1)

    conv_2 = Conv2D(num_conv_filters, (3, 3), padding='valid', name='conv_2_conv')(conv_1)
    conv_2 = Activation(activation, name='conv_2_activation')(conv_2)
    conv_2 = MaxPooling2D((1, 3), name='conv_2_max_pooling')(conv_2)
    conv_2 = Dropout(dropout_rate, name='conv_2_dropout')(conv_2)

    conv_3 = Conv2D(num_conv_filters, (1, 8), padding='valid', name='conv_3_conv')(conv_2)
    conv_3 = Activation(activation, name='conv_3_activation')(conv_3)
    conv_3 = MaxPooling2D((1, 3), name='conv_3_max_pooling')(conv_3)
    conv_3 = Dropout(dropout_rate, name='conv_3_dropout')(conv_3)

    # Flatten layer
    reshape = Reshape(target_shape=(-1, num_conv_filters))(conv_3)

    # TCN layers
    dilations = [2 ** i for i in range(tcn_num_dilations)]
    tcn = TCN(
        num_filters=[tcn_num_filters] * len(dilations),
        kernel_size=tcn_kernel_size,
        dilations=dilations,
        activation=activation,
        padding='same',
        dropout_rate=dropout_rate,
    )(reshape)
    # Dense layers
    beats = Dropout(dropout_rate, name='beats_dropout')(tcn)
    beats = Dense(1)(beats)
    beats = Activation(activation='sigmoid', name='beats')(beats)

    # Model
    return Model(inputs=input_layer, outputs=[beats])


def compile_model(model, summary=False, model_name='', summary_save_path=''):
    optimizer = Adam(learning_rate=0.002)

    model.compile(optimizer=optimizer,
                  loss=[K.binary_crossentropy],
                  metrics=['binary_accuracy'])
    if summary and summary_save_path != '':
        # create a string buffer to capture the summary
        buffer = io.StringIO()

        # redirect the standard output to the string buffer
        with redirect_stdout(buffer):
            model.summary()

        # get the model summary from the string buffer
        model_summary = buffer.getvalue()

        # save the model summary to a file
        with open(summary_save_path + '/' + model_name + '.txt', "w") as text_file:
            text_file.write(model_summary)


def train_model(model, train_data, test_data=None, model_name='', save_model=False, model_save_path='', epochs=NUM_EPOCHS, plot_save=False, plot_save_path=''):
    # define callbacks

    mc = ModelCheckpoint(model_save_path + '/' + model_name + '_best.h5', monitor='loss', save_best_only=True, verbose=0)
    lr = ReduceLROnPlateau(monitor='loss', factor=0.2, patience=10, verbose=1, mode='auto', min_delta=1e-3, cooldown=0,
                           min_lr=1e-7)
    es = EarlyStopping(monitor='loss', min_delta=1e-4, patience=50, verbose=0)
    csv_logger = CSVLogger(CSV_LOSSES_PATH + '/' + model_name + '.csv', append=True, separator=';')

    if save_model and model_save_path != '':
        callbacks = [mc, lr, es, csv_logger]
    else:
        callbacks = [lr, es, csv_logger]

    if test_data is not None:
        validation_data = test_data
        validation_steps = len(test_data)
    else:
        validation_data = None
        validation_steps = None

    # train the model
    history = model.fit(train_data,
                        steps_per_epoch=len(train_data),
                        epochs=epochs,
                        validation_data=validation_data,
                        validation_steps=validation_steps,
                        shuffle=True,
                        callbacks=callbacks)

    plot_metrics(history, metric='binary_accuracy', model_name=model_name, plot_save=plot_save, plot_save_path=plot_save_path, validation_included=(test_data is not None))
    plot_metrics(history, metric='loss', model_name=model_name, plot_save=plot_save, plot_save_path=plot_save_path, validation_included=(test_data is not None))


def plot_metrics(history, metric, validation_included, model_name='', plot_save=False, plot_save_path=''):
    valid_metrics = history.history.keys()

    if metric not in valid_metrics:
        print(f"Error: '{metric}' is not a valid metric. Valid metrics are: {', '.join(valid_metrics)}")
        return

    plt.figure(figsize=(12, 6))

    plt.plot(history.history[metric], color=plot_colors['train'])
    if validation_included:
        plt.plot(history.history['val_' + metric], color=plot_colors['val'])
    plt.title('Model ' + model_name + ' ' + metric)
    plt.xlabel('epoch')
    plt.ylabel(metric)
    if validation_included:
        plt.legend(['train', 'val'], loc='upper right')
    else:
        plt.legend(['train'], loc='upper right')
    plt.tight_layout()

    if plot_save and plot_save_path != '':
        if validation_included:
            plt.savefig(f'{plot_save_path}/{model_name}_{metric}_plot.png', format='png')
            print(f"Plot saved as {plot_save_path}/{model_name}_{metric}_plot.png")
        else:
            plt.savefig(f'{plot_save_path}/{model_name}_{metric}_plot.png', format='png')
            print(f"Plot saved as {plot_save_path}/{model_name}_{metric}_plot.png")
    else:
        plt.show()


def predict(model, spectrogram_sequence_dataset):
    activations = {}
    detections = {}
    print("INSIDE PREDICT FUNCTION")

    for i, batch_data in enumerate(spectrogram_sequence_dataset):
        # file name
        f = spectrogram_sequence_dataset.ids[i]
        # print progress
        sys.stderr.write('\rprocessing file %d of %d: %12s' % (i + 1, len(spectrogram_sequence_dataset), f))
        sys.stderr.flush()
        # predict activations
        x = batch_data
        beats = model.predict(x)
        beats_act = beats.squeeze()
        # beats
        beat_detections = get_detected_beats_dbn(beats_act)

        # collect activations and detections
        activations[f] = {'beats': beats_act}
        detections[f] = {'beats': beat_detections}

    return activations, detections
