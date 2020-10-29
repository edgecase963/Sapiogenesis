import random
import networks
import math
import torch
import time

from pymunk import Vec2d



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



class NeuralNet(torch.nn.Module):
    def __init__(self, pre_networks, final_network, optimizer="adam", learning_rate="default"):

        super(NeuralNet, self).__init__()

        self.pre_networks = pre_networks
        self.final_network = final_network

        self.minHiddenSize = 2

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

    def setupLayers(self):
        for net in self.networks:
            layers = net.layers()

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

        self.base_input = {
            "visual": [],
            "chemical": [],
            "movement": ["rotation", "speed", "direction"],
            "body": ["health", "energy"]
        }

        self.allowed_types = ["eye"]

        self.base_output = ["rotation", "speed", "direction"]

        self.output_lengths = {
            "eye": 1
        }

        # Each network is executed and their outputs are collected and used as inputs for the final network
        # The number of output variables are randomized
        # The sum of output variables is equal to the number of input variables for the final network

    def _get_eye_input(self, cell_id, environment, organism):
        spriteList = [sprite for sprite in environment.sprites if sprite.organism != organism]

        cell = organism.cells[cell_id]
        if not cell.alive:
            return 0

        cell_info = self.dna.cells[cell_id]
        sightRange = cell_info["size"] * 6
        sprites_in_range = []

        for sprite in spriteList:
            cell_pos = cell.getPos()
            sprite_pos = sprite.getPos()
            dist = calculateDistance(cell_pos[0], cell_pos[1], sprite_pos[0], sprite_pos[1])

            if dist <= sightRange:
                sprites_in_range.append(sprite)

        return len(sprites_in_range)

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
    def _get_direction_input(self, organism):
        return organism.movement["direction"]

    def _random_hidden(self, inputSize):
        hidden_cells = []
        for i in range(random.randrange(2, 8)):
            nSize = random.randrange(2, 8)
            hidden_cells.append(nSize)
        return hidden_cells
    def _random_output(self, hidden_cells):
        return random.randrange(2, 8)

    def setup_networks(self, rebuilding=False):
        self.pre_networks = []
        for cell_id in self.dna.cells:
            cell_info = self.dna.cells[cell_id]

            if cell_info["type"] == "eye" and not cell_id in self.base_input["visual"]:
                self.base_input["visual"].append(cell_id)

        visual_input_size = 0

        if self.base_input["visual"]:
            visual_input_size = len(self.base_input["visual"]) * self.output_lengths["eye"]

            if visual_input_size:
                visual_hidden = self._random_hidden(visual_input_size)
                visual_output_size = self._random_output(visual_hidden)

                visual_network = networks.Network(visual_input_size, visual_hidden, visual_output_size)

                self.pre_networks.append(visual_network)

        if self.base_input["movement"]:
            movement_input_size = 0

            for correspondent in self.base_input["movement"]:

                if correspondent == "rotation":
                    movement_input_size += 1
                elif correspondent == "speed":
                    movement_input_size += 1
                elif correspondent == "direction":
                    movement_input_size += 1

            if movement_input_size:
                movement_hidden = self._random_hidden(movement_input_size)
                movement_output_size = self._random_output(movement_hidden)

                movement_network = networks.Network(movement_input_size, movement_hidden, movement_output_size)

                self.pre_networks.append(movement_network)

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

        if self.pre_networks:
            inputSize = sum([net.outputSize for net in self.pre_networks])
            # The sum of all output sizes for each network in `self.pre_networks`

            hidden = self._random_hidden(inputSize)
            outputSize = 0

            outputSize = len(self.base_output)

            if outputSize:
                self.final_network = networks.Network(inputSize, hidden, outputSize)

        if self.pre_networks and self.final_network:
            self.network = NeuralNet(self.pre_networks, self.final_network)

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
                            visual_inputs.append(inp)

            if self.base_input["movement"]:
                for correspondent in self.base_input["movement"]:
                    if correspondent == "rotation":
                        inp = self._get_rotation_input(organism)
                        movement_inputs.append(inp)
                    elif correspondent == "speed":
                        inp = self._get_speed_input(organism)
                        movement_inputs.append(inp)
                    elif correspondent == "direction":
                        inp = self._get_direction_input(organism)
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
                network_output = self.network.forward(all_inputs)

                for i, output_val in enumerate(network_output):
                    correspondent = self.base_output[i]
                    if correspondent == "rotation":
                        organism.movement["rotation"] = output_val.tolist()
                    elif correspondent == "speed":
                        organism.movement["speed"] = output_val.tolist()
                    elif correspondent == "direction":
                        organism.movement["direction"] = output_val.tolist()

    def mutate(self, severity=.3):
        if self.network:
            for net in self.network.networks():
                net.mutateBias(severity)
                net.mutateLayers(severity)



if __name__ == "__main__":
    net1 = networks.Network(2, [3], 4)
    net2 = networks.Network(4, [3], 1)

    brain = NeuralNet([net1, net2])
