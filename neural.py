import random
import networks
import math
import torch
import time
import copy

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

memory_limit = 200
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
        dna.previousOutputs.pop(0)
        dna.previousDopamine.pop(0)

    max_stim = len(dna.previousInputs[0]) / 2.

    inputSum = sum(dna.previousInputs)
    inputAverages = torch.tensor([ i/len(dna.previousInputs) for i in inputSum ])
    stimulation = sum(inputAverages) / max_stim

    return float(stimulation)

def roundList(lst, fl=1):
    return [round(i, fl) for i in lst]

def rewardSorter(mem):
    return mem[2]

def remove_memory(dna, index):
    if index+1 <= len(dna.trainingInput):
        dna.trainingInput.pop(index)
        dna.trainingOutput.pop(index)
        dna.trainingReward.pop(index)

#def random_training_chunk(trainingInput, trainingOutput, chunkSize):
#    training_inputs = copy.deepcopy(trainingInput)
#    training_outputs = copy.deepcopy(trainingOutput)

#    if len(trainingInput) > chunkSize:
#        # If the length of training data is greater than the maximum index length, cut a random chunk from it
#        random_index = random.randrange( 0, len(trainingInput) - chunkSize )
#        training_inputs = training_inputs[ random_index : random_index+chunkSize ]
#        training_outputs = training_outputs[ random_index : random_index+chunkSize ]

#    return training_inputs, training_outputs



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
    def _get_olfactory_input(cell_id, environment, organism):
        smell_input = 0.0

        sprite = organism.cells[cell_id]
        sprite_pos = sprite.getPos()

        if not sprite.alive:
            return smell_input

        for cell in sprite.info["view"]:
            if cell.alive:
                continue
            cell_pos = cell.getPos()

            distance = calculateDistance(sprite_pos[0], sprite_pos[1], cell_pos[0], cell_pos[1])
            inputVal = ( sprite.info["smell_range"] - (distance + cell.radius) ) / sprite.info["smell_range"]
            inputVal = positive(inputVal)

            if inputVal > smell_input:
                smell_input = inputVal

        return smell_input

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
            elif cell_type == "olfactory":
                input_val = _get_olfactory_input(correspondent, environment, organism)
            #elif cell_type == "carniv":
            #    input_val = _get_carn_input(correspondent, environment, organism)
        elif isinstance(correspondent, str):
            if correspondent == "health":
                input_val = _get_health_input(organism)
            elif correspondent == "energy":
                input_val = _get_energy_input(organism)
            elif correspondent == "rotation":  # No longer in use
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
        flat_inputs = torch.tensor([ round(i, 1) for i in flat_inputs.tolist() ])

        if network.is_rnn:
            network_output = network.forward(flat_inputs, network.lastHidden)
        else:
            network_output = network.forward(flat_inputs)

        #new_modifier = torch.randn(network_output.shape) * network.boredom
        #network.boredom_modifier = (network.boredom_modifier + new_modifier) / 2.

        #network_output += network.boredom_modifier

        if random.random() <= network.boredom:
            network_output = torch.randn(network_output.shape)

        if positive(organism.dopamine) > 0.1 or positive(organism.pain) > 0.1:
            if len(organism.dna.previousInputs) > 2 and len(organism.dna.previousOutputs) > 2:
                organism.dna.short_term_memory.append([
                    #network.lastInput.tolist(),
                    #network.lastOutput.tolist(),
                    organism.dna.previousInputs[-3].tolist(),
                    organism.dna.previousOutputs[-3],
                    sum(organism.dna.previousDopamine[-2:]) / 2
                    #network.lastDopamine + organism.dopamine
                ])
                if network.is_rnn:
                    organism.dna.hidden_memory.append(network.lastHidden.tolist())

        while len(organism.dna.short_term_memory) > 30:
            organism.dna.short_term_memory.pop(0)
            if network.is_rnn:
                organism.dna.hidden_memory.pop(0)

        network.lastInput = flat_inputs.clone().detach().requires_grad_(True)
        network.lastOutput = network_output.clone().detach().requires_grad_(True)
        network.lastDopamine = organism.dopamine

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


