#!/usr/bin/env python
# Matt Sarnoff - October 14, 2014 - msarnoff.org
"""
generates footprint definitions for gEDA pcb


A domain-specific language that simplifies the creation of footprints for
the `pcb` printed circuit board editor. (http://pcb.geda-project.org)

The simplest way to use this library is to create a new Python file for
each footprint or suite of footprints you'd like to create. The first line
should be

  from footprint import *

The most concise way to create a footprint and write it to disk is by using
a `with` statement, like this:

  with Footprint("KPT-1101NE") as f:
    p1 = f.add_pad(x=0, y=0, width=1.1*mm, height=1.6*mm, number=1)
    p2 = f.add_pad(base=p1, left=p1.right+6.2*mm, number=2)

This defines a footprint for a surface-mount SPST tactile switch.
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

  f.add_pins(9, x=0, y=0, dx=54, dy=(112, -112), hole=30, diameter=66)

Though the library encourages the use of declarative syntax (e.g. defining
parameters relative to those of other elements), the implementation is
simple and each line is executed imperatively. There is no solver or
constraint system; parameters can only be specified relative to values
declared in previous statements. No connections are made between properties:
if property B is declared relative to property A, and property A is changed
in a successive statement, property B will *not* be updated. Despite these
limitations, it should be possible to create complex footprints with few
lines of code.

Not all pcb shape types and attributes are supported at the moment.
"""
import sys, os

__author__  = "Matt Sarnoff (msarnoff.org)"
__version__ = "1.0"


# use to specify dimensions in mm, e.g. "2.54*mm"
mm = 1.0/0.0254

def between(a, b, t=0.5):
  """Returns an intermediate value between two endpoints by performing
  linear interpolation.

  Arguments:
  a -- the first value
  b -- the second value
  t -- the interpolation point (between 0 and 1; defaults to 0.5)

  Return value:
  a + (b-a)*t

  If t is not specified, the value returned is halfway between a and b.
  If t=0, a is returned.
  If t=1, b is returned.
  """
  return a + (b-a)*t


def __mil_to_unit(mil):
  """pcb uses 1/100 mil as its native unit; this function converts mils
  to native units.

  Arguments:
  mil -- value in mils

  Return value:
  value in 1/100-mil units, rounded to the nearest integer
  """
  return round(mil * 100)



class Shape(object):
  """Abstract base class for all shapes."""

  def __init__(self):
    """Initializer. Takes no arguments."""
    self.name = ""
    self.number = ""
  
  def pcb_repr(self, tx=0, ty=0):
    """Returns a string representation of this shape in pcb format.

    Keyword arguments:
    tx -- amount this shape should be translated on the x axis
    ty -- amount this shape should be translated on the y axis

    tx and ty are required because all coordinates inside a pcb element
    are relative to its mark, and it's more convenient to start laying
    out pins and pads starting from (0,0), and then set the mark later.
    """
    return None
  
  def __str__(self):
    return self.pcb_repr()

  def __repr__(self):
    return self.pcb_repr()




