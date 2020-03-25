"""VECTOR API

This application sets up endpoints to work with the VECTOR code.
The current VECTOR code is written in Matlab, which we connect
to through the matlab.engine routine.

Endpoints
---------
/geometry : POST
    Receives a geometry file upload. We save this to a unique directory
    in /tmp space and return the unique identifier to the frontend for
    future requests.

/geometry/sat_name : POST
    This endpoint says we want the specific satellite's geometry file that we
    already have locally, so no upload comes along with it. We move that
    local geometry over to a unique directory
    in /tmp space and return the unique identifier to the frontend for
    future requests.

/singlepoint/<id> : POST
    Receives the json data from the frontend website and makes
    the call to Matlab to produce the output results. It returns
    a json dictionary of the calculated values.

/image/<id> : GET
    Returns the image that was produced by the geometry file uploaded. It
    must have an associated <id> which is where the saved files are stored.
"""
import shutil
import os
import pprint
import uuid
from flask import Flask, abort, jsonify, request, send_file, make_response
from flask_cors import CORS

import matlab.engine
eng = matlab.engine.start_matlab()
# path on EB ec2
eng.cd('/opt/python/current/app/vector-code/CD_CODE')
# Testing on local ec2
# eng.cd('/home/ec2-user/code/vector-api/vector-code/CD_CODE')

application = Flask(__name__)
CORS(application)
# Limit the content upload size to 16 MB
application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'wrl'}


def call_matlab(d):
    """Call the matlab main routine with the input dictionary `d`."""

    # Used for MATLAB input file parsing
    ACCOM_MODEL_DICT = {'SESAM': -1, 'Fixed': 0, 'Goodman': 2}
    # Matlab doesn't like ints... So change them to floats
    for key in d:
        if isinstance(d[key], int):
            d[key] = float(d[key])

    composition = d["composition"]
    for key in composition:
        # MATLAB wants floats...
        composition[key] = float(composition[key])

    # Default empty geometry file
    geom_file = ""
    obj_id = 0
    obj_type = d['objectType']
    if obj_type == 'sphere':
        obj_id = 1
    elif obj_type == 'plate':
        obj_id = 2
    elif obj_type == 'cylinder':
        obj_id = 3
    elif obj_type == 'custom':
        # Handle the geometry file
        obj_id = 4
        if d['user_id'] is None:
            abort(400, "Need a valid userId with a custom objectType.")
        # The geometry file is stored in the temporary directory
        geom_file = '/tmp/' + d['user_id'] + '/geom.wrl'
    else:
        abort(400, "Invalid objectType")

    out = eng.MAIN(float(obj_id), d["diameter"], d["length"],
                   d["area"], d["pitch"], d["sideslip"], d["temperature"],
                   d["speed"], composition["o"], composition["o2"],
                   composition["n2"], composition["he"], composition["h"],
                   ACCOM_MODEL_DICT[d["accommodationModel"]],
                   d["energyAccommodation"], d["surfaceMass"], matlab.double([]), geom_file,
                   nargout=5)

    # Make a dict for json return
    d_return = {"dragCoefficient": out[1],
                "projectedArea": out[2],
                "forceCoefficient": out[3],
                "energyAccommodation": out[4]}
    return d_return


@application.route('/api/singlepoint', methods=['POST'])
@application.route('/api/singlepoint/<user_id>', methods=['POST'])
def vector_matlab(user_id=None):
    if not request.json:
        abort(400, "No json content in the request.")

    input_dict = request.json
    input_dict['user_id'] = user_id
    output = call_matlab(input_dict)

    return jsonify(output)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@application.route('/api/geometry/<sat_name>', methods=['POST'])
def sat_geometry(sat_name):
    """
    This is a locally stored geometry file. Just move it over to the
    temporary directory unique to this user in /tmp space
    """
    valid_sats = {'sorce': 'sorce_simple_v0.wrl',
                  'cubesat1u': '1ucube.wrl',
                  'deployable3u': '3U_wdeployables.wrl'}

    if sat_name not in valid_sats:
        abort(400, f'Invalid satellite choice, it must be one of {valid_sats.keys()}.')

    user_id = str(uuid.uuid4())
    temp_dir = '/tmp/' + user_id + '/'
    os.makedirs(temp_dir)
    dest_file = temp_dir + 'geom.wrl'

    orig_dir = '/opt/python/current/app/vector-code/CD_CODE/'
    orig_file = orig_dir + valid_sats[sat_name]

    # Copy it over to the temp directory and call it 'geom.wrl'
    shutil.copyfile(orig_file, dest_file)

    return jsonify({'userId': user_id})


@application.route('/api/geometry', methods=['POST'])
def save_geometry():
    """Save the geometry file to a temporary directory."""

    # the file collection is lost when requests go through the API Gateway http proxy
    file = request.files.get('file') or request.environ.get('wsgi.input')
    if not file:
        abort(411, f"file or wsgi.input argument is required\n{pprint.pformat(('REQUEST', request.environ))}")

    # get the file path if possible
    # it works for local flask mode and for direct access to EB instance
    # it doesn't work for API Gateway http proxy in front of EB instance
    file_path = getattr(file, 'filename', None)
    if file_path and not allowed_file(file_path):
        abort(400, f"Bad file extension, only '.wrl' filetypes are allowed in '{file_path}'")

    # Make a directory unique to this user in /tmp space
    user_id = str(uuid.uuid4())
    temp_dir = '/tmp/' + user_id + '/'
    os.makedirs(temp_dir)
    geom_file = temp_dir + 'geom.wrl'

    # Save the uploaded file to a temporary file and then pass
    # that on to the Matlab image generation code
    bufsize = 16384
    with open(geom_file, 'wb') as f:
        # read the post data stream using a reasonable buffer size
        # the save method isn't available on the wsgi.input data stream
        data = file.read(bufsize)
        while data:
            f.write(data)
            data = file.read(bufsize)

    return jsonify({'userId': user_id})


@application.route('/api/image/<user_id>', methods=['GET'])
def get_image(user_id):
    """Get the image associated with <user_id>"""
    image_fname = '/tmp/' + user_id + '/geometry.png'
    if not os.path.exists(image_fname):
        abort(404, f"File not found for the userId: '{user_id}'")

    return send_file(image_fname, mimetype='image/png')


@application.errorhandler(Exception)
def handle_error(error):
    """General Exception Handler"""
    error_description = getattr(error, 'description', str(error))
    if error_description != str(error):
        error_description += "\n" + str(error)

    error_text = error_description + f"\n{pprint.pformat(('REQUEST', request.environ))}"

    return make_response(error_text, 500)


if __name__ == '__main__':
    application.run(debug=True)
