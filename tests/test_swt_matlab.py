'''
Created on Mar 14, 2020

@author: Kim Kokkonen
'''
import matlab.engine
eng = matlab.engine.start_matlab()

# path on EB ec2
eng.cd('/home/ec2-user/code/vector-api/vector-code/CD_CODE')


def call_matlab(d):
    """Call the matlab main routine with the input dictionary `d`."""

    # Used for MATLAB input file parsing
    OBJ_TYPE_DICT = {'sphere': 1, 'plate': 2,
                     'cylinder': 3, 'geometry_file': 4}
    ACCOM_MODEL_DICT = {'SESAM': -1, 'Fixed': 0, 'Goodman': 2}
    # Matlab doesn't like ints... So change them to floats
    for key in d:
        if isinstance(d[key], int):
            d[key] = float(d[key])

    composition = d["composition"]
    for key in composition:
        # MATLAB wants floats...
        composition[key] = float(composition[key])

    out = eng.MAIN(OBJ_TYPE_DICT[d["objectType"]], d["diameter"], d["length"],
                   d["area"], d["pitch"], d["sideslip"], d["temperature"],
                   d["speed"], composition["o"], composition["o2"],
                   composition["n2"], composition["he"], composition["h"],
                   ACCOM_MODEL_DICT[d["accommodationModel"]],
                   d["energyAccommodation"], d["surfaceMass"], matlab.double([]), "",
                   nargout=5)

    # Make a dict for json return
    d_return = {"dragCoefficient": out[1],
                "projectedArea": out[2],
                "forceCoefficient": out[3],
                "energyAccommodation": out[4]}
    return d_return


if __name__ == '__main__':
    d = {"objectType": "sphere", "diameter": 1.212, "length": 2.01, "area": 3.4, "pitch": 35.6,
         "sideslip": 12.5, "temperature": 1200.5, "speed": 7800.45, "composition":
         {"o": 100000000000, "o2": 1000000, "n2": 1000000, "he": 1000000, "h": 10000},
         "accommodationModel": "SESAM", "energyAccommodation": 0.93, "surfaceMass": 65
         }
    print(call_matlab(d))
