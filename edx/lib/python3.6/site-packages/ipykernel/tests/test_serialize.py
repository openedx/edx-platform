"""test serialization tools"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import pickle
from collections import namedtuple

from ipykernel.serialize import serialize_object, deserialize_object
from IPython.testing import decorators as dec
from ipykernel.pickleutil import CannedArray, CannedClass, interactive


def roundtrip(obj):
    """roundtrip an object through serialization"""
    bufs = serialize_object(obj)
    obj2, remainder = deserialize_object(bufs)
    assert remainder == []
    return obj2


SHAPES = ((100,), (1024,10), (10,8,6,5), (), (0,))
DTYPES = ('uint8', 'float64', 'int32', [('g', 'float32')], '|S10')


def new_array(shape, dtype):
    import numpy
    return numpy.random.random(shape).astype(dtype)

def test_roundtrip_simple():
    for obj in [
        'hello',
        dict(a='b', b=10),
        [1,2,'hi'],
        (b'123', 'hello'),
    ]:
        obj2 = roundtrip(obj)
        assert obj == obj2

def test_roundtrip_nested():
    for obj in [
        dict(a=range(5), b={1:b'hello'}),
        [range(5),[range(3),(1,[b'whoda'])]],
    ]:
        obj2 = roundtrip(obj)
        assert obj == obj2

def test_roundtrip_buffered():
    for obj in [
        dict(a=b"x"*1025),
        b"hello"*500,
        [b"hello"*501, 1,2,3]
    ]:
        bufs = serialize_object(obj)
        assert len(bufs) == 2
        obj2, remainder = deserialize_object(bufs)
        assert remainder == []
        assert obj == obj2

def test_roundtrip_memoryview():
    b = b'asdf' * 1025
    view = memoryview(b)
    bufs = serialize_object(view)
    assert len(bufs) == 2
    v2, remainder = deserialize_object(bufs)
    assert remainder == []
    assert v2.tobytes() == b

@dec.skip_without('numpy')
def test_numpy():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = new_array(shape, dtype=dtype)
            bufs = serialize_object(A)
            bufs = [memoryview(b) for b in bufs]
            B, r = deserialize_object(bufs)
            assert r == []
            assert A.shape == B.shape
            assert A.dtype == B.dtype
            assert_array_equal(A,B)

@dec.skip_without('numpy')
def test_recarray():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in [
            [('f', float), ('s', '|S10')],
            [('n', int), ('s', '|S1'), ('u', 'uint32')],
        ]:
            A = new_array(shape, dtype=dtype)

            bufs = serialize_object(A)
            B, r = deserialize_object(bufs)
            assert r == []
            assert A.shape == B.shape
            assert A.dtype == B.dtype
            assert_array_equal(A,B)

@dec.skip_without('numpy')
def test_numpy_in_seq():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = new_array(shape, dtype=dtype)
            bufs = serialize_object((A,1,2,b'hello'))
            canned = pickle.loads(bufs[0])
            assert isinstance(canned[0], CannedArray)
            tup, r = deserialize_object(bufs)
            B = tup[0]
            assert r == []
            assert A.shape == B.shape
            assert A.dtype == B.dtype
            assert_array_equal(A,B)

@dec.skip_without('numpy')
def test_numpy_in_dict():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = new_array(shape, dtype=dtype)
            bufs = serialize_object(dict(a=A,b=1,c=range(20)))
            canned = pickle.loads(bufs[0])
            assert isinstance(canned['a'], CannedArray)
            d, r = deserialize_object(bufs)
            B = d['a']
            assert r == []
            assert A.shape == B.shape
            assert A.dtype == B.dtype
            assert_array_equal(A,B)

def test_class():
    @interactive
    class C(object):
        a=5
    bufs = serialize_object(dict(C=C))
    canned = pickle.loads(bufs[0])
    assert isinstance(canned['C'], CannedClass)
    d, r = deserialize_object(bufs)
    C2 = d['C']
    assert C2.a == C.a

def test_class_oldstyle():
    @interactive
    class C:
        a=5

    bufs = serialize_object(dict(C=C))
    canned = pickle.loads(bufs[0])
    assert isinstance(canned['C'], CannedClass)
    d, r = deserialize_object(bufs)
    C2 = d['C']
    assert C2.a == C.a

def test_tuple():
    tup = (lambda x:x, 1)
    bufs = serialize_object(tup)
    canned = pickle.loads(bufs[0])
    assert isinstance(canned, tuple)
    t2, r = deserialize_object(bufs)
    assert t2[0](t2[1]) == tup[0](tup[1])

point = namedtuple('point', 'x y')

def test_namedtuple():
    p = point(1,2)
    bufs = serialize_object(p)
    canned = pickle.loads(bufs[0])
    assert isinstance(canned, point)
    p2, r = deserialize_object(bufs, globals())
    assert p2.x == p.x
    assert p2.y == p.y

def test_list():
    lis = [lambda x:x, 1]
    bufs = serialize_object(lis)
    canned = pickle.loads(bufs[0])
    assert isinstance(canned, list)
    l2, r = deserialize_object(bufs)
    assert l2[0](l2[1]) == lis[0](lis[1])

def test_class_inheritance():
    @interactive
    class C(object):
        a=5

    @interactive
    class D(C):
        b=10

    bufs = serialize_object(dict(D=D))
    canned = pickle.loads(bufs[0])
    assert isinstance(canned['D'], CannedClass)
    d, r = deserialize_object(bufs)
    D2 = d['D']
    assert D2.a == D.a
    assert D2.b == D.b
