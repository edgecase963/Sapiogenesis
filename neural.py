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

    hiddenList = dna.brain_structure["hidden_layers"]

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

        for layer in network.layers():
            print(layer)

        return network




if __name__ == "__main__":
    net = networks.Network(2, [3], 1)

    print( net.layers() )
