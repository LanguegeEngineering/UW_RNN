# -*- coding: utf-8 -*-
"""PL_RNN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19a0VAPRdD2MUXtx74QO3m7TBEzCvRTI0

# Polski

Tu używamy datasetu z CLARINU -  https://lepiszcze.ml/datasets/
"""

import numpy as np

import tensorflow_datasets as tfds
import tensorflow as tf

tfds.disable_progress_bar()

"""Import `matplotlib` and create a helper function to plot graphs:"""

import matplotlib.pyplot as plt


def plot_graphs(history, metric):
  plt.plot(history.history[metric])
  plt.plot(history.history['val_'+metric], '')
  plt.xlabel("Epochs")
  plt.ylabel(metric)
  plt.legend([metric, 'val_'+metric])

!pip -q install datasets

from pprint import pprint

from datasets import load_dataset

sentiment_dataset = load_dataset("clarin-pl/polemo2-official")


train_list = [sent['text'] for sent in sentiment_dataset['train']]
train_labels = [sent['target'] for sent in sentiment_dataset['train']]
pprint(train_list[:3])
print(train_labels[:3])

VOCAB_SIZE = 1000
encoder = tf.keras.layers.experimental.preprocessing.TextVectorization(
    max_tokens=VOCAB_SIZE)
encoder.adapt(train_list)

"""The `.adapt` method sets the layer's vocabulary. Here are the first 20 tokens. After the padding and unknown tokens they're sorted by frequency: """

vocab = np.array(encoder.get_vocabulary())
vocab[:20]

encoded_example = encoder(train_list)[:3].numpy()
encoded_example

"""With the default settings, the process is not completely reversible. There are three main reasons for that:

1. The default value for `preprocessing.TextVectorization`'s `standardize` argument is `"lower_and_strip_punctuation"`.
2. The limited vocabulary size and lack of character-based fallback results in some unknown tokens.
"""

for n in range(3):
  print("Original: ", train_list[n])
  print("Round-trip: ", " ".join(vocab[encoded_example[n]]))
  print()

"""![A drawing of the information flow in the model](https://github.com/tensorflow/docs/blob/master/site/en/tutorials/text/images/bidirectional.png?raw=1)

Above is a diagram of the model. 

1. This model can be build as a `tf.keras.Sequential`.

2. The first layer is the `encoder`, which converts the text to a sequence of token indices.

3. After the encoder is an embedding layer. An embedding layer stores one vector per word. When called, it converts the sequences of word indices to sequences of vectors. These vectors are trainable. After training (on enough data), words with similar meanings often have similar vectors.

  This index-lookup is much more efficient than the equivalent operation of passing a one-hot encoded vector through a `tf.keras.layers.Dense` layer.

4. A recurrent neural network (RNN) processes sequence input by iterating through the elements. RNNs pass the outputs from one timestep to their input on the next timestep.

  The `tf.keras.layers.Bidirectional` wrapper can also be used with an RNN layer. This propagates the input forward and backwards through the RNN layer and then concatenates the final output. 

  * The main advantage of a bidirectional RNN is that the signal from the beginning of the input doesn't need to be processed all the way through every timestep to affect the output.  

  * The main disadvantage of a bidirectional RNN is that you can't efficiently stream predictions as words are being added to the end.

5. After the RNN has converted the sequence to a single vector the two `layers.Dense` do some final processing, and convert from this vector representation to a single logit as the classification output.

The code to implement this is below:
"""

model = tf.keras.Sequential([
    encoder,
    tf.keras.layers.Embedding(
        input_dim=len(encoder.get_vocabulary()),
        output_dim=64,
        # Use masking to handle the variable sequence lengths
        mask_zero=True),
    tf.keras.layers.LSTM(64),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(4)
])

"""Please note that Keras sequential model is used here since all the layers in the model only have single input and produce single output. In case you want to use stateful RNN layer, you might want to build your model with Keras functional API or model subclassing so that you can retrieve and reuse the RNN layer states. Please check [Keras RNN guide](https://www.tensorflow.org/guide/keras/rnn#rnn_state_reuse) for more details.

The embedding layer [uses masking](https://www.tensorflow.org/guide/keras/masking_and_padding) to handle the varying sequence-lengths. All the layers after the `Embedding` support masking:
"""

print([layer.supports_masking for layer in model.layers])

"""To confirm that this works as expected, evaluate a sentence twice. First, alone so there's no padding to mask:

Compile the Keras model to configure the training process:
"""

model.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              optimizer=tf.keras.optimizers.Adam(1e-4),
              metrics=['accuracy'])

"""## Train the model"""

val_texts = [sent['text'] for sent in sentiment_dataset['validation']]
val_labels = [sent['target'] for sent in sentiment_dataset['validation']]
test_texts = [sent['text'] for sent in sentiment_dataset['test']]
test_labels = [sent['target'] for sent in sentiment_dataset['test']]

history = model.fit(x=train_list, y=train_labels, epochs=10, validation_data=(val_texts, val_labels), validation_steps=30)

test_loss, test_acc = model.evaluate(x=test_texts, y=test_labels)

print('Test Loss:', test_loss)
print('Test Accuracy:', test_acc)

plt.figure(figsize=(16, 8))
plt.subplot(1, 2, 1)
plot_graphs(history, 'accuracy')
plt.ylim(None, 1)
plt.subplot(1, 2, 2)
plot_graphs(history, 'loss')
plt.ylim(0, None)

"""Run a prediction on a new sentence:

If the prediction is >= 0.0, it is positive else it is negative.
"""

sample_text = ('Nie pamiętam kiedy ostatnio widziałem tak dobry film, nie mogę się doczekać następnej części')
predictions = model.predict(np.array([sample_text]))
print(predictions)

"""## Zadania

1. Spróbować zmodyfikować sieć, żeby dała lepsze wyniki (można kombinować z VOCAB i wszystkimi parametrami sieci)
2. Można spróbować pobrać inny dataset z https://lepiszcze.ml/datasets/ do klasyfikacji i tak zmodyfikować sieć, żeby działał.
3. Można, pamiętając o wcześniejszym przykładzie - dodać logowanie do WanDB

"""
