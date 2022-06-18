from django.http import HttpResponse
from django.test import RequestFactory

from waffle.middleware import WaffleMiddleware


get = RequestFactory().get('/foo')


def test_set_cookies():
    get.waffles = {'foo': [True, False], 'bar': [False, False]}
    resp = HttpResponse()
    assert 'dwf_foo' not in resp.cookies
    assert 'dwf_bar' not in resp.cookies

    resp = WaffleMiddleware().process_response(get, resp)
    assert 'dwf_foo' in resp.cookies
    assert 'dwf_bar' in resp.cookies

    assert 'True' == resp.cookies['dwf_foo'].value
    assert 'False' == resp.cookies['dwf_bar'].value


def test_rollout_cookies():
    get.waffles = {'foo': [True, True],
                   'bar': [False, True],
                   'baz': [True, False],
                   'qux': [False, False]}
    resp = HttpResponse()
    resp = WaffleMiddleware().process_response(get, resp)
    for k in get.waffles:
        cookie = 'dwf_%s' % k
        assert cookie in resp.cookies
        assert str(get.waffles[k][0]) == resp.cookies[cookie].value
        if get.waffles[k][1]:
            assert bool(resp.cookies[cookie]['max-age']) == get.waffles[k][0]
        else:
            assert resp.cookies[cookie]['max-age']


def test_testing_cookies():
    get.waffles = {}
    get.waffle_tests = {'foo': True, 'bar': False}
    resp = HttpResponse()
    resp = WaffleMiddleware().process_response(get, resp)
    for k in get.waffle_tests:
        cookie = 'dwft_%s' % k
        assert str(get.waffle_tests[k]) == resp.cookies[cookie].value
        assert not resp.cookies[cookie]['max-age']
