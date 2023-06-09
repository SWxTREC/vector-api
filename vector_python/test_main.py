import numpy as np

import vector_main


data = {
    "objectType": "cylinder",
    "diameter": 1.25,
    "length": 2.5,
    "area": 1.2,
    "pitch": 30,
    "sideslip": 15,
    "temperature": 800,
    "speed": 7750,
    "composition": {"o": 1e11,
                    "o2": 1e6,
                    "n2": 1e6,
                    "he": 1e6,
                    "h": 1e4},
    "accommodationModel": "SESAM",
    "energyAccomodation": 10,
    "surfaceMass": 5}

# Default empty geometry file
geom_file = ""
obj_id = 0
obj_type = data["objectType"]
if obj_type == 'sphere':
    obj_id = 1
elif obj_type == 'plate':
    obj_id = 2
elif obj_type == 'cylinder':
    obj_id = 3
elif obj_type == 'custom':
    # Handle the geometry file
    obj_id = 4

data["obj_id"] = obj_id
data["geom_file"] = geom_file

# Expected output with the above parameters
expected = {
    "dragCoefficient": 2.6623,
    "projectedArea": 2.62527,
    "forceCoefficient": 6.98926,
    "energyAccommodation": 0.4495,
}

ACCOM_MODEL_DICT = {'SESAM': -1, 'Fixed': 0, 'Goodman': 2}
composition = data["composition"]
out = vector_main.MAIN(data["obj_id"],
                            data["diameter"],
                            data["length"],
                            data["area"],
                            data["pitch"],
                            data["sideslip"],
                            data["temperature"],
                            data["speed"],
                            composition["o"],
                            composition["o2"],
                            composition["n2"],
                            composition["he"],
                            composition["h"],
                            ACCOM_MODEL_DICT[data["accommodationModel"]],
                            data["energyAccomodation"],
                            data["surfaceMass"], np.array([[]]).T,
                            data["geom_file"])

CD_status, CD, Aout, Fcoef, alpha_out = out
out_dict = {"dragCoefficient": CD[0][0],
            "projectedArea": Aout[0][0],
            "forceCoefficient": Fcoef[0][0],
            "energyAccomodation": alpha_out[0]}

print("Output:", out_dict)
