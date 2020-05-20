# API Definition

Version 0.1

Overview of the input/output requirements for VECTOR. The typical frontend
workflow will be (1) a call to the `/geometry` endpoint to get a unique `id`,
followed by (2) a call to the `/singlepoint/:id` endpoint with the desired
input parameters to compute all of the output values. Finally, (3) a call to the
`/image/:id` endpoint will return an image of the satellite geometry that was
used in the computations.

## Endpoints

- /geometry : POST

    This endpoint is for uploading files and accepts a VRML `.wrl` file.
    It will return a unique `id` to be associated with the upload.

- /geometry/sat_name : POST

    This endpoint says we want the requested satellite's geometry file that we
    already have locally, so there is no need to upload a file. This endpoint
    will return a unique `id` to be associated with the requested satellite.

    The named satellites available are:
  - `sorce`, the SORCE satellite
  - `cubesat1u`, a 1U CubeSat
  - `deployable3u`, a 3U CubeSat with solar panels

- /singlepoint/:id : POST
    Receives the JSON data from the frontend website and makes
    the call to Matlab to produce the output results. It returns
    a JSON dictionary of the calculated values. The `/geometry` endpoint
    must be called before this.

- /image/:id : GET
    Returns the image that was produced for the requested `id`.
    The `/singlepoint/:id` endpoint must be called before this.

## Inputs

objectType: string

`cylinder, sphere, plate, custom`

![Objects](https://raw.githubusercontent.com/SWxTREC/vector-code/master/docs/vector_objects.png)

diameter: float

`The diameter of the object [m], must be positive`

length: float

`The length of the object [m], must be positive`

area: float

`The area of the object [m^2], must be positive`

pitch: float

`Pitch angle of the object [deg], must be between -90 and 90`

sideslip: float

`Sideslip angle of the object [deg], must be between -180 and 180`

temperature: float

`Ambient temperature of the atmosphere [K], must be positive`

speed: float

`Speed of the object [m/s], must be positive`

composition: dictionary

```text
Number density composition of atmospheric constituents [/m3], must be positive


O: float

O2: float

N2: float

He: float

H: float
```

accommodationModel: string

`SESAM, Goodman, Fixed`

surfaceMass: float

`Surface mass of the object [amu], must be 1 or greater`

energyAccommodation: float

`Energy accommodation value for the object [-], must be between 0 and 1`

### Example Input Payload

```json
{
"objectType": "sphere",
"diameter": 1.212,
"length": 2.5,
"area": 0,
"pitch": 30,
"sideslip": 0,
"temperature": 1200.5,
"speed": 7800.45,
"composition": {"O": 1e11,
                "O2": 1e6,
                "N2": 1e6,
                "He": 1e6,
                "H": 1e4},
"accommodationModel": "SESAM",
"energyAccommodation": 0.93,
"surfaceMass": 65}
}
```

## Outputs

dragCoefficient: float

`The coefficient of drag of the object [-]`

projectedArea: float

`The projected area of the object [m2]`

forceCoefficent: float

`The force coefficient of the object [m2]`

### Example Output Payload

```json
{
"dragCoefficient": 2.7965,
"energyAccommodation": 0.3895,
"projectedArea": 1.1537,
"forceCoefficient": 3.2264
}
```
