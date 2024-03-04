# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
""" Global sisl fixtures """
import os
from pathlib import Path

import numpy as np
import pytest

from sisl import Atom, Geometry, Hamiltonian, Lattice, _environ

# Here we create the necessary methods and fixtures to enabled/disable
# tests depending on whether a sisl-files directory is present.


# Modify items based on whether the env is correct or not
def pytest_collection_modifyitems(config, items):
    sisl_files_tests = _environ.get_environ_variable("SISL_FILES_TESTS")
    if sisl_files_tests.is_dir():
        if (sisl_files_tests / "sisl").is_dir():
            return
        print(f"pytest-sisl: Could not locate sisl directory in: {sisl_files_tests}")
        return

    xfail_sisl_files = pytest.mark.xfail(
        run=False,
        reason="requires env(SISL_FILES_TESTS) pointing to clone of: https://github.com/zerothi/sisl-files",
    )
    for item in items:
        # Only skip those that have the sisl_files fixture
        # GLOBAL skipping of ALL tests that don't have this fixture
        if "sisl_files" in item.fixturenames:
            item.add_marker(xfail_sisl_files)


@pytest.fixture(scope="function")
def sisl_tmp(request, tmp_path_factory):
    """sisl specific temporary file and directory creator.

        sisl_tmp(file, dir_name='sisl')
        sisl_tmp.file(file, dir_name='sisl')
        sisl_tmp.dir('sisl')

    The scope of the `sisl_tmp` fixture is at a function level to
    clean up after each function.
    """

    class FileFactory:
        def __init__(self):
            self.base = tmp_path_factory.getbasetemp()
            self.dirs = [self.base]
            self.files = []

        def dir(self, name="sisl"):
            # Make name a path
            D = Path(name.replace(os.path.sep, "-"))
            if not (self.base / D).is_dir():
                # tmp_path_factory.mktemp returns pathlib.Path
                self.dirs.append(tmp_path_factory.mktemp(str(D), numbered=False))

            return self.dirs[-1]

        def file(self, name, dir_name="sisl"):
            # self.base *is* a pathlib
            D = self.base / dir_name.replace(os.path.sep, "-")
            if D in self.dirs:
                i = self.dirs.index(D)
            else:
                self.dir(dir_name)
                i = -1
            self.files.append(self.dirs[i] / name)
            return str(self.files[-1])

        def getbase(self):
            return self.dirs[-1]

        def __call__(self, name, dir_name="sisl"):
            """Shorthand for self.file"""
            return self.file(name, dir_name)

        def teardown(self):
            while len(self.files) > 0:
                # Do each removal separately
                f = self.files.pop()
                if f.is_file():
                    try:
                        f.close()
                    except Exception:
                        pass
                    try:
                        f.unlink()
                    except Exception:
                        pass
            while len(self.dirs) > 0:
                # Do each removal separately (from back of directory)
                d = self.dirs.pop()
                if d.is_dir():
                    try:
                        d.rmdir()
                    except Exception:
                        pass

    ff = FileFactory()
    request.addfinalizer(ff.teardown)
    return ff


@pytest.fixture(scope="session")
def sisl_files():
    """Environment catcher for the large files hosted in a different repository.

    If SISL_FILES_TESTS has been defined in the environment variable the directory
    will be used for the tests with this as a fixture.

    If the environment variable is empty and a test has this fixture, it will
    be skipped.
    """
    sisl_files_tests = _environ.get_environ_variable("SISL_FILES_TESTS")
    if not sisl_files_tests.is_dir():

        def _path(*files):
            pytest.xfail(
                reason=f"Environment SISL_FILES_TESTS not pointing to a valid directory.",
                run=False,
            )

        return _path

    def _path(*files):
        p = sisl_files_tests.joinpath(*files)
        if p.exists():
            return p
        # I expect this test to fail due to the wrong environment.
        # But it isn't an actual fail since it hasn't runned...
        pytest.xfail(
            reason=f"Environment SISL_FILES_TESTS may point to a wrong path(?); file {p} not found",
            run=False,
        )

    return _path