def train_network(organism, epochs=1, finite_memory=True):
    network = organism.brain
    if not network:
        return
    if network.lastOutput is None or network.lastInput is None or network.lastDopamine is None:
        return

    #inputDataR = roundList(network.lastInput.tolist())

    #allActions = [mem for mem in organism.dna.short_term_memory if roundList(mem[0]) == inputDataR]
    #print(allActions)

    for i, mem in enumerate(organism.dna.short_term_memory):
        inputDataR = roundList(mem[0])
        allActions = [m for m in organism.dna.short_term_memory if roundList( m[0] ) == inputDataR]

        if allActions:
            bestMemory = sorted(allActions, key=rewardSorter)[-1]
            bestAction = bestMemory[1]
            bestReward = bestMemory[2]
            addToTraining = True

            if inputDataR in [roundList(i) for i in organism.dna.trainingInput]:
                index = organism.dna.trainingInput.index(mem[0])
                if organism.dna.trainingReward[index] > bestReward:
                    addToTraining = False
                else:
                    remove_memory(organism.dna, index)

            if addToTraining:
                organism.dna.trainingInput.append( mem[0] )
                organism.dna.trainingOutput.append( bestAction )
                organism.dna.trainingReward.append( mem[2] )
                if network.is_rnn:
                    organism.dna.trainingHidden.append(organism.dna.hidden_memory[i])

    while len(organism.dna.trainingInput) > memory_limit and finite_memory:
        lowest_reward = sorted(organism.dna.trainingReward)[0]
        lowest_index = organism.dna.trainingReward.index(lowest_reward)
        # Remove the memory with the lowest reward first to preserve the most successful memories

        remove_memory(organism.dna, lowest_index)

    if organism.dna.trainingInput and organism.dna.trainingOutput:
        if network.is_rnn:
            for i in range(epochs):
                network.lastLoss = network.trainer.train_rnn(
                    torch.tensor(organism.dna.trainingInput),
                    torch.tensor(organism.dna.trainingOutput),
                    torch.tensor(organism.dna.trainingHidden)
                )
        else:
            for i in range(epochs):
                network.lastLoss = network.trainer.train_epoch(
                    torch.tensor(organism.dna.trainingInput),
                    torch.tensor(organism.dna.trainingOutput)
                )

    network.lastTrained = time.time()

    organism._update_brain_weights()


def setup_network(dna, learning_rate=0.02, rnn=False, hiddenSize=6):
    base_input = {
        "visual": [],
        "chemical": [],
        "movement": ["speed", "x_direction", "y_direction"],
        "body": ["energy"]
    }

    base_output = ["rotation", "speed", "x_direction", "y_direction"]

    for cell_id in dna.cells:
        cell_info = dna.cells[cell_id]

        if cell_info["type"] == "eye":
            base_input["visual"].append(cell_id)
        elif cell_info["type"] == "olfactory":
            base_input["chemical"].append(cell_id)
        #elif cell_info["type"] == "carniv":
        #    base_input["body"].append(cell_id)

    inputCells = []
    inputSize = 0
    hiddenList = dna.brain_structure["hidden_layers"]
    outputSize = 0

    if base_input["visual"]:
        inputSize += len(base_input["visual"]) * output_lengths["adv_eye2"]
        for cell_id in base_input["visual"]:
            inputCells.append(cell_id)

    if base_input["chemical"]:
        inputSize += len(base_input["chemical"])
        for cell_id in base_input["chemical"]:
            inputCells.append(cell_id)

    if base_input["movement"]:
        inputSize += len(base_input["movement"])
        for correspondent in base_input["movement"]:
            inputCells.append(correspondent)

    if base_input["body"]:
        inputSize += len(base_input["body"])
        for correspondent in base_input["body"]:
            inputCells.append(correspondent)

    outputSize = len(base_output)

    if inputSize and hiddenList and outputSize:
        outputSize = len(base_output)

        if rnn:
            network = networks.RNNetwork(inputSize, hiddenList, outputSize, hiddenSize, optimizer=dna.brain_structure["optimizer"], learning_rate=learning_rate)
        else:
            network = networks.Network(inputSize, hiddenList, outputSize, optimizer=dna.brain_structure["optimizer"], learning_rate=learning_rate)

        network.inputCells = inputCells
        network.outputCells = base_output[:]
        network.activate = lambda env, org, uDiff: activate(network, env, org, uDiff)
        network.lastUpdated = time.time()
        network.lastTrained = time.time()
        network.lastOutput = None
        network.lastInput = None
        network.lastDopamine = 0.0
        network.lastLoss = 0.0
        network.stimulation = 0.0
        network.boredom = 0.0
        network.boredom_modifier = torch.zeros(outputSize)
        network.is_rnn = rnn
        # boredom_modifier is how much to add to the network outputs and is changed randomly and scales with boredom

        return network