class Pad(Shape):
  """A surface-mount pad."""

  # Default value, in mils, of the clearance width.
  clearance = 1

  def __init__(self, **kwargs):
    """Pad initializer.

    Keyword arguments:
    base -- (optional) if specified, the pad to inherit default values
      from
    left -- coordinate of the pad's left edge
    top -- coordinate of the pad's right edge
    width -- width of the pad on the x axis
    height -- height of the pad on the y axis
    number -- pin number
    name -- (optional) pin name
    round -- if True, the pad's ends are rounded (default is False)

    Convenience keyword arguments:
    right -- coordinate of the pad's right edge
    x -- coordinate of the pad's center on the x axis
    bottom -- coordinate of the pad's bottom edge
    y -- coordinate of the pad's center on the y axis

    Exactly two x-axis values must be specified. They could be:
    - left and width
    - x and width
    - right and width
    - left and right

    Exactly two y-axis values must be specified. They could be:
    - top and height
    - y and height
    - bottom and height
    - top and bottom

    If a base pad is specified, any values not specified in the keyword
    arguments will be inherited from it. This can eliminate unnecessary
    parameter duplication.
    """
    super(Pad, self).__init__()
    self.round = False
    inheritable_keys = ["left", "width", "top", "height", "number", "name", "round"]
    all_keys = inheritable_keys + ["right", "x", "bottom", "y"]
    base = kwargs.get("base")
    if base is not None:
      for key in inheritable_keys:
        setattr(self, key, getattr(base, key, None))
    for key in all_keys:
      value = kwargs.get(key)
      if value is not None:
        setattr(self, key, value)

  def pcb_repr(self, tx=0, ty=0):
    # pcb is silly and defines pads as line segments...
    x1, y1, x2, y2, thickness = 0, 0, 0, 0, 0
    if self.width > self.height:
      thickness = self.height
      x1 = self.left + thickness/2.
      y1 = self.y
      x2 = self.right - thickness/2.
      y2 = self.y
    else:
      thickness = self.width
      x1 = self.x
      y1 = self.top + thickness/2.
      x2 = self.x
      y2 = self.bottom - thickness/2.
    mask = thickness + self.clearance
    return "Pad[%d %d %d %d %d %d %d \"%s\" \"%s\" %#x]" % (
        __mil_to_unit(x1+tx), __mil_to_unit(y1+ty),
        __mil_to_unit(x2+tx), __mil_to_unit(y2+ty),
        __mil_to_unit(thickness), __mil_to_unit(self.clearance),
        __mil_to_unit(mask),
        self.name,
        self.number,
        0 if self.round else 0x100)

  @property
  def right(self):
    """X coordinate of the pad's right edge."""
    return self.left + self.width
  @right.setter
  def right(self, value):
    """Sets the x coordinate of the pad's right edge."""
    if self.width is not None:
      self.left = value - self.width
    else:
      self.width = value - self.left

  @property
  def x(self):
    """Coordinate of the pad's center on the x axis."""
    return between(self.left, self.right)
  @x.setter
  def x(self, value):
    """Sets the coordinate of the pad's center on the x axis."""
    self.left = value - self.width/2.

  @property
  def bottom(self):
    """Y coordinate of the pad's bottom edge."""
    return self.top + self.height
  @bottom.setter
  def bottom(self, value):
    """Sets the y coordinate of the pad's bottom edge."""
    if self.height is not None:
      self.top = value - self.height
    else:
      self.height = value - self.top

  @property
  def y(self):
    """Coordinate of the pad's center on the y axis."""
    return between(self.top, self.bottom)
  @y.setter
  def y(self, value):
    """Sets the coordinate of the pad's center on the y axis."""
    self.top = value - self.height/2.



class Pin(Shape):
  """A plated-through hole."""

  # Default value, in mils, of the clearance width.
  clearance = 2
  """Default value, in mils, of the clearance width."""
  
  # Default value, in mils, of the solder mask offset from the outer
  # edge of the annular ring.
  mask_offset = 1

  def __init__(self, **kwargs):
    """Pin initializer.

    Keyword arguments:
    base -- (optional) if specified, the pin to inherit default values 
      from
    x -- coordinate of the hole's center on the x axis
    y -- coordinate of the hole's center on the y axis
    hole -- diameter of the drill hole
    diameter -- outer diameter of the copper annulus
    number -- pin number
    name -- (optional) pin name
    round -- if False, the surrounding copper is square
      (default is True)

    If a base pin is specified, any values not specified in the keyword
    arguments will be inherited from it. This can eliminate unnecessary
    parameter duplication.
    """
    super(Pin, self).__init__()
    self.round = True
    keys = ["x", "y", "hole", "diameter", "number", "name", "round"]
    base = kwargs.get("base")
    if base is not None:
      for key in keys:
        setattr(self, key, getattr(base, key, None))
    for key in keys:
      value = kwargs.get(key)
      if value is not None:
        setattr(self, key, value)

  def pcb_repr(self, tx=0, ty=0):
    return "Pin[%d %d %d %d %d %d \"%s\" \"%s\" %#x]" % (
        __mil_to_unit(self.x+tx), __mil_to_unit(self.y+ty),
        __mil_to_unit(self.diameter), __mil_to_unit(self.clearance),
        __mil_to_unit(self.diameter+self.mask_offset), __mil_to_unit(self.hole),
        __self.name, self.number,
        0x1 | (0 if self.round else 0x100))

  @property
  def left(self):
    """X coordinate of the copper annulus' outer left edge."""
    return self.x - self.diameter/2.
  @left.setter
  def left(self, value):
    """Sets the x coordinate of the copper annulus' outer left edge."""
    self.x = value + self.diameter/2.

  @property
  def right(self):
    """X coordinate of the copper annulus' outer right edge."""
    return self.x + self.diameter/2.
  @right.setter
  def right(self, value):
    """Sets the x coordinate of the copper annulus' outer right edge."""
    self.x = value - self.diameter/2.

  @property
  def top(self):
    """Y coordinate of the copper annulus' outer top edge."""
    return self.y - self.diameter/2.
  @top.setter
  def top(self, value):
    """Sets the y coordinate of the copper annulus' outer top edge."""
    self.y = value + self.diameter/2.

  @property
  def bottom(self):
    """Y coordinate of the copper annulus' outer bottom edge."""
    return self.y + self.diameter/2.
  @bottom.setter
  def bottom(self, value):
    """Sets the y coordinate of the copper annulus' outer bottom edge."""
    self.y = value - self.diameter/2.



