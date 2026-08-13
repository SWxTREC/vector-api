"""Regression tests for the VECTOR drag calculations.

The expected values below were produced by this package on NumPy 1.26.4 and match
the results the deployed API returned in production, so they pin the physics
rather than merely re-recording whatever the current code happens to do.

These exist because an unpinned dependency bump to NumPy 2 silently broke the
API: NumPy 2 refuses to convert size-1 arrays to Python scalars, which took out
both `math.erf` on array arguments and the per-component assignments in
`CD_triFile_effective`. Both failures were total (every request 500'd) yet
nothing in the repo caught them. Run these before widening a dependency bound.
"""

import numpy as np
import pytest

from vector_python import vector_main

# Accommodation model flags, matching the API's ACCOM_MODEL_DICT.
ACCOMMODATION_MODELS = {"SESAM": -1, "Fixed": 0, "Goodman": 2}

# Object type ids, matching the API's objectType -> obj_id mapping. Anything
# backed by a stored or uploaded .wrl file (SORCE, CSIM, the CubeSats, custom
# uploads) is object type 4, so the synthetic geometry below covers all of them.
OBJECT_TYPES = {"sphere": 1, "plate": 2, "cylinder": 3, "geometry": 4}

# A representative request, equal to the frontend's default form values.
INPUTS = dict(
    diameter=1.212, length=2.010, area=3.4, pitch=35.6, sideslip=12.5,
    temperature=1200.5, speed=7800.45,
    n_O=1e11, n_O2=1e6, n_N2=1e6, n_He=1e6, n_H=1e4,
    energy_accommodation=0.93, surface_mass=65.0,
)

# (dragCoefficient, projectedArea, forceCoefficient, energyAccommodation)
EXPECTED = {
    "sphere-SESAM": (2.79652343527429, 1.1537059197337012, 3.2263656419499744, 0.389465959393695),
    "sphere-Fixed": (2.3087960364573785, 1.1537059197337012, 2.6636716547185837, 0.93),
    "sphere-Goodman": (2.7987892713142264, 1.1537059197337012, 3.2289797504023947, 0.3857528269530596),
    "plate-SESAM": (2.9422147880367744, 2.764542587559894, 8.13387808327617, 0.389465959393695),
    "plate-Fixed": (2.3473575092807115, 2.764542587559894, 6.489369802635046, 0.93),
    "plate-Goodman": (2.9449783175495647, 2.764542587559894, 8.141517978306258, 0.3857528269530596),
    "cylinder-SESAM": (2.7175668702152893, 2.356200571419509, 6.403132612471991, 0.389465959393695),
    "cylinder-Fixed": (2.279420975518282, 2.356200571419509, 5.370773005021791, 0.93),
    "cylinder-Goodman": (2.7196023653737873, 2.356200571419509, 6.407928647327566, 0.3857528269530596),
    "geometry-SESAM": (2.2566885252699196, 0.1759872148137963, 0.3971483282645065, 0.389465959393695),
    "geometry-Fixed": (2.127937847421584, 0.1759872148137963, 0.37448985506458965, 0.93),
    "geometry-Goodman": (2.257286662521697, 0.1759872148137963, 0.39725359277352323, 0.3857528269530596),
}

# A unit cube in the VRML subset make_surface() understands. Keywords must start
# in column 0 and no line may be blank, because the reader dispatches on line[0].
UNIT_CUBE_WRL = """#VRML V1.0 ascii
Separator {
Coordinate3 {
point [
-0.5 -0.5 -0.5, 0.5 -0.5 -0.5, 0.5 0.5 -0.5, -0.5 0.5 -0.5,
-0.5 -0.5 0.5, 0.5 -0.5 0.5, 0.5 0.5 0.5, -0.5 0.5 0.5,
]
}
IndexedFaceSet {
coordIndex [
0, 1, 2, -1, 0, 2, 3, -1,
4, 5, 6, -1, 4, 6, 7, -1,
0, 1, 5, -1, 0, 5, 4, -1,
2, 3, 7, -1, 2, 7, 6, -1,
1, 2, 6, -1, 1, 6, 5, -1,
0, 3, 7, -1, 0, 7, 4, -1,
]
}
}
"""


@pytest.fixture(scope="module")
def cube_file(tmp_path_factory):
    """A synthetic geometry so the object-type-4 path is covered without
    shipping real satellite geometry files."""
    path = tmp_path_factory.mktemp("geometry") / "cube.wrl"
    path.write_text(UNIT_CUBE_WRL)
    return str(path)


def run_model(obj_id, accommodation_model, geometry_file=""):
    """Call MAIN the way the API's lambda handler does."""
    _, CD, area, force_coefficient, alpha = vector_main.MAIN(
        float(obj_id),
        INPUTS["diameter"], INPUTS["length"], INPUTS["area"],
        INPUTS["pitch"], INPUTS["sideslip"],
        INPUTS["temperature"], INPUTS["speed"],
        INPUTS["n_O"], INPUTS["n_O2"], INPUTS["n_N2"], INPUTS["n_He"], INPUTS["n_H"],
        ACCOMMODATION_MODELS[accommodation_model],
        INPUTS["energy_accommodation"], INPUTS["surface_mass"],
        np.array([[]]).T,
        geometry_file,
    )
    return CD[0][0], area[0][0], force_coefficient[0][0], alpha[0]


@pytest.mark.parametrize("object_type", OBJECT_TYPES)
@pytest.mark.parametrize("accommodation_model", ACCOMMODATION_MODELS)
def test_matches_expected_results(object_type, accommodation_model, cube_file):
    geometry_file = cube_file if object_type == "geometry" else ""
    results = run_model(OBJECT_TYPES[object_type], accommodation_model, geometry_file)

    expected = EXPECTED[f"{object_type}-{accommodation_model}"]
    # Tolerance covers the few-ULP drift between NumPy versions while staying far
    # tighter than any change that would alter the physics.
    assert results == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize("object_type", OBJECT_TYPES)
@pytest.mark.parametrize("accommodation_model", ACCOMMODATION_MODELS)
def test_results_are_scalars(object_type, accommodation_model, cube_file):
    """NumPy 2 rejects assigning a size-1 array where a scalar is expected, so a
    result that is silently an array is the shape of bug that broke the API."""
    geometry_file = cube_file if object_type == "geometry" else ""

    for value in run_model(OBJECT_TYPES[object_type], accommodation_model, geometry_file):
        assert np.ndim(value) == 0
        assert np.isfinite(float(value))
