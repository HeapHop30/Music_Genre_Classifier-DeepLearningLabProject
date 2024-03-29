''' RECURRENT NEURAL NETWORK WITH LSTM'''

import numpy as np
import matplotlib.pyplot as plt
import math
import tensorflow as tf
from tensorflow.contrib import rnn
import random

# GENRE_TO_CLASSES = {
#     "classic pop and rock": 0,
#     "classical": 1,
#     "dance and electronica": 2,
#     "folk": 3,
#     "hip-hop": 4,
#     "jazz and blues": 5,
#     "metal": 6,
#     "pop": 7,
#     "punk": 8,
#     "soul and reggae": 9
# }

GENRE_TO_CLASSES = {
	"classic pop and rock": 0,
	"dance and electronica": 1,
	"jazz and blues": 2,
	"punk": 3,
}


def manage_dataset(dataset):
	''' Function that divides the dataset into inputs and targets with the right shape,
		it also shuffles the data '''
	x = np.array([x[0] for x in dataset])
	y = np.array([[y[1] for y in dataset]])
	y = y.reshape([-1, 1])

	c = list(zip(x, y))
	random.shuffle(c)
	x_random, y_random = map(list, zip(*c))
	x_random = np.array([x for x in x_random])
	y_random = np.array([y for y in y_random])

	return x_random, y_random


''' Prepare dataset inputs and targets '''
print("---------- Loading data... ----------")
# database = trainingset = np.load("./data/dataset/trainingset_array.npy")
# dataset = validationset = np.load("./data/dataset/validationset_array.npy")
# dataset = testset = np.load("./data/dataset/testset_array.npy")
database = trainingset = np.load("./data/subset4c_np/trainingset_np.npy")
# testset = np.load("./data/subset4c_np/testset_np.npy")

train_x, train_y = manage_dataset(database)
# test_x, test_y = manage_dataset(testset)

'''Parameters'''
# hyperparameters
learning_rate = 0.001
epochs = 10
batch_size = 1
n_batches = len(database) // batch_size
print("Number of batches for each epoch:", n_batches)

# network parameters
n_samples = database.shape[0]
n_seg = train_x[0].shape[0]  # 8290
n_coef = train_x[0].shape[1]  # 12
n_classes = 4
layers_dim = np.array([256, 256])
n_layers = len(layers_dim)
fc_layer_dim = n_classes
dropout = 0.8
print("Number of segments for each song:", n_seg)

''' Variables '''
x = tf.placeholder(tf.float32, [None, n_seg, n_coef], name='x')
y = tf.placeholder(tf.int64, [None, n_classes], name='y')

keep_prob = tf.placeholder(tf.float32)


def getBatch(x, y, batch_size, iteration):
	''' Function that returns the next bach of data to be computed '''
	start_b = (iteration * batch_size) % len(x)
	end_b = ((iteration * batch_size) + batch_size) % len(x)

	if start_b < end_b:
		return x[start_b:end_b], y[start_b:end_b]
	else:
		batch_x = np.vstack((x[start_b:], x[:end_b]))
		batch_y = np.vstack((y[start_b:], y[:end_b]))

		return batch_x, batch_y


def one_hot_encoder(y):
	''' Function that applies one hot encoding to targets '''
	onehot = list()
	for value in y:
		letter = [0 for _ in range(n_classes)]
		letter[value[0]] = 1
		onehot.append(letter)
	onehot = np.array(onehot)
	return onehot


''' LSTM functions'''


def weight_variable(shape):
	''' Function that returns random weights of given shape '''
	initial = tf.truncated_normal(shape, stddev=0.1)
	return tf.Variable(initial)


def bias_variable(shape):
	''' Function that returns random biases of given shape '''
	initial = tf.constant(0.1, shape=shape)
	return tf.Variable(initial)


def create_LSTM_layers(input, rnn_shape, dropout):
	''' Function that returns recurrent layers of LSTM neurons
		having the given shape '''
	cells = [tf.nn.rnn_cell.LSTMCell(size) for size in rnn_shape]
	if (dropout != None):
		cells = [rnn.DropoutWrapper(cell, input_keep_prob=dropout, output_keep_prob=dropout) for cell in cells]

	multi_cells = tf.nn.rnn_cell.MultiRNNCell(cells)  # create a RNN cell composed sequentially of a number of RNNCells
	initial_state = multi_cells.zero_state(batch_size=batch_size, dtype=tf.float32)

	val, state = tf.nn.dynamic_rnn(multi_cells, input, initial_state=initial_state, dtype=tf.float32)
	val = tf.reshape(val, [-1, rnn_shape[-1]])
	return val


def create_fc_layer(x, layer_dim):
	''' Function that returns a feed-forward layer of activated neurons
		with the given size'''
	size_input = x.get_shape().as_list()[-1]
	W = weight_variable([size_input, layer_dim])
	b = bias_variable([layer_dim])

	layer = tf.matmul(x, W) + b

	return layer


