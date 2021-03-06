#!/usr/bin/env python
import torch
import random
import copy
import time



def expand_list(lst):
    result = []
    for i in range(len(lst)):
        result.append(lst[i])
        if i and i != len(lst)-1:
            result.append(lst[i])
    return result



class Trainer():
    def __init__(self, model, optimizer="adam", learning_rate="default", reduction="mean"):
        self.optimizers = {
            "adam": torch.optim.Adam,
            "adadelta": torch.optim.Adadelta,
            "adagrad": torch.optim.Adagrad,
            "adamax": torch.optim.Adamax,
            "adamw": torch.optim.AdamW,
            "asgd": torch.optim.ASGD,
            "rmsprop": torch.optim.RMSprop,
            "rprop": torch.optim.Rprop,
            "sgd": torch.optim.SGD,
        }

        if optimizer == "sgd" and learning_rate == "default":
            learning_rate = 0.1

        self.learning_rate = learning_rate
        self.loss_fn = torch.nn.MSELoss(reduction=reduction)
        self.model = model
        self.iterations = 0
        self.history = {}   # Structure: {<epoch>: <loss>}
        self.optimizer_name = optimizer

        if self.learning_rate == "default":
            self.optimizer = self.optimizers[optimizer.lower()](model.parameters())
            self.learning_rate = self.optimizer.defaults["lr"]
        else:
            self.optimizer = self.optimizers[optimizer.lower()](model.parameters(), lr=self.learning_rate)

    def set_optimizer(self, optimizer):
        self.optimizer = self.optimizers[optimizer.lower()](self.model.parameters(), lr=self.learning_rate)

    def set_learning_rate(self, learning_rate):
        self.learning_rate = learning_rate
        self.optimizer.defaults["lr"] = learning_rate

    def train_rnn(self, inputData, targetData, hiddenData):
        self.model.zero_grad()

        for i in range(targetData.size()[0]):
            result = self.model(inputData[i], hiddenData[i])

        targetData.resize_(result.shape)
        loss = self.loss_fn(result, targetData)
        loss.backward()

        # Add parameters' gradients to their values, multiplied by learning rate
        for p in self.model.parameters():
            if p.grad == None:
                continue
            p.data.add_(p.grad.data, alpha=-self.learning_rate)

        self.iterations += 1
        return loss.item()

    def train_epoch(self, inputData, target):
        result = self.model(inputData)

        loss = self.loss_fn(result, target)

        self.optimizer.zero_grad()
        loss.backward(retain_graph=True)
        self.optimizer.step()

        self.iterations += 1
        self.history[self.iterations] = loss.item()

        return loss.item()

    def train_until(self, inputData, target, iterations=None, target_loss=None):
        if target_loss:
            target_loss = float(target_loss)
        if target_loss or iterations:
            if iterations:
                if isinstance(iterations, int):
                    for i in range(iterations):
                        loss = self.train_epoch(inputData, target)
                        if target_loss:
                            if loss <= target_loss:
                                return loss
                    return loss
            elif target_loss:
                loss = target_loss+1.0
                while loss > target_loss:
                    loss = self.train_epoch(inputData, target)
                return loss

        return self.train_epoch(inputData, target)



class RNNetwork(torch.nn.Module):
    def __init__(self, inputSize, hiddenLayers, outputSize, hiddenSize, optimizer="adam", learning_rate="default"):
        super(RNNetwork, self).__init__()

        self.isRNN = True
        self.inputSize = inputSize + hiddenSize
        self.hiddenList = hiddenLayers[:]
        self.outputSize = outputSize
        self.hiddenSize = hiddenSize

        self.lastHidden = None

        self.optimizer = "adam"
        self.learning_rate = learning_rate

        self.setupLayers(self.inputSize, self.hiddenList, self.outputSize, self.hiddenSize)

    def layers(self):
        layers = [self.inputLayer]
        for layer in self.hiddenLayers:
            layers.append(layer)
        layers.append(self.outputLayer)
        layers.append(self.outputLayerH)
        return layers

    def setupLayers(self, inputSize, hiddenLayers, outputSize, hiddenSize):
        hiddenLayers = expand_list(hiddenLayers)
        self.hiddenList = hiddenLayers[:]

        self.inputLayer = torch.nn.Linear(inputSize, hiddenLayers[0])
        self.hiddenLayers = []
        self.lastHidden = torch.zeros(hiddenSize)

        hList = iter(hiddenLayers)
        for i in hList:
            try:
                newLayer = torch.nn.Linear(i, next(hList))
                self.hiddenLayers.append(newLayer)
            except StopIteration:
                break

        last_out = hiddenLayers[len(hiddenLayers)-1]

        self.outputLayer = torch.nn.Linear(last_out, outputSize)
        self.outputLayerH = torch.nn.Linear(last_out, hiddenSize)

        self.trainer = Trainer(self, optimizer=self.optimizer, learning_rate=self.learning_rate)

    def initHidden(self):
        return torch.zeros(self.hiddenSize)

    def forward(self, inputs, hidden):
        if hidden is None:
            hidden = self.initHidden()

        combined = torch.cat((inputs, hidden), 0)

        result = self.inputLayer(combined)
        result = torch.sigmoid(result)

        for layer in self.hiddenLayers:
            result = layer(result)

        self.lastHidden = self.outputLayerH(result)
        return self.outputLayer(result)