class SilkLine(Shape):
  """A line on the silkscreen layer."""

  default_thickness = 10

  def __init__(self, x1, y1, x2, y2, **kwargs):
    """Line initializer.

    Arguments:
    x1 -- x coordinate of the first endpoint
    y1 -- y coordinate of the first endpoint
    x2 -- x coordinate of the second endpoint
    y2 -- y coordinate of the second endpoint
    thickness -- (optional) line thickness
      SilkLine.default_thickness is used if unspecified
    """
    self.x1 = x1
    self.y1 = y1
    self.x2 = x2
    self.y2 = y2
    self.thickness = kwargs.get("thickness", self.default_thickness)

  def pcb_repr(self, tx=0, ty=0):
    return "ElementLine[%d %d %d %d %d]" % (
        __mil_to_unit(self.x1+tx), __mil_to_unit(self.y1+ty),
        __mil_to_unit(self.x2+tx), __mil_to_unit(self.y2+ty),
        __mil_to_unit(self.thickness))



class SilkPolyline(Shape):
  """A series of connected line segments on the silkscreen layer."""

  def __init__(self, *points, **kwargs):
    """Polyline initializer.

    Arguments:
    two or more 2-element (x, y) tuples

    Keyword arguments:
    thickness -- (optional) line thickness
      SilkLine.default_thickness is used if unspecified
    closed -- if True, an additional segment connects the first and last
      points
    """
    thickness = kwargs.get("thickness", SilkLine.default_thickness)
    self.segments = []
    last_point = None
    for x, y in points:
      if last_point is not None:
        self.segments.append(SilkLine(
          last_point[0], last_point[1],
          x, y,
          thickness=thickness))
      last_point = (x, y)
    if kwargs.get("closed") is True:
      self.segments.append(SilkLine(
        last_point[0], last_point[1],
        self.segments[0].x1, self.segments[0].y1,
        thickness=thickness))

  def pcb_repr(self, tx, ty):
    return "\n".join(s.pcb_repr(tx, ty) for s in self.segments)



