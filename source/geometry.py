import math
import typing


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, v: 'Vector' = None):
        v = v or Vector(0, 0)
        return math.sqrt((self.x - v.x) ** 2 + (self.y - v.y) ** 2)

    def side_of(self, a: 'Vector', b: 'Vector'):
        return math.copysign(1, (a.y - self.y) * (b.x - self.x) - (b.y - self.y) * (a.x - self.x))

    def transform(self, shift: 'Vector' = None, angle=0.):
        shift = shift or Vector(0, 0)
        sin, cos = math.sin(angle), math.cos(angle)
        return Vector(cos * self.x - sin * self.y, sin * self.x + cos * self.y) + shift

    def inv_transform(self, shift: 'Vector' = None, angle=0.):
        shift = shift or Vector(0, 0)
        return (self - shift).transform(angle=-angle)

    def mirror(self, x=True, y=True):
        return Vector((-1 if x else 1) * self.x, (-1 if y else 1) * self.y)

    def copy(self):
        return Vector(self.x, self.y)

    def __add__(self, v: 'Vector'):
        return Vector(self.x + v.x, self.y + v.y)

    def __sub__(self, v: 'Vector'):
        return Vector(self.x - v.x, self.y - v.y)

    def __truediv__(self, f: float):
        return Vector(self.x / f, self.y / f)

    def __mul__(self, f: float):
        return Vector(self.x * f, self.y * f)


class LineSegment:
    def __init__(self, a: Vector, b: Vector):
        self.a = a
        self.b = b

    def transform(self, shift=Vector(0, 0), angle=0.):
        return LineSegment(self.a.transform(shift, angle), self.b.transform(shift, angle))

    def inv_transform(self, shift=Vector(0, 0), angle=0.):
        return LineSegment(self.a.inv_transform(shift, angle), self.b.inv_transform(shift, angle))

    def intersects(self, s: 'LineSegment'):
        return self.a.side_of(s.a, s.b) * self.b.side_of(s.a, s.b) <= 0 and \
               s.a.side_of(self.a, self.b) * s.b.side_of(self.a, self.b) <= 0

    def mirror(self, x=True, y=True):
        return LineSegment(self.a.mirror(x, y), self.b.mirror(x, y))


class Box:
    def __init__(self, dims: Vector, center=Vector(0, 0)):
        self.dims = dims
        self.center = center
        self.radius = (self.dims / 2).distance_to()
        self.l, self.r = center.x - dims.x / 2, center.x + dims.x / 2
        self.b, self.t = center.y - dims.y / 2, center.y + dims.y / 2
        self.corners = [Vector(x, y) for x in (self.l, self.r) for y in (self.b, self.t)]

    def contains(self, v: Vector):
        return self.l < v.x < self.r and self.b < v.y < self.t

    def intersects(self, s: LineSegment):
        return not any([
            s.a.x < self.l and s.b.x < self.l, self.r < s.a.x and self.r < s.b.x,
            s.a.y < self.b and s.b.y < self.b, self.t < s.a.y and self.t < s.b.y,
            all([self.l < s.a.x < self.r, self.l < s.b.x < self.r, self.b < s.a.y < self.t, self.b < s.b.y < self.t]),
            abs(sum(v.side_of(s.a, s.b) for v in self.corners)) == 4
        ])

    def mirror(self, x=True, y=True):
        return Box(self.dims, self.center.mirror(x, y))


Geometry = typing.Union[Vector, LineSegment, Box]


def x_mirrors(g: Geometry) -> tuple[Geometry, Geometry]:
    return g, g.mirror(y=False)


def y_mirrors(g: Geometry) -> tuple[Geometry, Geometry]:
    return g, g.mirror(x=False)


def mirrors(g: Geometry) -> tuple[Geometry, Geometry]:
    return g, g.mirror()
