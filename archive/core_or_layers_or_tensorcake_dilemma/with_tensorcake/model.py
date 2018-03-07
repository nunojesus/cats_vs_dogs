"""Provides an interface for interacting with the model."""

import argparse

import numpy as np
import tensorflow as tf
from tensorcake.layers.activations import elu
from tensorcake.layers.convolutional import conv_2d
from tensorcake.layers.core import dense, flatten_2d
from tensorcake.layers.pooling import global_avg_pool_2d, max_pool_2d
from tensorcake.optimization.accuracies import categorical_accuracy_reporter
from tensorcake.optimization.objectives import mean_absolute_error
from tensorcake.optimization.optimizers import nesterov_momentum
from tensorcake.preprocessing.image import ImagePreprocessor
from tensorcake.utils.report import tensorboard_writer
from tensorcake.utils.state import restore_variables, save_variables


def model(input_):
    """
    Defines the model's architecture.

    # Parameters
        input_ (tf.placeholder): Placeholder for the input data.
    # Returns
        The output of the model.
    """
    output = conv_2d(input_, 8)
    output = elu(output)
    output = max_pool_2d(output)
    output = conv_2d(output, 16)
    output = elu(output)
    output = conv_2d(output, 16)
    output = elu(output)
    output = max_pool_2d(output)
    output = conv_2d(output, 32)
    output = elu(output)
    output = conv_2d(output, 32)
    output = elu(output)
    output = conv_2d(output, 32)
    output = elu(output)
    output = max_pool_2d(output)
    output = conv_2d(output, 64)
    output = elu(output)
    output = conv_2d(output, 64)
    output = elu(output)
    output = conv_2d(output, 64)
    output = elu(output)
    output = conv_2d(output, 64)
    output = elu(output)
    output = max_pool_2d(output)
    output = conv_2d(output, 128)
    output = elu(output)
    output = conv_2d(output, 128)
    output = elu(output)
    output = conv_2d(output, 128)
    output = elu(output)
    output = conv_2d(output, 128)
    output = elu(output)
    output = conv_2d(output, 128)
    output = elu(output)
    output = max_pool_2d(output)
    output = global_avg_pool_2d(output)
    output = flatten_2d(output)
    output = dense(output, 2)
    return output


def train(steps, resuming):
    """
    Trains the model and saves the result.

    # Parameters
        steps (int): Amount of images to train on.
        resuming (bool): Whether or not to resume training on a saved model.
    """
    with tf.name_scope('input'):
        data = tf.placeholder(tf.float32, shape=[None, 256, 256, 3])
        labels = tf.placeholder(tf.float32, shape=[None, 2])
    with tf.name_scope('output'):
        output = model(data)
    with tf.name_scope('objective'):
        objective = mean_absolute_error(labels, output)
    with tf.name_scope('accuracy'):
        accuracy = categorical_accuracy_reporter(labels, output)
    with tf.name_scope('optimizer'):
        optimizer = nesterov_momentum(objective)
    tf.summary.scalar('objective', objective)
    tf.summary.scalar('accuracy', accuracy)
    summary = tf.summary.merge_all()
    sess = tf.Session()
    with sess:
        if resuming:
            restore_variables(sess)
        else:
            tf.global_variables_initializer().run()
        writer = tensorboard_writer()
        preprocessor = ImagePreprocessor()
        encoding = {'cats': [1, 0], 'dogs': [0, 1]}
        for step, data_arg, label_arg in preprocessor.preprocess_directory(steps, 'data/train',
                                                                           encoding, (256, 256)):
            print('Step: {}/{}'.format(step, steps))
            optimizer.run(feed_dict={data: data_arg, labels: label_arg})
            current_summary = summary.eval(feed_dict={data: data_arg, labels: label_arg})
            writer.add_summary(current_summary, global_step=step)
        save_variables(sess)


def test(image):
    """
    Test the model on a single image.

    # Parameters
        image (str): Path to the image in question.
    # Prints
        The resulting tensor of predictions.
        In this case, argmax==0 means 'cat' and argmax==1 means 'dog'.
    """
    data = tf.placeholder(tf.float32, shape=[None, 256, 256, 3])
    with tf.name_scope('output'):
        output = model(data)
    sess = tf.Session()
    with sess.as_default():
        restore_variables(sess)
        preprocessor = ImagePreprocessor()
        data_arg = np.array([preprocessor.preprocess_image(image, (256, 256))])
        result = output.eval(feed_dict={data: data_arg})
        print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-tr', '--train', action='store_true')
    parser.add_argument('-r', '--resuming', action='store_true')
    parser.add_argument('-s', '--steps', type=int)
    parser.add_argument('-te', '--test', action='store_true')
    parser.add_argument('-i', '--image')
    parser.set_defaults(resuming=False)
    args = parser.parse_args()
    if args.train:
        train(args.steps, args.resuming)
    elif args.test:
        test(args.image)