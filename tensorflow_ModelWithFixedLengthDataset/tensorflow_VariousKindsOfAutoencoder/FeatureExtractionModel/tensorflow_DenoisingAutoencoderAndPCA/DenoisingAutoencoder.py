import os
import shutil
from collections import *

import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
from tqdm import tqdm

import PCA


def model(TEST=True, Comparison_with_PCA=True, model_name="Autoencoder", corrupt_probability=0.5,
          optimizer_selection="Adam",
          learning_rate=0.001, training_epochs=100,
          batch_size=128, display_step=10, batch_norm=True):
    mnist = input_data.read_data_sets("", one_hot=False)

    if batch_norm == True:
        model_name = "batch_norm_" + model_name

    if TEST == False:
        if os.path.exists("tensorboard/{}".format(model_name)):
            shutil.rmtree("tensorboard/{}".format(model_name))

    # ksize, strides? -> [1, 2, 2, 1] = [one image, width, height, one channel]
    # pooling을 할때, 각 batch 에 대해 한 채널에 대해서 하니까, 1, 1,로 설정해준것.
    def pooling(input, type="avg", k=2, padding='VALID'):
        if type == "max":
            return tf.nn.max_pool(input, ksize=[1, k, k, 1], strides=[1, k, k, 1], padding=padding)
        else:
            return tf.nn.avg_pool(input, ksize=[1, k, k, 1], strides=[1, k, k, 1], padding=padding)

    def layer(input, weight_shape, bias_shape):
        weight_init = tf.random_normal_initializer(stddev=0.01)
        bias_init = tf.random_normal_initializer(stddev=0.01)
        if batch_norm:
            w = tf.get_variable("w", weight_shape, initializer=weight_init)
        else:
            weight_decay = tf.constant(0.00001, dtype=tf.float32)
            w = tf.get_variable("w", weight_shape, initializer=weight_init,
                                regularizer=tf.contrib.layers.l2_regularizer(scale=weight_decay))
        b = tf.get_variable("b", bias_shape, initializer=bias_init)

        if batch_norm:
            return tf.layers.batch_normalization(tf.matmul(input, w) + b, training=not TEST)
        else:
            return tf.matmul(input, w) + b

    # stride? -> [1, 2, 2, 1] = [one image, width, height, one channel]
    def conv2d(input, weight_shape='', bias_shape='', strides=[1, 1, 1, 1], padding="VALID"):
        weight_init = tf.contrib.layers.xavier_initializer(uniform=False)
        bias_init = tf.constant_initializer(value=0)
        if batch_norm:
            w = tf.get_variable("w", weight_shape, initializer=weight_init)
        else:
            weight_decay = tf.constant(0.00001, dtype=tf.float32)
            w = tf.get_variable("w", weight_shape, initializer=weight_init,
                                regularizer=tf.contrib.layers.l2_regularizer(scale=weight_decay))

        b = tf.get_variable("b", bias_shape, initializer=bias_init)
        conv_out = tf.nn.conv2d(input, w, strides=strides, padding=padding)

        if batch_norm:
            return tf.layers.batch_normalization(tf.nn.bias_add(conv_out, b), training=not TEST)
        else:
            return tf.nn.bias_add(conv_out, b)

    def conv2d_transpose(input, output_shape='', weight_shape='', bias_shape='', strides=[1, 1, 1, 1], padding="VALID"):
        weight_init = tf.contrib.layers.xavier_initializer(uniform=False)
        bias_init = tf.constant_initializer(value=0)
        if batch_norm:
            w = tf.get_variable("w", weight_shape, initializer=weight_init)
        else:
            weight_decay = tf.constant(0.00001, dtype=tf.float32)
            w = tf.get_variable("w", weight_shape, initializer=weight_init,
                                regularizer=tf.contrib.layers.l2_regularizer(scale=weight_decay))
        b = tf.get_variable("b", bias_shape, initializer=bias_init)

        conv_out = tf.nn.conv2d_transpose(input, w, output_shape=output_shape, strides=strides, padding=padding)
        if batch_norm:
            return tf.layers.batch_normalization(tf.nn.bias_add(conv_out, b), training=not TEST)
        else:
            return tf.nn.bias_add(conv_out, b)

    def inference(x):
        if model_name == "Autoencoder" or model_name == "batch_norm_Autoencoder":
            with tf.variable_scope("encoder"):
                with tf.variable_scope("fully1"):
                    fully_1 = tf.nn.relu(layer(tf.reshape(x, (-1, 784)), [784, 256], [256]))
                with tf.variable_scope("fully2"):
                    fully_2 = tf.nn.relu(layer(fully_1, [256, 128], [128]))
                with tf.variable_scope("fully3"):
                    fully_3 = tf.nn.relu(layer(fully_2, [128, 64], [64]))
                with tf.variable_scope("output"):
                    encoder_output = tf.nn.relu(layer(fully_3, [64, 2], [2]))

            with tf.variable_scope("decoder"):
                with tf.variable_scope("fully1"):
                    fully_4 = tf.nn.relu(layer(encoder_output, [2, 64], [64]))
                with tf.variable_scope("fully2"):
                    fully_5 = tf.nn.relu(layer(fully_4, [64, 128], [128]))
                with tf.variable_scope("fully3"):
                    fully_6 = tf.nn.relu(layer(fully_5, [128, 256], [256]))
                with tf.variable_scope("output"):
                    decoder_output = tf.nn.sigmoid(layer(fully_6, [256, 784], [784]))
            return encoder_output, decoder_output

        elif model_name == 'Convolution_Autoencoder' or model_name == "batch_norm_Convolution_Autoencoder":
            with tf.variable_scope("encoder"):
                with tf.variable_scope("conv_1"):
                    conv_1 = tf.nn.relu(
                        conv2d(x, weight_shape=[5, 5, 1, 32], bias_shape=[32], strides=[1, 1, 1, 1], padding="VALID"))
                    # result -> batch_size, 24, 24, 32
                with tf.variable_scope("conv_2"):
                    conv_2 = tf.nn.relu(
                        conv2d(conv_1, weight_shape=[5, 5, 32, 32], bias_shape=[32], strides=[1, 1, 1, 1],
                               padding="VALID"))
                    # result -> batch_size, 20, 20, 32
                with tf.variable_scope("conv_3"):
                    conv_3 = tf.nn.relu(
                        conv2d(conv_2, weight_shape=[5, 5, 32, 32], bias_shape=[32], strides=[1, 1, 1, 1],
                               padding="VALID"))
                    # result -> batch_size, 16, 16, 32
                with tf.variable_scope("conv_4"):
                    conv_4 = tf.nn.relu(
                        conv2d(conv_3, weight_shape=[5, 5, 32, 32], bias_shape=[32], strides=[1, 1, 1, 1],
                               padding="VALID"))
                    # result -> batch_size, 12, 12, 32
                with tf.variable_scope("conv_5"):
                    conv_5 = tf.nn.relu(
                        conv2d(conv_4, weight_shape=[5, 5, 32, 32], bias_shape=[32], strides=[1, 1, 1, 1],
                               padding="VALID"))
                    # result -> batch_size, 8, 8, 32
                with tf.variable_scope("conv_6"):
                    conv_6 = tf.nn.relu(
                        conv2d(conv_5, weight_shape=[5, 5, 32, 32], bias_shape=[32], strides=[1, 1, 1, 1],
                               padding="VALID"))
                    # result -> batch_size, 4, 4, 32
                with tf.variable_scope("output"):
                    encoder_output = tf.nn.relu(
                        conv2d(conv_6, weight_shape=[4, 4, 32, 2], bias_shape=[2], strides=[1, 1, 1, 1],
                               padding="VALID"))
                    # result -> batch_size, 1, 1, 2

            with tf.variable_scope("decoder"):
                with tf.variable_scope("trans_conv_1"):
                    conv_7 = tf.nn.relu(
                        conv2d_transpose(encoder_output, output_shape=tf.shape(conv_6), weight_shape=[4, 4, 32, 2],
                                         bias_shape=[32], strides=[1, 1, 1, 1], padding="VALID"))
                    # result -> batch_size, 4, 4, 32
                with tf.variable_scope("trans_conv_2"):
                    conv_8 = tf.nn.relu(
                        conv2d_transpose(conv_7, output_shape=tf.shape(conv_5), weight_shape=[5, 5, 32, 32],
                                         bias_shape=[32],
                                         strides=[1, 1, 1, 1], padding="VALID"))
                    # result -> batch_size, 8, 8, 32
                with tf.variable_scope("trans_conv_3"):
                    conv_9 = tf.nn.relu(
                        conv2d_transpose(conv_8, output_shape=tf.shape(conv_4), weight_shape=[5, 5, 32, 32],
                                         bias_shape=[32],
                                         strides=[1, 1, 1, 1], padding="VALID"))
                    # result -> batch_size, 12, 12, 32
                with tf.variable_scope("trans_conv_4"):
                    conv_10 = tf.nn.relu(
                        conv2d_transpose(conv_9, output_shape=tf.shape(conv_3), weight_shape=[5, 5, 32, 32],
                                         bias_shape=[32],
                                         strides=[1, 1, 1, 1], padding="VALID"))
                    # result -> batch_size, 16, 16, 32
                with tf.variable_scope("trans_conv_5"):
                    conv_11 = tf.nn.relu(
                        conv2d_transpose(conv_10, output_shape=tf.shape(conv_2), weight_shape=[5, 5, 32, 32],
                                         bias_shape=[32],
                                         strides=[1, 1, 1, 1], padding="VALID"))
                    # result -> batch_size, 20, 20, 32
                with tf.variable_scope("trans_conv_6"):
                    conv_12 = tf.nn.relu(
                        conv2d_transpose(conv_11, output_shape=tf.shape(conv_1), weight_shape=[5, 5, 32, 32],
                                         bias_shape=[32],
                                         strides=[1, 1, 1, 1], padding="VALID"))
                    # result -> batch_size, 24, 24, 32

                with tf.variable_scope("output"):
                    decoder_output = tf.nn.sigmoid(
                        conv2d_transpose(conv_12, output_shape=tf.shape(x), weight_shape=[5, 5, 1, 32],
                                         bias_shape=[1],
                                         strides=[1, 1, 1, 1], padding="VALID"))
                    # result -> batch_size, 28, 28, 1
            return encoder_output, decoder_output

    def evaluate(output, x):
        with tf.variable_scope("validation"):
            tf.summary.image('input_image', tf.reshape(x, [-1, 28, 28, 1]), max_outputs=5)
            tf.summary.image('output_image', tf.reshape(output, [-1, 28, 28, 1]), max_outputs=5)

            if model_name == 'Convolution_Autoencoder' or model_name == "batch_norm_Convolution_Autoencoder":
                l2 = tf.sqrt(tf.reduce_sum(tf.square(tf.subtract(output, x)), axis=[1, 2, 3]))
            elif model_name == "Autoencoder" or model_name == "batch_norm_Autoencoder":
                l2 = tf.sqrt(tf.reduce_sum(tf.square(tf.subtract(output, tf.reshape(x, (-1, 784)))), axis=1))

            val_loss = tf.reduce_mean(l2)
            tf.summary.scalar('val_cost', val_loss)
            return val_loss

    def loss(output, x):
        if model_name == 'Convolution_Autoencoder' or model_name == "batch_norm_Convolution_Autoencoder":
            l2 = tf.sqrt(tf.reduce_sum(tf.square(tf.subtract(output, x)), axis=[1, 2, 3]))
        elif model_name == "Autoencoder" or model_name == "batch_norm_Autoencoder":
            l2 = tf.sqrt(tf.reduce_sum(tf.square(tf.subtract(output, tf.reshape(x, (-1, 784)))), axis=1))
        train_loss = tf.reduce_mean(l2)
        return train_loss

    def training(cost, global_step):
        tf.summary.scalar("train_cost", cost)
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            if optimizer_selection == "Adam":
                optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
            elif optimizer_selection == "RMSP":
                optimizer = tf.train.RMSPropOptimizer(learning_rate=learning_rate)
            elif optimizer_selection == "SGD":
                optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)
            train_operation = optimizer.minimize(cost, global_step=global_step)
        return train_operation

    def Denoising(x, r=0.1):
        # 0인 경우 입력을 손상시키지 않고, 1인경우 입력을 손상시킨다.
        corrupt_x = tf.multiply(x, tf.cast(tf.random_uniform(shape=tf.shape(x), minval=0, maxval=2, dtype=tf.int32),
                                           tf.float32))
        Denoising_x = tf.add(tf.multiply(corrupt_x, r), tf.multiply(x, 1 - r))
        return Denoising_x

    # print(tf.get_default_graph()) #기본그래프이다.
    JG_Graph = tf.Graph()  # 내 그래프로 설정한다.- 혹시라도 나중에 여러 그래프를 사용할 경우를 대비
    with JG_Graph.as_default():  # as_default()는 JG_Graph를 기본그래프로 설정한다.
        with tf.name_scope("feed_dict"):
            x = tf.placeholder("float", [None, 28, 28, 1])
            d_x = Denoising(x, r=corrupt_probability)
        with tf.variable_scope("shared_variables", reuse=tf.AUTO_REUSE) as scope:
            with tf.name_scope("inference"):
                encoder_output, decoder_output = inference(d_x)
            # or scope.reuse_variables()
            
        # Adam optimizer의 매개변수들을 저장하고 싶지 않다면 여기에 선언해야한다.
        with tf.name_scope("saver"):
            saver = tf.train.Saver(var_list=tf.global_variables(), max_to_keep=3)
        if not TEST:
            with tf.name_scope("loss"):
                global_step = tf.Variable(0, name="global_step", trainable=False)
                cost = loss(decoder_output, x)
            with tf.name_scope("trainer"):
                train_operation = training(cost, global_step)
            with tf.name_scope("tensorboard"):
                summary_operation = tf.summary.merge_all()

        with tf.name_scope("evaluation"):
            evaluate_operation = evaluate(decoder_output, d_x)

    config = tf.ConfigProto(log_device_placement=False, allow_soft_placement=True)
    config.gpu_options.allow_growth = True
    with tf.Session(graph=JG_Graph, config=config) as sess:
        print("initializing!!!")
        sess.run(tf.global_variables_initializer())
        ckpt = tf.train.get_checkpoint_state(os.path.join('model', model_name))
        if ckpt and tf.train.checkpoint_exists(ckpt.model_checkpoint_path):
            print("Restore {} checkpoint!!!".format(os.path.basename(ckpt.model_checkpoint_path)))
            saver.restore(sess, ckpt.model_checkpoint_path)
            # shutil.rmtree("model/{}/".format(model_name))

        if not TEST:

            summary_writer = tf.summary.FileWriter(os.path.join("tensorboard", model_name), sess.graph)

            for epoch in tqdm(range(training_epochs)):
                avg_cost = 0.
                total_batch = int(mnist.train.num_examples / batch_size)
                for i in range(total_batch):
                    mbatch_x, mbatch_y = mnist.train.next_batch(batch_size)
                    feed_dict = {x: mbatch_x.reshape((-1, 28, 28, 1))}
                    _, minibatch_cost = sess.run([train_operation, cost], feed_dict=feed_dict)
                    avg_cost += (minibatch_cost / total_batch)

                print("L2 cost : {}".format(avg_cost))
                if epoch % display_step == 0:
                    val_feed_dict = {x: mnist.validation.images[:1000].reshape(
                        (-1, 28, 28, 1))}  # GPU 메모리 인해 mnist.test.images[:1000], 여기서 1000이다.
                    val_cost, summary_str = sess.run([evaluate_operation, summary_operation],
                                                     feed_dict=val_feed_dict)
                    print("Validation L2 cost : {}".format(val_cost))
                    summary_writer.add_summary(summary_str, global_step=sess.run(global_step))

                    save_model_path = os.path.join('model', model_name)
                    if not os.path.exists(save_model_path):
                        os.makedirs(save_model_path)
                    saver.save(sess, save_model_path + '/', global_step=sess.run(global_step),
                               write_meta_graph=False)

            print("Optimization Finished!")

        # batch_norm=True 일 때, 이동평균 사용
        if Comparison_with_PCA and TEST:
            # PCA , Autoencoder Visualization
            test_feed_dict = {x: mnist.test.images.reshape(-1, 28, 28,
                                                           1)}  # GPU 메모리 인해 mnist.test.images[:1000], 여기서 1000이다.
            pca_applied = PCA.PCA(n_components=2, show_reconstruction_image=False)  # 10000,2
            encoder_applied, test_cost = sess.run([encoder_output, evaluate_operation],
                                                  feed_dict=test_feed_dict)
            print("Test L2 cost : {}".format(test_cost))
            applied = OrderedDict(PCA=pca_applied, Autoencoder=encoder_applied.reshape(-1, 2))

            # PCA , Autoencoder 그리기
            fig, ax = plt.subplots(1, 2, figsize=(18, 12))
            # fig.suptitle('vs', size=20, color='r')
            for x, (key, value) in enumerate(applied.items()):
                ax[x].grid(False)
                ax[x].set_title(key, size=20, color='k')
                ax[x].set_axis_off()
                for num in range(10):
                    ax[x].scatter(
                        [value[:, 0][i] for i in range(len(mnist.test.labels)) if mnist.test.labels[i] == num], \
                        [value[:, 1][j] for j in range(len(mnist.test.labels)) if mnist.test.labels[j] == num], \
                        s=10, label=str(num), marker='o')
                ax[x].legend()

            # plt.tight_layout()
            if model_name == "Autoencoder":
                plt.savefig("PCA vs Autoencoder.png", dpi=300)
            elif model_name == "batch_norm_Autoencoder":
                plt.savefig("PCA vs batch_Autoencoder.png", dpi=300)
            elif model_name == "Convolution_Autoencoder":
                plt.savefig("PCA vs ConvAutoencoder.png", dpi=300)
            elif model_name == "batch_norm_Convolution_Autoencoder":
                plt.savefig("PCA vs batchConvAutoencoder.png", dpi=300)
            plt.show()


if __name__ == "__main__":
    # optimizers_ selection = "Adam" or "RMSP" or "SGD"
    # model_name = "Convolution_Autoencoder" or "Autoencoder"
    model(TEST=True, Comparison_with_PCA=True, model_name="Autoencoder",
          corrupt_probability=0.5,
          optimizer_selection="Adam", learning_rate=0.001, training_epochs=300, batch_size=256,
          display_step=1, batch_norm=False)
else:
    print("model imported")
