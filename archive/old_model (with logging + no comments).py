"""Provides an interface for interacting with the model."""

import argparse
import logging
import os

import cv2
import tensorflow as tf

from operations import (convolution_2d, dense, elu, flatten_2d, globalaveragepooling_2d,
                        maxpooling_2d)
from preprocessing import ImagePreprocessor

logfmt = '%(asctime)s | W/N %(module)s | %(levelname)s: %(message)s'
datefmt = '%m/%d/%Y @ %I:%M:%S %p'
logging.basicConfig(level=logging.INFO, format=logfmt, datefmt=datefmt)
logger = logging.getLogger()

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
    # output = zeropadding_2d(input_, 3)
    # output = convolution_2d(output, 32, filter_size=8, strides=2)
    output = convolution_2d(input_, 32)
    output = elu(output)
    output = maxpooling_2d(output)
    output = convolution_2d(output, 64)
    output = elu(output)
    output = maxpooling_2d(output)
    output = convolution_2d(output, 128)
    output = elu(output)
    output = maxpooling_2d(output)
    output = convolution_2d(output, 256)
    output = elu(output)
    output = maxpooling_2d(output)
    output = convolution_2d(output, 512)
    output = elu(output)
    output = maxpooling_2d(output)
    output = globalaveragepooling_2d(output)
    output = flatten_2d(output)
    output = dense(output, 2)
    return output


def preprocess(image):
    """
    Preprocesses an image for the model.
    Converts image to a 256x256x3, 8-bit LAB representation.

    # Parameters
        image (str): Path to the image.
    # Returns
        A preprocessed image (numpy array).
    """
    image = cv2.imread(image)
    image = cv2.resize(image, (256, 256))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    image = image.astype('float32')
    image /= 255
    return image


def train(steps, resuming):
    """
    Trains the model with SGD + Momentum.

    # Parameters
        steps (int): Amount of batches to train.
        resuming (bool): Whether or not to train from scratch.
    """
    logging.info('Creating placeholders, defining operations...')
    data = tf.placeholder(tf.float32, shape=[None, 256, 256, 3])
    labels = tf.placeholder(tf.float32, shape=[None, 2])
    raw_output = model(data)
    objective = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(labels=labels,
                                                                       logits=raw_output))
    optimizer = tf.train.MomentumOptimizer(0.01, 0.9).minimize(objective)
    correct_prediction = tf.equal(tf.argmax(labels, axis=1), tf.argmax(raw_output, axis=1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    logging.info('Creating session and initializing `tf.train.Saver`.')
    sess = tf.InteractiveSession()
    sess.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    if resuming:
        logger.info('Loading checkpoint files...')
        saver.restore(sess, os.path.join(os.getcwd(), 'saved_model'))
    preproc = ImagePreprocessor()
    order = ['cats', 'dogs']
    accuracies = []
    step = 1
    for data_subset, labels_subset in preproc.preprocess_directory(steps, 'data/train', order):
        logger.info('Finished preprocessing image; finished fetching label.')
        logger.info('Evaluating current accuracy...')
        current_accuracy = accuracy.eval(feed_dict={data: data_subset, labels: labels_subset})
        current_accuracy = round(current_accuracy.item() * 100)
        logging.info('Managing moving average of accuracies...')
        accuracies.append(current_accuracy)
        if len(accuracies) == 10:
            reporting_accuracy = sum(accuracies) / len(accuracies)
            del accuracies[0]
        else:
            reporting_accuracy = 'WTNG'
        logging.info('Printing out stats...')
        current_objective = objective.eval(feed_dict={data: data_subset, labels: labels_subset})
        print('Step: {}/{} | Accuracy: {}% | Objective: {}'.format(step, steps, reporting_accuracy,
                                                                   current_objective))
        # TODO debugging info
        current_pred = raw_output.eval(feed_dict={data: data_subset, labels: labels_subset})
        print('Pred: {}'.format(current_pred))
        # TODO debugging info
        logging.info('Feeding to model...')
        optimizer.run(feed_dict={data: data_subset, labels: labels_subset})
        logging.info('End loop, incrementing step...')
        step += 1
    logger.info('All steps passed. Saving model and terminating...')
    saver.save(sess, os.path.join(os.getcwd(), 'saved_model'))


def test():
    # TODO
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-tr', '--train', action='store_true')
    parser.add_argument('-r', '--resuming', action='store_true')
    parser.add_argument('-s', '--steps', type=int)
    parser.add_argument('-te', '--test', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.set_defaults(resuming=False, verbose=False)
    args = parser.parse_args()
    if not args.verbose:
        logger.disabled = True
    if args.train:
        train(args.steps, args.resuming)
    elif args.test:
        test()