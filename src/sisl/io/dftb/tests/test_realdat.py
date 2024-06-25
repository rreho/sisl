# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations

""" pytest test configures """

import os.path as osp

import numpy as np
import pytest

import sisl

pytestmark = [pytest.mark.io, pytest.mark.dftb]
_dir = osp.join("sisl", "io", "dftb")


def test_molecule_overlap(sisl_files):
    si = sisl.get_sile(sisl_files(_dir, "molecule", "overreal.dat"))
    S = si.read_overlap()

    assert S.na == 3
    assert S.no == 6


def test_molecule_hamiltonian(sisl_files):
    si = sisl.get_sile(sisl_files(_dir, "molecule", "hamreal1.dat"))
    S = si.read_overlap()
    H = si.read_hamiltonian()

    assert H.na == 3
    assert H.no == 6

    assert np.allclose(H._csr._D[:, -1], S._csr._D.ravel())
