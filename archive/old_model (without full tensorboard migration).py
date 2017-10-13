"""Provides an interface for interacting with the model."""

import argparse

import tensorflow as tf

from layers.activations import elu, sigmoid
from layers.convolutional import convolution_2d, flatten_2d, globalaveragepooling_2d, maxpooling_2d
from layers.core import dense
from layers.meta import restore_model, save_model
from layers.objectives import mean_binary_entropy
from layers.optimizers import nesterov_momentum
from layers.preprocessing import ImagePreprocessor
from layers.reporters import categorical_accuracy_reporter, report

# Inside of this directory, there should be 2 more directories, `cats` and `dogs`.
# Those directories will contain the actual images.
DATA_DIR = 'data/train'


def model(input_):
    """
    Defines the model's architecture.

    # Parameters
        input_ (tf.placeholder): Placeholder for the input data.
    # Returns
        The output of the model.
    """
    output = convolution_2d(input_, 8)
    output = elu(output)
    output = maxpooling_2d(output)
    output = convolution_2d(output, 16)
    output = elu(output)
    output = convolution_2d(output, 16)
    output = elu(output)
    output = maxpooling_2d(output)
    output = convolution_2d(output, 32)
    output = elu(output)
    output = convolution_2d(output, 32)
    output = elu(output)
    output = convolution_2d(output, 32)
    output = elu(output)
    output = maxpooling_2d(output)
    output = convolution_2d(output, 64)
    output = elu(output)
    output = convolution_2d(output, 64)
    output = elu(output)
    output = convolution_2d(output, 64)
    output = elu(output)
    output = convolution_2d(output, 64)
    output = elu(output)
    output = maxpooling_2d(output)
    output = globalaveragepooling_2d(output)
    output = flatten_2d(output)
    output = dense(output, 2)
    return output


def train(steps, resuming):
    """
    Trains the model and saves the result.

    # Parameters
        steps (int): Amount of images to train on.
        resuming (bool): Whether or not to train from scratch.
    """
    with tf.name_scope('input'):
        data = tf.placeholder(tf.float32, shape=[None, 256, 256, 3])
        labels = tf.placeholder(tf.float32, shape=[None, 2])
    with tf.name_scope('output'):
        logits = model(data)
        output = sigmoid(logits)
    with tf.name_scope('objective'):
        objective = mean_binary_entropy(labels, logits)
    with tf.name_scope('accuracy'):
        accuracy = categorical_accuracy_reporter(labels, output)
    with tf.name_scope('optimizer'):
        optimizer = nesterov_momentum(objective)
    tf.summary.scalar('objective', objective)
    tf.summary.scalar('accuracy', accuracy)
    summary = tf.summary.merge_all()
    # TODO: Refactor. Code is ugly as fuck!
    sess = tf.Session()
    with sess.as_default():
        tf.global_variables_initializer().run()
        writer = tf.summary.FileWriter('test', graph=tf.get_default_graph())
        if resuming:
            restore_model(sess)
        prepro = ImagePreprocessor()
        accuracies = []
        objectives = []
        for step, data_arg, label_arg in prepro.preprocess_directory(steps, 'data/train',
                                                                     ['cats', 'dogs'],
                                                                     rescale=(256, 256)):
            current_accuracy = accuracy.eval(feed_dict={data: data_arg, labels: label_arg})
            current_objective = objective.eval(feed_dict={data: data_arg, labels: label_arg})
            accuracies.append(current_accuracy)
            objectives.append(current_objective)
            if step % 10 == 0:
                moving_accuracy = sum(accuracies) / len(accuracies)
                moving_objective = sum(objectives) / len(objectives)
                accuracies.clear()
                objectives.clear()
            else:
                moving_accuracy = 'WTNG'
                moving_objective = 'WTNG'
            report(step, steps, moving_accuracy, moving_objective)
            optimizer.run(feed_dict={data: data_arg, labels: label_arg})
            current_summary = summary.eval(feed_dict={data: data_arg, labels: label_arg})
            writer.add_summary(current_summary, step)
        save_model(sess)


def test():
    # TODO
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-tr', '--train', action='store_true')
    parser.add_argument('-r', '--resuming', action='store_true')
    parser.add_argument('-s', '--steps', type=int)
    parser.add_argument('-te', '--test', action='store_true')
    parser.set_defaults(resuming=False)
    args = parser.parse_args()
    if args.train:
        train(args.steps, args.resuming)
    elif args.test:
        test()