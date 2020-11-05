import random
import networks
import math
import torch
import time

from pymunk import Vec2d



cell_types = {
    "barrier": 0,
    "carniv": 4,
    "eye": 8,
    "olfactory": 12,
    "co2C": 16,
    "push": 20,
    "pheremone": 24,
    "body": 28,
    "rotate": 32,
    "dead": 36,
    "heart": 40
}
# This is used to create inputs for eye cells

output_lengths = {
    "eye": len(cell_types) * 4
}

memory_limit = 80



def num2perc(num, maxNum):
    return ((float(num) / float(maxNum)) * 100.0)

def perc2num(perc, maxNum):
    return ((float(perc) / 100.0) * float(maxNum))

def calculateDistance(x1,y1,x2,y2):
    return math.sqrt( (x2 - x1)**2 + (y2 - y1)**2 )

def positive(x):
    if x > 0:
        return x
    return -x

def getAngle(x1, y1, x2, y2):
    myradians = math.atan2(y2-y1, x2-x1)
    return myradians

def getDirection(angle):
    direction = [math.cos(angle), math.sin(angle)]
    return direction



def activate(network, environment, organism, uDiff):
    def _get_eye_input(cell_id, environment, organism):
        eye_input = [0] * output_lengths["eye"]

        sprite = organism.cells[cell_id]
        sprite_pos = sprite.getPos()
        if not sprite.alive:
            return eye_input

        sprite_info = sprite.base_info

        for cell in sprite.info["view"]:
            cell_pos = cell.getPos()
            cell_info = cell.base_info

            dist = calculateDistance(sprite_pos[0], sprite_pos[1], cell_pos[0], cell_pos[1])
            angle = getAngle(sprite_pos[0], sprite_pos[1], cell_pos[0], cell_pos[1])
            direction = [math.cos(angle), math.sin(angle)]

            lp = cell_types[ cell_info["type"] ]

            if not eye_input[lp]:
                eye_input[lp] = 1.0
                eye_input[lp+1] = direction[0]
                eye_input[lp+2] = direction[1]
                eye_input[lp+3] = dist
            elif eye_input[lp+3] > dist:
                eye_input[lp] = 1.0
                eye_input[lp+1] = direction[0]
                eye_input[lp+2] = direction[1]
                eye_input[lp+3] = dist

        return eye_input
    def _get_health_input(organism):
        return organism.health_percent() / 100.
    def _get_energy_input(organism):
        current_energy = sum([organism.cells[id].info["energy"] for id in organism.living_cells()])
        max_energy = sum([organism.dna.cells[id]["energy_storage"] for id in organism.dna.cells])

        energy_perc = num2perc(current_energy, max_energy)

        return energy_perc / 100.
    def _get_rotation_input(organism):
        rotation = organism.rotation()
        if rotation:
            return rotation / 360.
        else:
            return 0.0
    def _get_speed_input(organism):
        return organism.movement["speed"]
    def _get_x_direction_input(organism):
        return organism.movement["direction"][0]
    def _get_y_direction_input(organism):
        return organism.movement["direction"][1]

    network.lastUpdated = time.time()
    all_inputs = []

    for correspondent in network.inputCells:
        input_val = None
        if isinstance(correspondent, int):   # Cell ID
            cell_type = organism.dna.cells[correspondent]["type"]
            if cell_type == "eye":
                input_val = _get_eye_input(correspondent, environment, organism)
        elif isinstance(correspondent, str):
            if correspondent == "health":
                input_val = _get_health_input(organism)
            elif correspondent == "energy":
                input_val = _get_energy_input(organism)
            elif correspondent == "rotation":
                input_val = _get_rotation_input(organism)
            elif correspondent == "speed":
                input_val = _get_speed_input(organism)
            elif correspondent == "x_direction":
                input_val = _get_x_direction_input(organism)
            elif correspondent == "y_direction":
                input_val = _get_y_direction_input(organism)

        try:
            len(input_val)
        except TypeError:
            input_val = torch.tensor([input_val])

        all_inputs.append( torch.tensor(input_val) )

    if all_inputs:
        flat_inputs = []
        for i in all_inputs:
            flat_inputs.extend(i)
        flat_inputs = torch.tensor(flat_inputs).float()

        network_output = network.forward(flat_inputs)
        #network_output = self.network.forward(all_inputs)

        network.lastInput = flat_inputs.clone().detach().requires_grad_(True)
        network.lastOutput = network_output.clone().detach().requires_grad_(True)

        for i, output_val in enumerate(network_output):
            correspondent = network.outputCells[i]
            if correspondent == "rotation":
                organism.movement["rotation"] = output_val.tolist()
            elif correspondent == "speed":
                organism.movement["speed"] = output_val.tolist()
            elif correspondent == "x_direction":
                organism.movement["direction"][0] = output_val.tolist()
            elif correspondent == "y_direction":
                organism.movement["direction"][1] = output_val.tolist()


