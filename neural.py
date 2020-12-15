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
    "body": 24,
    "rotate": 28,
    "dead": 32,
    "heart": 36
}
# This is used to create inputs for eye cells

output_lengths = {
    "adv_eye": len(cell_types) * 4,
    "adv_eye2": 8,
    "eye": 4,
    "carniv": 1
}

memory_limit = 280
stimulation_memory = 10



def num2perc(num, maxNum):
    return (float(num) / float(maxNum)) * 100.0

def perc2num(perc, maxNum):
    return (float(perc) / 100.0) * float(maxNum)

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

def calculateStimulation(dna):
    if not dna.previousInputs:
        return 0.0
    while len(dna.previousInputs) > stimulation_memory:
        dna.previousInputs.pop(0)
    while len(dna.previousOutputs) > stimulation_memory:
        dna.previousOutputs.pop(0)

    max_stim = len(dna.previousInputs[0])

    inputSum = sum(dna.previousInputs)
    inputAverages = [i/len(dna.previousInputs) for i in inputSum]
    stimulation = sum(inputAverages) / max_stim
    #stimulation = torch.mean( torch.tensor(inputAverages) ) / max_stim

    return float(stimulation)



def activate(network, environment, organism, uDiff):
    def _get_eye_input(cell_id, environment, organism):
        eye_input = [0] * 4
        # [<-x>, <+x>, <-y>, <+y>]

        sprite = organism.cells[cell_id]
        sprite_pos = sprite.getPos()
        rotationAngle = math.radians(organism.rotation())
        if not sprite.alive:
            return eye_input

        sprite_info = sprite.cell_info

        for cell in sprite.info["view"]:
            cell_pos = cell.getPos()
            cell_info = cell.cell_info

            angle = getAngle(sprite_pos[0], sprite_pos[1], cell_pos[0], cell_pos[1])
            angle += rotationAngle
            direction = [math.cos(angle), math.sin(angle)]

            if direction[0] < 0:
                eye_input[0] = 1.0
            else:
                eye_input[1] = 1.0

            if direction[1] < 0:
                eye_input[2] = 1.0
            else:
                eye_input[3] = 1.0

        return eye_input
    def _adv_get_eye_input(cell_id, environment, organism):
        eye_input = [0] * 8
        # [
        #   <rightHalf-topQuarter-topEighth>,
        #   <rightHalf-topQuarter-bottomEighth>,
        #   <rightHalf-bottomQuarter-topEighth>,
        #   <rightHalf-bottomQuarter-bottomEighth>,
        #   <leftHalf-bottomQuarter-bottomEighth>,
        #   <leftHalf-bottomQuarter-topEighth>,
        #   <leftHalf-topQuarter-bottomEighth>,
        #   <leftHalf-topQuarter-topEighth>,
        #]
        # Calculates how many organisms are in each quarter of the eye's vision radius (clockwise)

        sprite = organism.cells[cell_id]
        sprite_pos = sprite.getPos()
        rotationAngle = math.radians(organism.rotation())
        if not sprite.alive:
            return eye_input

        sprite_info = sprite.cell_info

        for cell in sprite.info["view"]:
            cell_pos = cell.getPos()
            cell_info = cell.cell_info

            angle = getAngle(sprite_pos[0], sprite_pos[1], cell_pos[0], cell_pos[1])
            angle -= rotationAngle
            direction = [math.cos(angle), math.sin(angle)]

            distance = calculateDistance(sprite_pos[0], sprite_pos[1], cell_pos[0], cell_pos[1])
            inputVal = ( sprite.info["sight_range"] - (distance + cell.radius) ) / sprite.info["sight_range"]
            inputVal = positive(inputVal)
            # inputVal is ranged from 0.0 to 1.0. The closer the nearest cell is (in that eighth), the higher the value

            if direction[0] >= 0.0:  # Right Half
                if direction[1] < 0.0:  # Top Right Quarter
                    if direction[0] < .707:  # Top Right Quarter - Top Eighth
                        if eye_input[0] < inputVal:
                            eye_input[0] = inputVal

                    else:  # Top Right Quarter - Bottom Eighth
                        if eye_input[1] < inputVal:
                            eye_input[1] = inputVal

                else:  # Bottom Right Quarter
                    if direction[0] >= .707:  # Bottom Right Quarter - Top Eighth
                        if eye_input[2] < inputVal:
                            eye_input[2] = inputVal

                    else:  # Bottom Right Quarter - Bottom Eighth
                        if eye_input[3] < inputVal:
                            eye_input[3] = inputVal

            else:  # Left Half
                if direction[1] >= 0.0:  # Bottom Left Quarter
                    if direction[1] >= .707:  # Bottom Left Quarter - Bottom Eighth
                        if eye_input[4] < inputVal:
                            eye_input[4] = inputVal

                    else:  # Bottom Left Quarter - Top Eighth
                        if eye_input[5] < inputVal:
                            eye_input[5] = inputVal

                else:  # Top Left Quarter
                    if direction[0] < -.707:  #Top Left Quarter - Bottom Eighth
                        if eye_input[6] < inputVal:
                            eye_input[6] = inputVal

                    else:  #Top Left Quarter - Top Eighth
                        if eye_input[7] < inputVal:
                            eye_input[7] = inputVal

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
                input_val = _adv_get_eye_input(correspondent, environment, organism)
            elif cell_type == "carniv":
                input_val = _get_carn_input(correspondent, environment, organism)
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

        if network.isRNN:
            network_output = network.forward(flat_inputs, network.lastHidden)
        else:
            network_output = network.forward(flat_inputs)

        new_modifier = random.uniform(-1, 1) * network.boredom
        network.boredom_modifier = (network.boredom_modifier + new_modifier) / 2.

        network_output = torch.tensor([ i+network.boredom_modifier for i in network_output ])

        network.lastInput = flat_inputs.clone().detach().requires_grad_(True)
        network.lastOutput = network_output.clone().detach().requires_grad_(True)

        organism.dna.previousInputs.append( flat_inputs )
        organism.dna.previousOutputs.append( network_output.tolist() )
        organism.dna.previousDopamine.append( organism.dopamine )

        for i, output_val in enumerate(network_output):
            correspondent = network.outputCells[i]
            if correspondent == "rotation":
                rotation_val = output_val.tolist()
                if rotation_val > 1.0:
                    rotation_val = 1.0
                if rotation_val < -1.0:
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
    network.stimulation = calculateStimulation(organism.dna)

    if network.stimulation and curiosity:
        inverse_val = 1.0 - network.stimulation
        network.boredom = inverse_val * curiosity
        #network.boredom = curiosity / network.stimulation
    else:
        network.boredom = 0.0