class SilkArc(Shape):
  """An arc on the silkscreen layer."""

  def __init__(self, x, y, **kwargs):
    """Arc initializer.

    Arguments:
    x -- x coordinate of the arc center
    y -- y coordinate of the arc center

    Keyword arguments:
    x_radius -- arc radius on the x axis
    y_radius -- arc radius on the y axis
    start_angle -- angle start in degrees counterclockwise from
      negative x
    delta_angle -- arc sweep; positive values rotate counterclockwise
    thickness -- (optional) line thickness
      SilkLine.default_thickness is used if unspecified

    Convenience keyword arguments:
    radius -- specifies the arc radius on the x and y axes
    diameter -- specifies the arc diameter on the x and y axes
    """
    self.x = x
    self.y = y
    self.x_radius = kwargs.get("x_radius")
    self.y_radius = kwargs.get("y_radius")
    self.start_angle = kwargs.get("start_angle", 0)
    self.delta_angle = kwargs.get("delta_angle", 360)
    self.thickness = kwargs.get("thickness", SilkLine.default_thickness)
    radius = kwargs.get("radius")
    if radius is not None:
      self.radius = radius
    diameter = kwargs.get("diameter")
    if diameter is not None:
      self.diameter = diameter

  @property
  def radius(self):
    """The radius of the arc.
    If x and y radii are different, returns their average."""
    return between(self.x_radius, self.y_radius)
  @radius.setter
  def radius(self, value):
    """Sets the x and y radii of the arc to the given value."""
    self.x_radius = value
    self.y_radius = value

  @property
  def diameter(self):
    """The diameter of the arc.
    If the x and y diameters are different, returns their average."""
    return self.radius*2
  @diameter.setter
  def diameter(self, value):
    """Sets the x and y diameters of the arc to the given value."""
    self.radius = value/2.

  def pcb_repr(self, tx, ty):
    return "ElementArc[%d %d %d %d %d %d %d]" % (
        __mil_to_unit(self.x+tx), __mil_to_unit(self.y+ty),
        __mil_to_unit(self.x_radius), __mil_to_unit(self.y_radius),
        self.start_angle, self.delta_angle,
        __mil_to_unit(self.thickness))



