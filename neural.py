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
    "adv_eye": len(cell_types) * 4,
    "eye": 4,
    "carniv": 1
}

memory_limit = 80
stimulation_memory = 30



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

def calculateStimulation(network):
    if not network.previousInputs:
        return 0.0
    while len(network.previousInputs) > stimulation_memory:
        network.previousInputs.pop(0)

    inputSum = sum(network.previousInputs)
    inputAverages = [i/len(network.previousInputs) for i in inputSum]
    #stimulation = sum(inputAverages)
    stimulation = torch.mean( torch.tensor(inputAverages) )

    return float(stimulation)



def activate(network, environment, organism, uDiff):
    def _adv_get_eye_input(cell_id, environment, organism):
        eye_input = [0] * output_lengths["eye"]

        sprite = organism.cells[cell_id]
        sprite_pos = sprite.getPos()
        if not sprite.alive:
            return eye_input

        sprite_info = sprite.cell_info

        for cell in sprite.info["view"]:
            cell_pos = cell.getPos()
            cell_info = cell.cell_info

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
    def _get_eye_input(cell_id, environment, organism):
        eye_input = [0] * 4
        # [<-x>, <+x>, <-y>, <+y>]

        sprite = organism.cells[cell_id]
        sprite_pos = sprite.getPos()
        sprite_angle = math.radians( organism.rotation() )
        if not sprite.alive:
            return eye_input

        sprite_info = sprite.cell_info

        for cell in sprite.info["view"]:
            cell_pos = cell.getPos()
            cell_info = cell.cell_info
            rotationAngle = math.radians(organism.rotation())

            angle = getAngle(sprite_pos[0], sprite_pos[1], cell_pos[0], cell_pos[1])
            angle += rotationAngle
            direction = [math.cos(angle+sprite_angle), math.sin(angle+sprite_angle)]

            if direction[0] < 0:
                eye_input[0] += 1
            else:
                eye_input[1] += 1

            if direction[1] < 0:
                eye_input[2] += 1
            else:
                eye_input[3] += 1

        return eye_input

    def _get_carn_input(cell_id, environment, organism):
        sprite = organism.cells[cell_id]
        if sprite.alive and sprite.info["in_use"]:
            return 1.0
        return 0.0
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
            elif cell_type == "carniv":
                input_val = _get_carn_input(correspondent, environment, organism)
        elif isinstance(correspondent, list):
            if correspondent[0] == "touch":
                sprite = organism.cells[correspondent[1]]
                if sprite.info["colliding"]:
                    input_val = 1.0
                else:
                    input_val = 0.0
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
        network.previousInputs.append(flat_inputs)

        if network.isRNN:
            network_output = network.forward(flat_inputs, network.lastHidden)
        else:
            network_output = network.forward(flat_inputs)

        network.lastInput = flat_inputs.clone().detach().requires_grad_(True)
        network.lastOutput = network_output.clone().detach().requires_grad_(True)

        for i, output_val in enumerate(network_output):
            correspondent = network.outputCells[i]
            if correspondent == "rotation":
                rotation_val = output_val.tolist()
                if rotation_val >= 1.0:
                    rotation_val = 1.0
                if rotation_val >= -1.0:
                    rotation_val = -1.0
                organism.movement["rotation"] = rotation_val
            elif correspondent == "speed":
                speed = output_val.tolist()
                if speed > 1.0:
                    speed = 1.0
                elif speed < -1.0:
                    speed = -1.0
                organism.movement["speed"] = speed
            elif correspondent == "x_direction":
                dir_val = output_val.tolist()
                if dir_val > 1.0:
                    dir_val = 1.0
                elif dir_val < -1.0:
                    dir_val = -1.0
                organism.movement["direction"][0] = dir_val
            elif correspondent == "y_direction":
                dir_val = output_val.tolist()
                if dir_val > 1.0:
                    dir_val = 1.0
                elif dir_val < -1.0:
                    dir_val = -1.0
                organism.movement["direction"][1] = dir_val

    curiosity = organism.dna.base_info["curiosity"]
    network.stimulation = calculateStimulation(network)

    if network.stimulation and curiosity:
        network.boredom = curiosity / network.stimulation
    else:
        network.boredom = 0.0


def train_network(organism, epochs=1):
    network = organism.brain
    if not network:
        return
    if network.lastOutput == None or network.lastInput == None:
        return

    inputData = network.lastInput.clone()
    targetData = network.lastOutput.clone()
    if organism.pain >= 0.1:
        targetData = torch.tensor( [x * -organism.pain for x in targetData] ).float()
    else:
        targetData = torch.tensor( [x * organism.dopamine for x in targetData] ).float()

    organism.dna.trainingInput.append( inputData.tolist() )
    organism.dna.trainingOutput.append( targetData.tolist() )

    while len(organism.dna.trainingInput) > memory_limit:
        organism.dna.trainingInput.pop(0)
        organism.dna.trainingOutput.pop(0)

    if network.isRNN:
        for i in range(epochs):
            loss = network.trainer.train_rnn(torch.tensor(organism.dna.trainingInput), torch.tensor(organism.dna.trainingOutput))
            network.lastLoss = loss
            #loss = network.trainer.train_epoch(inputData, targetData)
    else:
        for i in range(epochs):
            loss = network.trainer.train_epoch(torch.tensor(organism.dna.trainingInput), torch.tensor(organism.dna.trainingOutput))
            network.lastLoss = loss
    network.lastTrained = time.time()

    organism._update_brain_weights()


def setup_network(dna, learning_rate=0.02, rnn=False, hiddenSize=8):
    base_input = {
        "visual": [],
        "chemical": [],
        "movement": ["rotation", "speed", "x_direction", "y_direction"],
        "body": ["health", "energy"]
    }

    base_output = ["rotation", "speed", "x_direction", "y_direction"]

    for cell_id in dna.cells:
        cell_info = dna.cells[cell_id]

        if cell_info["type"] == "eye":
            base_input["visual"].append(cell_id)
        elif cell_info["type"] == "carniv":
            base_input["body"].append(cell_id)

    inputCells = []
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

    for cell_id in dna.cells:
        inputSize += 1
        inputCells.append(["touch", cell_id])

    hiddenList = dna.brain_structure["hidden_layers"]

    outputSize = len(base_output)

    if inputSize and hiddenList and outputSize:
        outputSize = len(base_output)

        if rnn:
            network = networks.RNNetwork(inputSize, hiddenList, outputSize, 6, optimizer=dna.brain_structure["optimizer"], learning_rate=learning_rate)
        else:
            network = networks.Network(inputSize, hiddenList, outputSize, optimizer=dna.brain_structure["optimizer"], learning_rate=learning_rate)

        network.inputCells = inputCells
        network.outputCells = base_output[:]
        network.activate = lambda env, org, uDiff: activate(network, env, org, uDiff)
        network.lastUpdated = time.time()
        network.lastTrained = time.time()
        network.lastOutput = None
        network.lastInput = None
        network.lastLoss = 0.0
        network.previousInputs = []
        network.stimulation = 0.0
        network.boredom = 0.0

        return network
