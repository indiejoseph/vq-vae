# -*- coding: utf-8 -*-
#/usr/bin/python2
'''
By kyubyong park. kbpark.linguist@gmail.com.
https://www.github.com/kyubyong/vq-vae
'''

from __future__ import print_function

from hparams import Hyperparams as hp
import tensorflow as tf
from utils import get_wav
import os
import glob
import numpy as np

def speaker2id(speaker):
    func = {speaker:id for id, speaker in enumerate(hp.speakers)}
    return func.get(speaker, None)

def id2speaker(id):
    func = {id:speaker for id, speaker in enumerate(hp.speakers)}
    return func.get(id, None)

def load_data(mode="train"):
    '''Loads data
    Args:
      mode: "train" or "eval".

    Returns:
      files: A list of sound file paths.
      speaker_ids: A list of speaker ids.
    '''
    if mode=="train":
        wavs = glob.glob('/data/private/speech/vctk/wavs/*.npy')
        # wavs = glob.glob('vctk/wavs/*.npy')
        qts = [wav.replace("wavs", "qts") for wav in wavs]
        speakers = np.array([speaker2id(os.path.basename(wav)[:4]) for wav in wavs], np.int32)

        return wavs, qts, speakers
    else: # test. two samples.
        files = ['/data/private/speech/vctk/qts/'+line.split("|")[0].strip() + ".npy" for line in hp.test_data.splitlines()]
        speaker_ids = [int(line.split("|")[1]) for line in hp.test_data.splitlines()]
        return files, speaker_ids

# load_data()
def get_batch():
    """Loads training data and put them in queues"""
    with tf.device('/cpu:0'):
        # Load data
        wavs, qts, speakers = load_data() # list


        # Calc total batch count
        num_batch = len(wavs) // hp.batch_size

        # to tensor
        wavs = tf.convert_to_tensor(wavs, tf.string)
        qts = tf.convert_to_tensor(qts, tf.string)
        speakers = tf.convert_to_tensor(speakers, tf.int32)

        # Create Queues
        wav, qt, speaker = tf.train.slice_input_producer([wavs, qts, speakers], shuffle=True)

        # Parse
        wav, = tf.py_func(lambda x: np.load(x), [wav], [tf.float32])  # (None, 1)
        qt, = tf.py_func(lambda x: np.load(x), [qt], [tf.int32])  # (None, 1)

        # Cut off
        qt = tf.pad(qt, ([0, hp.T], [0, 0]), mode="CONSTANT")[:hp.T, :]

        # Add shape information
        wav.set_shape((None,))
        qt.set_shape((hp.T, 1))
        speaker.set_shape(())

        # Batching
        qts, wavs, speakers = tf.train.batch(tensors=[qt, wav, speaker],
                                             batch_size=hp.batch_size,
                                             shapes=([hp.T, 1], [None,], []),
                                             num_threads=32,
                                             dynamic_pad=True)
        return qts, wavs, speakers, num_batch