class Footprint(object):
  """A footprint definition. (an "element" in pcb terms)

  A footprint is composed of multiple shapes, defined in the classes
  above.
  """

  def __init__(self, name, **kwargs):
    """Footprint initializer.

    Arguments:
    name -- name of the component

    Keyword arguments:
    description -- text description of the component
    mark_x -- x coordinate of the element's "diamond" marker
      (optional; defaults to 0)
    mark_y -- y coordinate of the element's "diamond" marker
      (optional; defaults to 0)
    text_x -- x coordinate of the left edge of the text
      (optional; defaults to 0)
    text_y -- y coordinate of the top edge of the text
      (optional; defaults to 0)
    text_direction -- rotation of the text
      (optional; 0=normal, 1=rotated 90 degrees left, 2=upside down,
      3=rotated 270 degrees left; defaults to 0)
    """
    self.name = name
    self.description = kwargs.get("description", "")
    self.mark_x = 0
    self.mark_y = 0
    self.text_x = 0
    self.text_y = 0
    self.text_direction = 0
    self.text_scale = 100
    self.shapes = []
    self.pinpadcounter = 1  # for pin/pad auto-numbering

  def __enter__(self):
    """Convenience to allow use of the `with` statement.

    At the end of a `with` statement, the footprint is written to disk
    if no exceptions are raised."""
    return self

  def __exit__(self, type, value, traceback):
    """Ends a `with` statement.

    If no exceptions were raised, the footprint is written to a file in
    the current directoryl the `name` property is used as the filename,
    and the `.fp` extension is appended.
    """
    if type is None and self.name:
      self.write(self.name + ".fp")

  def __getitem__(self, number):
    """Returns the pin or pad with the given number attribute.

    This may not correspond to the actual index of the pin or pad in the
    shapes array. Returns None if there is no matching pin or pad."""
    try:
      return next(s for s in self.shapes if getattr(s, "number", None) == number) 
    except StopIteration:
      return None

  def add_pad(self, **kwargs):
    """Adds a pad to the footprint.

    Keyword arguments:
    same as those for Pad.__init__()

    Return value:
    the added pad

    If `base` and `number` are not specified, the current pin/pad number
    is assigned to the `number` attribute and incremented.
    """
    if not "base" in kwargs:
      kwargs["number"] = kwargs.get("number", self.pinpadcounter)
    pad = Pad(**kwargs)
    self.shapes.append(pad)
    self.pinpadcounter += 1
    return pad

  def add_pin(self, **kwargs):
    """Adds a pin to the footprint.

    Keyword arguments:
    same as those for Pin.__init__()

    Return value:
    the added pin

    If `base` and `number` are not specified, the current pin/pad number
    is assigned to the `number` attribute and incremented.
    """
    if not "base" in kwargs:
      kwargs["number"] = kwargs.get("number", self.pinpadcounter)
    pin = Pin(**kwargs)
    self.shapes.append(pin)
    self.pinpadcounter += 1
    return pin

  def add_pads(self, count, **kwargs):
    """Adds multiple pads at given intervals.

    Arguments:
    count -- number of pads to add

    Keyword arguments:
    x -- x coordinate of the center of the first pad
    y -- y coordinate of the center of the first pad
    dx -- amount to step in the x direction after placing a pad
    dy -- amount to step in the y direction after placing a pad
    width -- width of each pad
    height -- height of each pad

    Return value:
    array of the added pads

    To place staggered pads, a tuple of length >= 2 may be specified for
    `dx` and/or `dy`. In the case of a 2-element tuple, the first
    element is used as the step value after placing every odd pad, and
    the second element is used as the step value after placing every
    even pad.
    """
    return self.__add_shapes(count, self.add_pad, **kwargs)

  def add_pins(self, count, **kwargs):
    """Adds multiple pins at given intervals.

    Arguments:
    count -- number of pins to add

    Keyword arguments:
    x -- x coordinate of the center of the first pin
    y -- y coordinate of the center of the first pin
    dx -- amount to step in the x direction after placing a pin
    dy -- amount to step in the y direction after placing a pin
    hole -- diameter of each pin's drill hole
    diameter -- outer diameter of each pin's copper annulus

    Return value:
    array of the added pins

    To place staggered pins, a tuple of length >= 2 may be specified for
    `dx` and/or `dy`. In the case of a 2-element tuple, the first
    element is used as the step value after placing every odd pin, and
    the second element is used as the step value after placing every
    even pin.
    """
    return self.__add_shapes(count, self.add_pin, **kwargs)

  def __add_shapes(self, count, fn, **kwargs):
    added_shapes = []
    number = kwargs.get("number", self.pinpadcounter)
    dx = kwargs.get("dx", 0)
    dy = kwargs.get("dy", 0)
    for i in range(0, count):
      kwargs["number"] = number
      added_shapes.append(fn(**kwargs))
      kwargs["x"] += dx if not isinstance(dx, tuple) else dx[i % len(dx)]
      kwargs["y"] += dy if not isinstance(dy, tuple) else dy[i % len(dy)]
      number += 1
    return added_shapes

  def add_line(self, *args, **kwargs):
    """Adds a line to the silkscreen layer.

    Arguments:
    same as those for SilkLine.__init__()

    Keyword arguments:
    same as those for SilkLine.__init__()

    Return value:
    the added line
    """
    line = SilkLine(*args, **kwargs)
    self.shapes.append(line)
    return line

  def add_polyline(self, *args, **kwargs):
    """Adds a polyline to the silkscreen layer.

    Arguments:
    same as those for SilkPolyline.__init__()

    Keyword arguments:
    same as those for SilkPolyline.__init__()

    Return value:
    the added polyline
    """
    pline = SilkPolyline(*args, **kwargs)
    self.shapes.append(pline)
    return pline

  def add_arc(self, *args, **kwargs):
    """Adds an arc to the silkscreen layer.

    Arguments:
    same as those for SilkArc.__init__()

    Keyword arguments:
    same as those for SilkArc.__init__()

    Return value:
    the added arc
    """
    arc = SilkArc(*args, **kwargs)
    self.shapes.append(arc)
    return arc

  def mark(self, pin_or_pad):
    """Sets the mark position to the center of the given pin or pad."""
    self.mark_x = pin_or_pad.x
    self.mark_y = pin_or_pad.y

  def __str__(self):
    """Returns a string representation of the footprint in pcb format."""
    s = "Element[\"\" \"%s\" \"\" \"%s\" %d %d %d %d %d %d \"\"] (\n" % (
        self.description, self.name,
        __mil_to_unit(self.mark_x), __mil_to_unit(self.mark_y),
        __mil_to_unit(self.text_x), __mil_to_unit(self.text_y),
        self.text_direction, self.text_scale)
    s += "\n".join(s.pcb_repr(-self.mark_x, -self.mark_y) for s in self.shapes)
    s += "\n)\n"
    return s

  def write(self, filename=None):
    """Writes the footprint to a file with the given name."""
    if filename is None:
      filename = os.path.splitext(sys.argv[0])[0] + ".fp"
    with open(filename, "w") as f:
      f.write(str(self))