class Network(torch.nn.Module):
    def __init__(self, inputSize, hiddenLayers, outputSize, optimizer="adam", learning_rate="default"):
        # inputSize    : <int>
        # hiddenLayers : [<int>, <int>, <int>]
        # outputSize   : <int>

        super(Network, self).__init__()

        self.isRNN = False
        self.minHiddenSize = 2

        self.inputSize = inputSize
        self.hiddenList = hiddenLayers[:]
        self.outputSize = outputSize

        self.optimizer = "adam"
        self.learning_rate = learning_rate

        self.setupLayers(inputSize, hiddenLayers, outputSize)

    def copy(self):
        return copy.deepcopy(self)

    def layers(self):
        layers = [self.inputLayer]
        for layer in self.hiddenLayers:
            layers.append(layer)
        layers.append(self.outputLayer)
        return layers

    def layerSizes(self):
        layer_sizes = [self.inputSize]
        for s in self.hiddenList:
            layer_sizes.append(s)
        layer_sizes.append(self.outputSize)
        return layer_sizes

    def setupLayers(self, inputSize, hiddenLayers, outputSize):
        hiddenLayers = expand_list(hiddenLayers)
        self.hiddenList = hiddenLayers[:]

        self.inputLayer = torch.nn.Linear(inputSize, hiddenLayers[0])
        self.hiddenLayers = []

        hList = iter(hiddenLayers)
        for i in hList:
            try:
                newLayer = torch.nn.Linear(i, next(hList))
                self.hiddenLayers.append(newLayer)
            except StopIteration:
                break

        last_out = hiddenLayers[len(hiddenLayers)-1]

        self.outputLayer = torch.nn.Linear(last_out, outputSize)

        self.trainer = Trainer(self, optimizer=self.optimizer, learning_rate=self.learning_rate)

    def mutateLayers(self, magnitude):
        # `magnitude` : 0.0 - 1.0
        newHidden = []
        lengthChange = round(magnitude * 10.)

        try:
            random.randrange(-lengthChange, lengthChange)
        except ValueError:
            return

        lengthChange = random.randrange(-lengthChange, lengthChange)

        if lengthChange > 0:
            for i in range(lengthChange):
                if len(self.hiddenList)-1 >= i:
                    newLayer = self.hiddenList[i]
                else:
                    newLayer = random.randrange( min(self.hiddenList), max(self.hiddenList)+1 )
                newHidden.append(newLayer)
        else:
            newLength = len(self.hiddenList) + lengthChange
            if newLength < 1:
                newLength = 1

            for i in range(newLength):
                if len(self.hiddenList)-1 >= i:
                    newLayer = self.hiddenList[i]
                else:
                    newLayer = random.randrange( min(self.hiddenList), max(self.hiddenList)+1 )
                newHidden.append(newLayer)

        sizeChange = round(magnitude * 10.)

        for i in range(len(newHidden)):
            newAmt = random.randrange(-sizeChange, sizeChange)
            newHidden[i] = newHidden[i]-newAmt
            if newHidden[i] < self.minHiddenSize:
                newHidden[i] = self.minHiddenSize

        self.setupLayers(self.inputSize, newHidden, self.outputSize)

    def mutateBias(self, magnitude):
        # `magnitude` : 0.0 - 1.0
        with torch.no_grad():
            mRange = round(magnitude * 100.)

            try:
                random.randrange(-mRange, mRange) / 100.
            except ValueError:
                return

            for n in self.inputLayer.bias:
                diff = random.randrange(-mRange, mRange) / 100.
                n += diff

            for layer in self.hiddenLayers:
                for n in layer.bias:
                    diff = random.randrange(-mRange, mRange) / 100.
                    n += diff

            for n in self.outputLayer.bias:
                diff = random.randrange(-mRange, mRange) / 100.
                n += diff

    def forward(self, inputs):
        result = self.inputLayer(inputs)
        result = torch.sigmoid(result)

        for layer in self.hiddenLayers:
            result = layer(result)

        return self.outputLayer(result)

    def get_layers(self):
        lList = []
        lList.append(self.inputLayer)
        for layer in self.hiddenLayers:
            lList.append(layer)
        lList.append(self.outputLayer)
        return lList



if __name__ == "__main__":
    inputData = torch.tensor( [[0,0], [0,1], [1,0], [1,1]] ).float()
    targetData = torch.tensor( [[0,1,1,1]] ).float().resize_(4,1)

    net = Network(2, [3, 3], 1, learning_rate=0.001)

    print("Input Data: {}".format(inputData))

    print("\nLayers:")
    for layer in net.get_layers():
        print(layer)
    print("\n")

    print("Before mutation\n")
    input(net.layerSizes())

    net.mutateLayers(.2)

    print("\nAfter mutation\n")
    input(net.layerSizes())

    loss = net.trainer.train_until(inputData, targetData, iterations=10)

    while loss > 0.001:
        loss = net.trainer.train_until(inputData, targetData, iterations=50)
        print("Loss: {}".format(loss))

    print("\n\nAfter Training:\n{}".format(net(inputData)) )
