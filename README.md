footprint
=========

A domain-specific language that simplifies the creation of footprints for
the `pcb` printed circuit board editor. ([http://pcb.geda-project.org](http://pcb.geda-project.org))

The simplest way to use this library is to create a new Python file for
each footprint or suite of footprints you'd like to create. The first line
should be

```python
from footprint import *
```

The most concise way to create a footprint and write it to disk is by using
a `with` statement, like this example

```python
  with Footprint("KPT-1101NE") as f:
    p1 = f.add_pad(x=0, y=0, width=1.1*mm, height=1.6*mm, number=1)
    p2 = f.add_pad(base=p1, left=p1.right+6.2*mm, number=2)
```

This defines a footprint for a [surface-mount SPST tactile switch](https://www.sparkfun.com/products/8229).
The `Footprint` initializer takes a name as its argument: this determines
the name of the output file on disk.

The coordinate system uses mils (1/1000 inch), but values in millimeters can
be specified by multiplying them by the constant `mm`.

The locations of pins and pads can be specified in a number of ways; by
centers, corners or edges.

Values can be specified relative to those of other elements; when creating a
pin or pad, a `base` argument can specify a pin/pad to inherit values from.
This allows easy creation of, for example, many equally-sized holes, without
repeating the same values multiple times.

At the end of a `with` statement, the footprint is written to disk, using
the footprint's name as the filename and appending the `.fp` extension.

Convenience methods exist for creating arrays of pins/pads, either inline or
staggered. This line creates the hole pattern for a 9-pin D-sub connector:

```python
  f.add_pins(9, x=0, y=0, dx=54, dy=(112, -112), hole=30, diameter=66)
```

Though the library encourages the use of declarative syntax (e.g. defining
parameters relative to those of other elements), the implementation is
simple and each line is executed imperatively. There is no solver or
constraint system; parameters can only be specified relative to values
declared in previous statements. No connections are made between properties:
if property B is declared relative to property A, and property A is changed
in a successive statement, property B will **not** be updated. Despite these
limitations, it should be possible to create complex footprints with few
lines of code.

Not all pcb shape types and attributes are supported at the moment.