def recurrent_neural_network(x):
	''' Function that uses create_LSTM_layers and create_fc_layer to generate
		a recurrent neural network with LSTM '''
	val = create_LSTM_layers(x, layers_dim, dropout)
	output = create_fc_layer(val, fc_layer_dim)

	output = tf.slice(output, [int(output.shape[0]) - batch_size, 0], [batch_size, n_classes])
	output_activated = tf.nn.softmax(output)

	return output_activated, output


'''Perform training'''


def plot_results(title, tot_loss, tot_acc, y_lim=True):
	plt.close()
	lim = 10 if y_lim else max(tot_loss)+1
	y_step = 0.5

	plt.suptitle(title,
				 fontsize=14, fontweight="bold")
	plt.title("learning_rate = {},   epochs = {},   batch_size = {},   n_classes = {},   dropout = {}"
			  .format(learning_rate, epochs, batch_size, n_classes, dropout),
			  fontsize=10)
	plt.xlabel("Epochs")
	plt.ylabel("Values")
	plt.plot(tot_loss, label="loss")
	plt.plot(tot_acc, label="accuracy")
	plt.xlim(0, epochs)
	plt.ylim(0, lim)
	plt.axhline(y=1, c="lightgrey", linewidth=0.7, zorder=0)
	plt.xticks(np.arange(0, epochs, 1.0))
	plt.yticks(np.arange(0, lim, y_step))
	plt.legend()
	plt.show()


def reverse_dic(ind):
	genre = list(GENRE_TO_CLASSES.keys())[list(GENRE_TO_CLASSES.values()).index(ind)]
	return genre


def class_accuracy(out, batch_y, right_out, all_out):
	for i in range(batch_size):
		out_i = np.argmax(out[i])
		target_i = np.argmax(batch_y[i])
		if out_i == target_i:
			right_out[target_i] += 1
		all_out[target_i] += 1


def model_training(restore_model=False):
	''' Function that performs the training of the neural network '''
	output, output_nonactivated = recurrent_neural_network(x)

	loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=output_nonactivated, labels=y))
	train_step = tf.train.RMSPropOptimizer(learning_rate).minimize(loss)

	correctness = tf.equal(tf.argmax(output, -1), tf.argmax(y, -1))
	accuracy = tf.reduce_mean(tf.cast(correctness, 'float'))

	# Initialize a session
	sess = tf.InteractiveSession()
	sess.run(tf.global_variables_initializer())
	saver = tf.train.Saver()

	tot_loss = []
	tot_acc = []

	if (restore_model):
		# print("---------- Restoring model... ----------")
		# saver.restore(sess, "models/lstm_model/lstm_model.ckpt")
		#
		# print("---------- Computing outputs... ----------")
		# loss = loss.eval(feed_dict={x: test_x, y: test_y})
		# acc = accuracy.eval(feed_dict={x: test_x, y: test_y})
		# print()
		# print("----- Results:\n  Loss: {:.5f}\n  Acc: {:.5f}".format(loss, acc))

		print("FINISHED!")

	else:
		for epoch in range(epochs):
			print("---------")
			print("Computing epoch {} of {}".format(epoch, epochs))
			genres_acc = []
			avg_loss = 0
			avg_acc = 0
			right_out = [0] * n_classes
			all_out = [0] * n_classes

			for i in range(n_batches):
				print("\tComputing batch {} of {}".format(i, n_batches))
				batch_x, batch_y = getBatch(train_x, train_y, batch_size, i)

				out, _, loss_value, acc = sess.run([output, train_step, loss, accuracy],
												   feed_dict={x: batch_x, y: batch_y})

				class_accuracy(out, batch_y, right_out, all_out)

				if i % 100 == 0:
					print("\tloss: ", loss_value)
					# print("\tacc: ", acc)
				avg_loss += loss_value
				avg_acc += acc

			avg_loss = avg_loss / n_batches
			avg_acc = avg_acc / n_batches
			tot_loss.append(avg_loss)
			tot_acc.append(avg_acc)
			print("----- Epoch: {}\n  AVG loss: {:.5f}\n  AVG acc: {:.5f}".format(epoch, avg_loss, avg_acc))

			for i in range(n_classes):
				genres_acc.append(right_out[i] / all_out[i] if all_out[i] != 0 else 0)
			for i in range(n_classes):
				print("   ", reverse_dic(i), ": {:.4f}".format(genres_acc[i]))
			print()

		# print("---------- Computing test outputs... ----------")
		# loss_test, acc_test = sess.run([loss, accuracy], feed_dict={x: test_x, y: test_y})
		# print("----- Test results:\n  Loss: {:.5f}\n  Acc: {:.5f}".format(loss_test, acc_test))
		# print()
		print("FINISHED!")
		print()
		print("---------- Saving model... ----------")
		save_path = saver.save(sess, "models/lstm_model2/lstm_model2.ckpt")
		print("Model saved in file: %s" % save_path)
		print()
		print("---------- Plotting results... ----------")
		plot_results("Recurrent Neural Network", tot_loss, tot_acc)
		plot_results("Recurrent Neural Network", tot_loss, tot_acc, y_lim=False)


tf.set_random_seed(0)
train_y = one_hot_encoder(train_y)
# test_y = one_hot_encoder(test_y)
model_training(restore_model=False)