def train_network(organism, epochs=1):
    def reverse_val(x):
        if x == 0.0:
            return 1.0
        return -x

    network = organism.brain
    if not network:
        return
    if network.lastOutput == None or network.lastInput == None:
        return


    inputData = network.lastInput.clone().detach()
    targetData = network.lastOutput.clone().detach()
    if organism.pain:
        targetData = torch.tensor( [reverse_val(x) for x in targetData] ).float()
    #targetData = torch.tensor( [x * (organism.dopamine) for x in targetData] ).float()

    network.trainingInput.append( inputData.tolist() )
    network.trainingOutput.append( targetData.tolist() )

    while len(network.trainingInput) > memory_limit:
        network.trainingInput.pop(0)
        network.trainingOutput.pop(0)

    for i in range(epochs):
        loss = network.trainer.train_epoch(torch.tensor(network.trainingInput), torch.tensor(network.trainingOutput))
        #loss = network.trainer.train_epoch(inputData, targetData)
        network.lastLoss = loss
    network.lastTrained = time.time()


def setup_network(dna):
    base_input = {
        "visual": [],
        "chemical": [],
        "movement": ["rotation", "speed", "x_direction", "y_direction"],
        "body": ["health", "energy"]
    }

    base_output = ["rotation", "speed", "x_direction", "y_direction"]

    inputCells = []

    for cell_id in dna.cells:
        cell_info = dna.cells[cell_id]

        if cell_info["type"] == "eye":
            base_input["visual"].append(cell_id)

    inputSize = 0
    hiddenList = []
    outputSize = 0

    if base_input["visual"]:
        inputSize += len(base_input["visual"]) * output_lengths["eye"]
        for cell_id in base_input["visual"]:
            inputCells.append(cell_id)

    if base_input["movement"]:
        inputSize += len(base_input["movement"])
        for correspondent in base_input["movement"]:
            inputCells.append(correspondent)

    if base_input["body"]:
        inputSize += len(base_input["body"])
        for correspondent in base_input["body"]:
            inputCells.append(correspondent)

    hiddenList = [random.randrange(inputSize, round(inputSize*1.2)) for i in range(random.randrange(3, 6))]

    outputSize = len(base_output)

    if inputSize and hiddenList and outputSize:
        outputSize = len(base_output)

        network = networks.Network(inputSize, hiddenList, outputSize)

        network.inputCells = inputCells
        network.outputCells = base_output[:]
        network.activate = lambda env, org, uDiff: activate(network, env, org, uDiff)
        network.lastUpdated = time.time()
        network.lastTrained = time.time()
        network.lastOutput = None
        network.lastInput = None
        network.trainingInput = []
        network.trainingOutput = []
        network.lastLoss = 0
        return network



