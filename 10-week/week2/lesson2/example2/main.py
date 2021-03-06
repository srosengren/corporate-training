import math

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import torch
from torch.autograd import Variable
from sklearn.metrics import mean_squared_error

class PyTorchLRModel(torch.nn.Module):

    def __init__(self, input_dim, output_dim):

        # call class constructor
        super(PyTorchLRModel, self).__init__()
        
        # use the nn package to create a linear layer
        self.linear = torch.nn.Linear(input_dim, output_dim)

    def forward(self, x):

        # Define the "forward" pass of this model. Think of this
        # for now as just the method that takes data input and
        # passes this through the model to create output (i.e., a prediction).
        out = self.linear(x)
        return out

def pytorch_lr_fit(x, y, learning_rate, epochs, lambda1, lambda2):
    """
    Train a (potentially multiple) linear regresison model 
    using SGD and pytorch.

    Args:
        x - feature array, a numpy array
        y - response array, a numpy array
        learning_rate - learning rate used in SGD
        epochs - number of epochs for the SGD loop
        lambda1 - the l1 regularization rate
        lambda2 - the l2 regularization rate
    Returns:
        The trained model
    """

    # define the number of features that we expect as input
    # (in input_dimension), and the number of output features
    # (in output_dimension). 
    input_dimension = x.ndim
    output_dimension = y.ndim
    
    # prep the shapes of x and y for pytorch
    if input_dimension == 1:
        x = x[:, np.newaxis]
    else:
        input_dimension = x.shape[1]
    if output_dimension == 1:
        y = y[:, np.newaxis]
    else:
        output_dimension = y.shape[1]

    # initialize the model
    model = PyTorchLRModel(input_dimension, output_dimension)
    
    # our error/loss function
    criterion = torch.nn.MSELoss()
    
    # define our SGD optimizer
    optimiser = torch.optim.SGD(model.parameters(), lr=learning_rate, weight_decay=lambda2) 

    # loop over our epochs, similar to our previous implementation
    for epoch in range(epochs):

        # increment the epoch count
        epoch +=1
        
        # define our feature and response variables
        features = Variable(torch.from_numpy(x).float(), requires_grad=True)
        response = Variable(torch.from_numpy(y).float())
        
        # clear the gradients
        optimiser.zero_grad()
        
        # calculate the predicted values
        predictions = model.forward(features)
        
        # calculate our loss
        loss = criterion(predictions, response)

        # add l1 regularization
        if lambda1 > 0.0:
            params = torch.cat([x.view(-1) for x in model.linear.parameters()])
            l1_regularization = lambda1 * torch.norm(params, 1)
            loss += l1_regularization

        # implement our gradient-based updates to our
        # parammeters (putting them "back" into the model
        # via a "backward" update)
        loss.backward()
        optimiser.step()

    return model

def main():
    
    # import the training data
    training_data = pd.read_csv('../data/training.csv')

    # pick out our features and response for training
    cols = ['bmi', 'map', 'ldl', 'hdl', 'tch', 'glu', 'ltg', 'y']
    num_features = len(cols[0:-1])

    # scale the features and response
    scaler = MinMaxScaler()
    train_data = scaler.fit_transform(training_data[cols])

    # fit our models
    model_lr = pytorch_lr_fit(np.array(train_data[:, 0:num_features]), 
            np.array(train_data[:, num_features]), 0.1, 1000, 0.0, 0.0)
    model_lasso = pytorch_lr_fit(np.array(train_data[:, 0:num_features]), 
            np.array(train_data[:, num_features]), 0.1, 1000, 0.001, 0.0)
    model_ridge = pytorch_lr_fit(np.array(train_data[:, 0:num_features]), 
            np.array(train_data[:, num_features]), 0.1, 1000, 0.0, 0.001)
    model_enet = pytorch_lr_fit(np.array(train_data[:, 0:num_features]), 
            np.array(train_data[:, num_features]), 0.1, 1000, 0.001, 0.001)
    
    # read in and pre-process our test data
    test_data = pd.read_csv('../data/test.csv')
    test_data = scaler.transform(test_data[cols])

    # test input for the model and observation tensors
    test_input = Variable(torch.from_numpy(test_data[:, 0:num_features]).float())
    
    # make our predictions by running the test input "forward"
    # through the models
    predictions_lr = model_lr(test_input)
    predictions_lasso = model_lasso(test_input)
    predictions_ridge = model_ridge(test_input)
    predictions_enet = model_enet(test_input)

    # calculate our RMSEs
    rmse_lr = math.sqrt(mean_squared_error(predictions_lr.data.numpy(), 
        test_data[:, num_features]))
    rmse_lasso = math.sqrt(mean_squared_error(predictions_lasso.data.numpy(), 
        test_data[:, num_features]))
    rmse_ridge = math.sqrt(mean_squared_error(predictions_ridge.data.numpy(), 
        test_data[:, num_features]))
    rmse_enet = math.sqrt(mean_squared_error(predictions_enet.data.numpy(), 
        test_data[:, num_features]))

    print('RMSE no regularization: %0.4f'% rmse_lr)
    print('RMSE lasso: %0.4f'% rmse_lasso)
    print('RMSE ridge: %0.4f'% rmse_ridge)
    print('RMSE elastic net: %0.4f'% rmse_enet)

if __name__ == "__main__":
    main()