@pytest.fixture(scope="session")
def sisl_system():
    """A preset list of geometries/Hamiltonians."""

    class System:
        pass

    d = System()

    alat = 1.42
    sq3h = 3.0**0.5 * 0.5
    C = Atom(Z=6, R=1.42)
    lattice = Lattice(
        np.array([[1.5, sq3h, 0.0], [1.5, -sq3h, 0.0], [0.0, 0.0, 10.0]], np.float64)
        * alat,
        nsc=[3, 3, 1],
    )
    d.g = Geometry(
        np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], np.float64) * alat,
        atoms=C,
        lattice=lattice,
    )

    d.R = np.array([0.1, 1.5])
    d.t = np.array([0.0, 2.7])
    d.tS = np.array([(0.0, 1.0), (2.7, 0.0)])
    d.C = Atom(Z=6, R=max(d.R))
    d.lattice = Lattice(
        np.array([[1.5, sq3h, 0.0], [1.5, -sq3h, 0.0], [0.0, 0.0, 10.0]], np.float64)
        * alat,
        nsc=[3, 3, 1],
    )
    d.gtb = Geometry(
        np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], np.float64) * alat,
        atoms=C,
        lattice=lattice,
    )

    d.ham = Hamiltonian(d.gtb)
    d.ham.construct([(0.1, 1.5), (0.1, 2.7)])
    return d


# We are ignoring stuff in sisl.viz.plotly if plotly cannot be imported
# collect - ignore seems not to fully work... I should report this upstream.
# however, the pytest_ignore_collect seems very stable and favourable
collect_ignore = ["setup.py"]
collect_ignore_glob = []

# skip paths
_skip_paths = []
try:
    import plotly
except ImportError:
    _skip_paths.append(os.path.join("sisl", "viz", "plotly"))


def _wrapped_ignore_collect(path, config):
    # ensure we only compare against final *sisl* stuff
    global _skip_paths
    parts = list(Path(path).parts)
    parts.reverse()
    sisl_parts = parts[: parts.index("sisl")]
    sisl_parts.reverse()
    sisl_path = str(Path("sisl").joinpath(*sisl_parts))

    for skip_path in _skip_paths:
        if skip_path in sisl_path:
            return True
    return False


if pytest.version_tuple >= (7, 0):

    def pytest_ignore_collect(collection_path, config):
        return _wrapped_ignore_collect(collection_path, config)

else:

    def pytest_ignore_collect(path, config):
        return _wrapped_ignore_collect(path, config)


def pytest_configure(config):
    pytest.sisl_travis_skip = pytest.mark.skipif(
        os.environ.get("SISL_TRAVIS_CI", "false").lower() == "true",
        reason="running on TRAVIS",
    )

    # Locally manage pytest.ini input
    for mark in [
        "io",
        "generic",
        "bloch",
        "hamiltonian",
        "geometry",
        "geom",
        "neighbor",
        "shape",
        "state",
        "electron",
        "phonon",
        "utils",
        "unit",
        "distribution",
        "spin",
        "self_energy",
        "help",
        "messages",
        "namedindex",
        "sparse",
        "lattice",
        "supercell",
        "sc",
        "quaternion",
        "sparse_geometry",
        "sparse_orbital",
        "ranges",
        "physics",
        "physics_feature",
        "orbital",
        "oplist",
        "grid",
        "atoms",
        "atom",
        "sgrid",
        "sdata",
        "sgeom",
        "version",
        "bz",
        "brillouinzone",
        "monkhorstpack",
        "bandstructure",
        "inv",
        "eig",
        "linalg",
        "density_matrix",
        "dynamicalmatrix",
        "energydensity_matrix",
        "siesta",
        "tbtrans",
        "dftb",
        "vasp",
        "w90",
        "wannier90",
        "gulp",
        "fdf",
        "fhiaims",
        "aims",
        "orca",
        "collection",
        "category",
        "geom_category",
        "plot",
        "slow",
        "overlap",
        "mixing",
        "typing",
        "only",
        "viz",
        "processors",
        "data",
        "plots",
        "plotters",
    ]:
        config.addinivalue_line(
            "markers", f"{mark}: mark test to run only on named environment"
        )