class NeuralNet(torch.nn.Module):
    def __init__(self, pre_networks, final_network, optimizer="adam", learning_rate="default"):

        super(NeuralNet, self).__init__()

        self.pre_networks = pre_networks
        self.final_network = final_network

        self.minHiddenSize = 2

        self.inputSize = 0
        self.hiddenList = []
        self.outputSize = 0

        self.optimizer = "adam"
        self.learning_rate = "default"

    def copy(self):
        return copy.deepcopy(self)

    def networks(self):
        nets = []
        nets.extend(self.pre_networks)
        nets.append(self.final_network)
        return nets

    def layers(self):
        layers = []
        for net in self.networks():
            layers.extend(net.layers())
        return layers

    def layerSizes(self):
        layer_sizes = [self.inputSize]
        for s in self.hiddenList:
            layer_sizes.append(s)
        layer_sizes.append(self.outputSize)
        return layer_sizes

    def forward(self, inputs):
        # `inputs` should be a list containing tensors for each network
        # Structure: [<tensor>, <tensor>]

        result_list = []
        for i, network in enumerate(self.pre_networks):
            result = network(inputs[i])
            result = torch.sigmoid(result)
            result_list.append(result)

        all_inputs = torch.cat(result_list)
        output = self.final_network(all_inputs)

        return output

    def get_layers(self):
        lList = []
        lList.append(self.inputLayer)
        for layer in self.hiddenLayers:
            lList.append(layer)
        lList.append(self.outputLayer)
        return lList



