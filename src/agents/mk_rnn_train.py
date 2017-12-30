""" This module contains code for maintaining the basic Mario Kart AI agent's state-decision map. """
import logging
import os

import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.autograd import Variable

from src import helper, keylog
from src.agents.train_valid_data import get_mario_train_valid_loader

logger = logging.getLogger(__name__)

# Hyper Parameters
input_size = 15
hidden_size_1 = 64
hidden_size_2 = 64
hidden_size_3 = 64
output_vec = len(keylog.Keyboard)
history = 3

num_epochs = 50
batch_size = 50

learning_rate = 1e-5


class MKRNN(nn.Module):
    def __init__(self):
        """ Neural network architecture of Mario Kart AI agent. """
        super(MKRNN, self).__init__()
        self.input_size = input_size
        self.history = history
        self.hidden_size_1 = hidden_size_1
        self.hidden_size_2 = hidden_size_2
        self.hidden_size_3 = hidden_size_3
        self.output_vec = output_vec

        self.lstm = nn.LSTM(self.input_size * self.input_size,
                            self.hidden_size_1,
                            num_layers=self.history, dropout=0.5)

        self.encoder = nn.Sequential(
            nn.Linear(self.history * self.hidden_size_1, self.hidden_size_2),
            nn.Dropout(0.5),
            nn.LeakyReLU(),
            nn.Linear(self.hidden_size_2, self.hidden_size_3),
            nn.Dropout(0.5),
            nn.LeakyReLU(),
            nn.Linear(self.hidden_size_3, self.output_vec)
        )

        if torch.cuda.is_available():
            print("cuda is available.")
            self.cuda()

    def forward(self, x):
        """ Forward pass of the neural network. Accepts a tensor of size input_size*input_size. """
        x_input = x.view(-1, self.history, self.input_size * self.input_size)
        if torch.cuda.is_available():
            x_input = x_input.cuda()
        x = Variable(x_input).float()

        out, _ = self.lstm(x)
        out = out.view(-1, self.history * self.hidden_size_1)
        encoded = self.encoder(out)
        return encoded


if __name__ == '__main__':
    """ Train neural network Mario Kart AI agent. """
    mkrnn = MKRNN()
    # define gradient descent optimizer and loss function
    optimizer = torch.optim.Adam(mkrnn.parameters(), weight_decay=0.05, lr=learning_rate)
    loss_func = nn.MSELoss()

    # load data
    train_loader, valid_loader = get_mario_train_valid_loader(batch_size, False, 123, history=history)

    # store validation losses
    validation_losses = []

    for epoch in range(num_epochs):
        for step, (x, y) in enumerate(train_loader):
            # Wrap label 'y' in variable
            y_label = y.view(-1, output_vec)
            if torch.cuda.is_available():
                y_label = y_label.cuda()
            nn_label = Variable(y_label)

            # forward pass
            forward_pass = mkrnn(x)
            loss = loss_func(forward_pass, nn_label)  # compute loss
            optimizer.zero_grad()  # zero gradients from previous step
            loss.backward()  # compute gradients
            optimizer.step()  # apply backpropagation

            # log training
            if step % 50 == 0:
                print('Epoch: ', epoch, 'Step: ', step, '| train loss: %.4f' % loss.data[0])
                valid_loss = 0
                for (valid_x, valid_y) in valid_loader:
                    valid_y_label = valid_y.view(-1, output_vec)
                    if torch.cuda.is_available():
                        valid_y_label = valid_y_label.cuda()
                    valid_nn_label = Variable(valid_y_label)

                    valid_forward_pass = mkrnn(valid_x)
                    valid_loss_eval = loss_func(valid_forward_pass, valid_nn_label)  # compute validation loss
                    valid_loss += valid_loss_eval.data[0]
                print('Epoch: ', epoch, 'Step: ', step, '| validation loss: %.4f' % valid_loss)
                validation_losses.append(valid_loss)

    # save model
    torch.save(mkrnn, os.path.join(helper.get_models_folder(), "mkrnn_{}.pkl".format(history)))

    # save validation curve data
    fig_data = [validation_losses, history, num_epochs, batch_size, learning_rate]
    helper.pickle_object(fig_data, "mkrnn_{}".format(history))

    # show validation curve
    f = plt.figure()
    plt.plot(validation_losses)
    plt.ylabel('Validation error')
    plt.xlabel('Number of iterations')
    plt.title('NN Cross Validation Error, learning rate = %s, batch size = %i, number of Epochs= %i' % (
        learning_rate, batch_size, num_epochs))
    plt.show()
