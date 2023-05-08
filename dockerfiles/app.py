# Testing vector code from Python
# https://www.mathworks.com/help/compiler_sdk/gs/create-a-python-application-with-matlab-code.html
# Compile on Linux:
# https://www.mathworks.com/help/compiler_sdk/python/compiler.build.pythonpackage.html
# https://adam.isi.uu.nl/methods/dockerfile/example-matlab/
import faulthandler
import sys
faulthandler.enable(file=sys.stdout, all_threads=True)
import json
import os
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


import boto3
try:
    BUCKET = boto3.resource('s3').Bucket(os.environ['S3_BUCKET'])
    logger.info("Using S3_BUCKET: %s", os.environ['S3_BUCKET'])
except KeyError:
    # Local install
    logger.warning("S3_BUCKET environment variable not set. Using local install.")
    BUCKET = None

logger.info("LD_LIBRARY_PATH: [%s]", os.environ.get("LD_LIBRARY_PATH", ""))
logger.info("PYTHONPATH: [%s]", os.environ.get("PYTHONPATH", ""))
logger.info("PATH: [%s]", os.environ.get("PATH", ""))

def vector_handler(event, context):
    # Remote testing does need to string load the event
    if BUCKET is not None:
        data = json.loads(event['body'])
    else:
        # Local testing doesn't send the event as a JSON string
        data = event['body']
    logger.info("Input JSON body: %s", data)

    # Matlab doesn't like ints... So change them to floats
    for key in data:
        if isinstance(data[key], int):
            data[key] = float(data[key])

    composition = data["composition"]
    for key in composition:
        # MATLAB wants floats
        composition[key] = float(composition[key])

    # Default empty geometry file
    geom_file = ""
    obj_id = 0
    obj_type = data['objectType']
    if obj_type == 'sphere':
        obj_id = 1
    elif obj_type == 'plate':
        obj_id = 2
    elif obj_type == 'cylinder':
        obj_id = 3
    elif obj_type == 'custom':
        # Handle the geometry file
        obj_id = 4
        if data['userId'] is None:
            return {"statusCode": 400, "body": "Need a valid userId with a custom objectType."}
        # The geometry file is stored in s3 under the userID, go and retrieve it locally
        # BUCKET/data/vector/userID.wrl
        geom_file = '/tmp/geom.wrl'
        BUCKET.download_file(f"/data/vector/{data['userId']}.wrl", geom_file)
    else:
        return {"statusCode": 400, "body": "Invalid objectType."}

    data["obj_id"] = float(obj_id)
    data["geom_file"] = geom_file
    matlab_return = run_matlab(data)
    return {"statusCode": 200, "body": matlab_return}


def run_matlab(data):
    """Runs the matlab VECTOR code"""
    logger.info("Running matlab with options: %s", data)
    logger.info("Beginning imports from v5")
    import vector_main
    logger.info("vector_main loaded")
    vector_main.initialize_runtime(['-nojvm', '-nodisplay'])
    logger.info("vector_main initialized")
    # Import the matlab module only after you have imported 
    # MATLAB Compiler SDK generated Python modules.
    from matlab import double as mdouble
    logger.info("matlab double imported")
    try:
        my_vector_main = vector_main.initialize()
    except Exception as e:
        logger.error(f'Error initializing Vector_main package\\n:{e}')
        exit(1)
    logger.info("Initialized Matlab runtime")

    # Used for MATLAB input file parsing
    ACCOM_MODEL_DICT = {'SESAM': -1, 'Fixed': 0, 'Goodman': 2}
    composition = data["composition"]
    out = my_vector_main.MAIN(data["obj_id"],
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
                              data["energyAccommodation"],
                              data["surfaceMass"], mdouble([]),
                              data["geom_file"],
                              nargout=5)

    logger.info("Matlab returned: %s", out)
    if os.path.exists("geometry.png"):
        logger.info("Uploading geometry.png to S3: %s", f"/data/vector/{data['userId']}.png")
        BUCKET.upload_file("geometry.png", f"/data/vector/{data['userId']}.png")
    # Make a dict for json return
    d_return = {"dragCoefficient": out[1],
                "projectedArea": out[2],
                "forceCoefficient": out[3],
                "energyAccommodation": out[4]}
    return d_return