class Brain():
    def __init__(self, dna):
        self.dna = dna
        self.pre_networks = []
        self.final_network = None
        self.network = None
        self.lastUpdated = time.time()
        self.lastTrained = time.time()

        self.base_input = {
            "visual": [],
            "chemical": [],
            "movement": ["rotation", "speed", "x_direction", "y_direction"],
            "body": ["health", "energy"]
        }
        # Structure: {
        #   "visual": [<cell_id>, <cell_id>],
        #   "chemical": [<cell_id>, <cell_id>],
        #   "movement": ["rotation", "speed", "direction"],
        #   "body": ["health", "energy"]
        #}
        # If an item in any of these lists is an integer, then it corresponds to a cell's ID
        # If it is a string, then it corresponds to a specific attribute of the organism

        self.lastInput = None
        self.lastOutput = None

        self.trainingInput = []
        self.trainingOutput = []

        self.allowed_types = ["eye"]

        self.base_output = ["rotation", "speed", "x_direction", "y_direction"]

        # Each network is executed and their outputs are collected and used as inputs for the final network
        # The number of output variables are randomized
        # The sum of output variables is equal to the number of input variables for the final network

    def _get_eye_input(self, cell_id, environment, organism):
        spriteList = [sprite for sprite in environment.sprites if sprite.organism != organism]

        eye_input = [0] * len(cell_types)*4

        cell = organism.cells[cell_id]
        if not cell.alive:
            return eye_input

        cell_info = self.dna.cells[cell_id]
        sightRange = cell_info["size"] * 6

        for sprite in spriteList:
            cell_pos = cell.getPos()
            sprite_pos = sprite.getPos()
            sprite_id = sprite.cell_id
            sprite_info = sprite.organism.dna.cells[sprite_id]

            dist = calculateDistance(cell_pos[0], cell_pos[1], sprite_pos[0], sprite_pos[1])
            angle = getAngle(cell_pos[0], cell_pos[1], sprite_pos[0], sprite_pos[1])
            direction = [math.cos(angle), math.sin(angle)]

            if dist <= sightRange:
                lp = cell_types[sprite_info["type"]]

                if not eye_input[lp]:
                    eye_input[lp] = 1.0
                    eye_input[lp+1] = direction[0]
                    eye_input[lp+2] = direction[1]
                    eye_input[lp+3] = dist
                elif eye_input[lp+3] > dist:
                    eye_input[lp] = 1.0
                    eye_input[lp+1] = direction[0]
                    eye_input[lp+2] = direction[1]
                    eye_input[lp+3] = dist

        return eye_input

    def _get_health_input(self, organism):
        return organism.health_percent() / 100.
    def _get_energy_input(self, organism):
        current_energy = sum([organism.cells[id].info["energy"] for id in organism.living_cells()])
        max_energy = sum([self.dna.cells[id]["energy_storage"] for id in self.dna.cells])

        energy_perc = num2perc(current_energy, max_energy)

        return energy_perc / 100.
    def _get_rotation_input(self, organism):
        rotation = organism.rotation()
        if rotation:
            return rotation / 360.
        else:
            return 0.0
    def _get_speed_input(self, organism):
        return organism.movement["speed"]
    def _get_x_direction_input(self, organism):
        return organism.movement["direction"][0]
    def _get_y_direction_input(self, organism):
        return organism.movement["direction"][1]

    def _random_hidden(self, inputSize):
        hidden_cells = []
        for i in range(random.randrange(2, 6)):
            nSize = random.randrange(inputSize, inputSize*2)
            hidden_cells.append(nSize)
        return hidden_cells
    def _random_output(self, hidden_cells):
        return random.randrange(2, 6)

    def setup_networks(self, rebuilding=False):
        self.pre_networks = []
        for cell_id in self.dna.cells:
            cell_info = self.dna.cells[cell_id]

            if cell_info["type"] == "eye" and not cell_id in self.base_input["visual"]:
                self.base_input["visual"].append(cell_id)

        inputSize = 0
        hiddenList = [random.randrange(20, 120) for i in range(random.randrange(6, 22))]
        outputSize = 0

        visual_input_size = 0

        if self.base_input["visual"]:
            visual_input_size = len(self.base_input["visual"]) * output_lengths["eye"]

            if visual_input_size:
                visual_hidden = self._random_hidden(visual_input_size)
                visual_output_size = self._random_output(visual_hidden)

                visual_network = networks.Network(visual_input_size, visual_hidden, visual_output_size)

                self.pre_networks.append(visual_network)
                inputSize += visual_input_size

        if self.base_input["movement"]:
            movement_input_size = 0

            for correspondent in self.base_input["movement"]:

                if correspondent == "rotation":
                    movement_input_size += 1
                elif correspondent == "speed":
                    movement_input_size += 1
                elif correspondent == "x_direction":
                    movement_input_size += 1
                elif correspondent == "y_direction":
                    movement_input_size += 1

            if movement_input_size:
                movement_hidden = self._random_hidden(movement_input_size)
                movement_output_size = self._random_output(movement_hidden)

                movement_network = networks.Network(movement_input_size, movement_hidden, movement_output_size)

                self.pre_networks.append(movement_network)
                inputSize += movement_input_size

        if self.base_input["body"]:
            body_input_size = 0

            for correspondent in self.base_input["body"]:
                if correspondent == "health":
                    body_input_size += 1
                elif correspondent == "energy":
                    body_input_size += 1

            if body_input_size:
                body_hidden = self._random_hidden(body_input_size)
                body_output_size = self._random_output(body_hidden)

                body_network = networks.Network(body_input_size, body_hidden, body_output_size)

                self.pre_networks.append(body_network)
                inputSize += body_input_size

        if self.pre_networks:
            final_inputSize = sum([net.outputSize for net in self.pre_networks])
            # The sum of all output sizes for each network in `self.pre_networks`

            hidden = self._random_hidden(final_inputSize)
            outputSize = 0

            hiddenList.extend(hidden)

            outputSize = len(self.base_output)

            if outputSize:
                self.final_network = networks.Network(final_inputSize, hidden, outputSize)

        if self.pre_networks and self.final_network:
            #self.network = NeuralNet(self.pre_networks, self.final_network)
            self.network = networks.Network(inputSize, hiddenList, outputSize)

        return self

    def rebuild(self):
        for cell_id in self.base_input["visual"][:]:
            if not cell_id in self.dna.cells:
                self.base_input["visual"].remove(cell_id)
            elif not self.dna.cells[cell_id]["type"] in self.allowed_types:
                self.base_input["visual"].remove(cell_id)

        self.setup_networks(rebuilding=True)

    def activate(self, environment, organism, uDiff):
        self.lastUpdated = time.time()
        if self.network:
            visual_inputs = []
            movement_inputs = []
            body_inputs = []
            all_inputs = []

            if self.base_input["visual"]:
                for cell_id in self.base_input["visual"]:
                    if cell_id in self.dna.cells and cell_id in organism.cells:
                        sprite = organism.cells[cell_id]
                        cell_info = self.dna.cells[cell_id]

                        if cell_info["type"] == "eye":
                            inp = self._get_eye_input(cell_id, environment, organism)
                            visual_inputs.extend(inp)

            if self.base_input["movement"]:
                for correspondent in self.base_input["movement"]:
                    if correspondent == "rotation":
                        inp = self._get_rotation_input(organism)
                        movement_inputs.append(inp)
                    elif correspondent == "speed":
                        inp = self._get_speed_input(organism)
                        movement_inputs.append(inp)
                    elif correspondent == "x_direction":
                        inp = self._get_x_direction_input(organism)
                        movement_inputs.append(inp)
                    elif correspondent == "y_direction":
                        inp = self._get_y_direction_input(organism)
                        movement_inputs.append(inp)

            if self.base_input["body"]:
                for correspondent in self.base_input["body"]:
                    if correspondent == "health":
                        inp = self._get_health_input(organism)
                        body_inputs.append(inp)
                    elif correspondent == "energy":
                        inp = self._get_energy_input(organism)
                        body_inputs.append(inp)

            if visual_inputs:
                all_inputs.append( torch.tensor(visual_inputs).float() )
            if movement_inputs:
                all_inputs.append( torch.tensor(movement_inputs).float() )
            if body_inputs:
                all_inputs.append( torch.tensor(body_inputs).float() )

            if all_inputs:
                flat_inputs = []
                for i in all_inputs:
                    flat_inputs.extend(i)
                flat_inputs = torch.tensor(flat_inputs)

                network_output = self.network.forward(flat_inputs)
                #network_output = self.network.forward(all_inputs)

                self.lastInput = flat_inputs.clone().detach()
                self.lastOutput = network_output.clone().detach()

                for i, output_val in enumerate(network_output):
                    correspondent = self.base_output[i]
                    if correspondent == "rotation":
                        organism.movement["rotation"] = output_val.tolist()
                    elif correspondent == "speed":
                        organism.movement["speed"] = output_val.tolist()
                    elif correspondent == "x_direction":
                        organism.movement["direction"][0] = output_val.tolist()
                    elif correspondent == "y_direction":
                        organism.movement["direction"][1] = output_val.tolist()

    def reverse_val(self, x):
        if x == 0.0:
            return 1.0
        return -x

    def train_networks(self, organism, epochs=1):
        if self.lastOutput == None or self.lastInput == None:
            return
        if not self.network:
            return

        inputData = self.lastInput.clone().detach()
        targetData = self.lastOutput.clone().detach()
        if organism.dopamine < 0:
            targetData = torch.tensor( [self.reverse_val(x) for x in targetData] ).float()

        self.trainingInput.append( inputData.tolist() )
        self.trainingOutput.append( targetData.tolist() )

        loss = self.network.trainer.train_epoch(torch.tensor(self.trainingInput), torch.tensor(self.trainingOutput))
        self.lastTrained = time.time()
        #print(loss)

    def mutate(self, severity=.3):
        if self.network:
            for net in self.network.networks():
                net.mutateBias(severity)
                net.mutateLayers(severity)



if __name__ == "__main__":
    net1 = networks.Network(2, [3], 4)
    net2 = networks.Network(4, [3], 1)
    net3 = networks.Network(6, [3], 1)

    brain = NeuralNet([net1, net2], net3)
