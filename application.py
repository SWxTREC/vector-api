from tempfile import NamedTemporaryFile
import pprint
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


def call_matlab_image(fname):
    """Call the matlab image generation function with the input filename.

    Returns
    -------
    filepath : str
        Path to the created image.
    """
    # TODO: Still need to add the calls to the actual Matlab code.
    return 'test.png'


@application.route('/api/singlepoint', methods=['POST'])
def vector_matlab():
    if not request.json:
        abort(400, "No json content in the request.")

    output = call_matlab(request.json)
    return jsonify(output)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@application.route('/api/image', methods=['POST'])
def generate_image():
    file = request.files.get('file') or request.environ.get('wsgi.input')
    if not file:
        abort(411, f"file or wsgi.input argument is required\n{pprint.pformat(('REQUEST', request.environ))}")

    file_path = getattr(file, 'filename', default=None)
    if file_path and not allowed_file(file_path):
        abort(400, f"Bad file extension, only '.wrl' filetypes are allowed in '{file_path}'")

    # Save the uploaded file to a temporary file and then pass
    # that on to the matlab image generation code
    bufsize = 16384
    with NamedTemporaryFile() as f:
        data = file.read(bufsize)
        while data:
            f.write(data)
            data = file.read(bufsize)
        
        image_fname = call_matlab_image(f.name)
        return send_file(image_fname, mimetype='image/png')

    # If we made it here, there was an unknown error
    abort(400, "Unknown error handling the uploaded image")


@application.errorhandler(Exception)
def handle_error(error):
    '''General Exception Handler'''
    error_description = getattr(error, 'description', str(error))
    if error_description != str(error):
        error_description += "\n" + str(error)

    error_text = error_description + f"\n{pprint.pformat(('REQUEST', request.environ))}"

    return make_response(error_text, 500)


if __name__ == '__main__':
    application.run(debug=True)
