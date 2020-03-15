from tempfile import NamedTemporaryFile
import pprint
from flask import Flask, abort, jsonify, request, send_file
from flask_cors import CORS

import matlab.engine
eng = matlab.engine.start_matlab()
# path on EB ec2
# eng.cd('/opt/python/current/app/vector-code/CD_CODE')
# Testing on local ec2
eng.cd('/home/ec2-user/code/vector-api/vector-code/CD_CODE')

application = Flask(__name__)
CORS(application)
# Limit the content upload size to 16 MB
application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'wrl'}

class LoggingMiddleware(object):
    """
    See https://stackoverflow.com/a/25467602
    """
    def __init__(self, app):
        self._app = app

    def __call__(self, environ, resp):
        errorlog = environ['wsgi.errors']
        pprint.pprint(('REQUEST', environ), stream=errorlog)

        def log_response(status, headers, *args):
            pprint.pprint(('RESPONSE', status, headers), stream=errorlog)
            return resp(status, headers, *args)

        return self._app(environ, log_response)

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
    # check if the post request has the file part
    file = request.values.get('file') or request.files.get('file') or request.json.get('file')
    if not file:
        abort(400, f"No 'file' in the request.")

    # if user does not select file, browser also
    # submitted an empty part without filename
    if file.filename == '':
        abort(400, "The filename  in the request was empty.")

    if not allowed_file(file.filename):
        abort(400, "Bad file extension, only '.wrl' filetypes are allowed")

    if file and allowed_file(file.filename):
        # Save the uploaded file to a temporary file and then pass
        # that on to the matlab image generation code
        with NamedTemporaryFile() as f:
            file.save(f.name)
            image_fname = call_matlab_image(f.name)
            return send_file(image_fname, mimetype='image/png')

    # If we made it here, there was an unknown error
    abort(400, "Unknown error handling the uploaded image")


if __name__ == '__main__':
    application.wsgi_app = LoggingMiddleware(application.wsgi_app)
    application.run(debug=True)
