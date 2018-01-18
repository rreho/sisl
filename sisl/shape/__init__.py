"""
==========================
Shapes (:mod:`sisl.shape`)
==========================

.. module:: sisl.shape

A variety of default shapes.

All shapes inherit the `Shape` class.

All shapes in sisl allows one to perform arithmetic on them.
I.e. one may *add* two shapes to accomblish what would be equivalent
to an ``&`` operation. The resulting shape will be a ``CompositeShape`` which
implements the necessary routines to ensure correct operation.

Currently these mathematical/boolean operators are implemented:

`&`
    intersection of shapes

`|`/`+`
    union of shapes

`^`
    the disjunction union

'-'
    complementary shape

.. autosummary::
   :toctree:

   Shape - base class
   Cuboid - 3d cube
   Cube - 3d box
   Ellipsoid
   Sphere

"""
from .base import *
from .ellipsoid import *
from .prism4 import *

__all__ = [s for s in dir() if not s.startswith('_')]