def train_network(organism, epochs=1, save_memory=False):
    network = organism.brain
    if not network:
        return
    if (network.lastOutput == None or network.lastInput == None) and save_memory:
        return
    if (not organism.dna.trainingInput or not organism.dna.trainingOutput) and not save_memory:
        return
    if len(organism.dna.previousInputs) < 4 or len(organism.dna.previousOutputs) < 4:
        return
    if len(organism.dna.previousDopamine) < 3:
        return

    pos_dopamine = list( map(positive, organism.dna.previousDopamine) )
    scaled_dopamine_list = [ i/max(pos_dopamine) for i in organism.dna.previousDopamine ]

    if save_memory:
        #inputData = network.lastInput.clone()
        #targetData = network.lastOutput.clone()

        inputData = sum( organism.dna.previousInputs[-4:-3] )
        targetData = sum( map(torch.tensor, organism.dna.previousOutputs[-4:-3]) )
        #inputData = organism.dna.previousInputs[-4]
        #targetData = organism.dna.previousOutputs[-4]

        dopamineData = scaled_dopamine_list[-3:-1]
        targetDopamine = sum(dopamineData) / len(dopamineData)

        if organism.pain >= 0.1:
            targetData = torch.tensor( [x * -organism.pain for x in targetData] ).float()
        else:
            targetData = torch.tensor( [x * targetDopamine for x in targetData] ).float()
        #    targetData = torch.tensor( [x * organism.energy_diff for x in targetData] ).float()

        organism.dna.trainingInput.append( inputData.tolist() )
        organism.dna.trainingOutput.append( targetData.tolist() )

        while len(organism.dna.trainingInput) > memory_limit:
            organism.dna.trainingInput.pop(0)
            organism.dna.trainingOutput.pop(0)

    if network.isRNN:
        for i in range(epochs):
            network.lastLoss = network.trainer.train_rnn(torch.tensor(organism.dna.trainingInput), torch.tensor(organism.dna.trainingOutput))
    else:
        for i in range(epochs):
            network.lastLoss = network.trainer.train_epoch(torch.tensor(organism.dna.trainingInput), torch.tensor(organism.dna.trainingOutput))

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
        inputSize += len(base_input["visual"]) * output_lengths["adv_eye2"]
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
        network.stimulation = 0.0
        network.boredom = 0.0
        network.boredom_modifier = 0.0
        # boredom_modifier is how much to add to the network outputs and is changed randomly and scales with boredom

        return network
