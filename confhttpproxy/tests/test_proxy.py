from unittest import TestCase
import subprocess
import pytest
import time
import requests

from confhttpproxy import ProxyRouter, ProxyRouterException, NullRouter


@pytest.fixture
def config_fixture():
    yield {'api_host': 'localhost',
           'api_port': 88}

@pytest.fixture
def start_proxy():
    cmds = ['configurable-http-proxy', '--port=80', '--api-port=88',
            '--no-prepend-path', '--no-include-prefix']
    proxyserver = subprocess.Popen(
            cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t1 = subprocess.Popen(
        ['python3', '-m', 'http.server', '5555'],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE,
        cwd='/var'
    )
    t2 = subprocess.Popen(
        ['python3', '-m', 'http.server', '6666'],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE,
        cwd='/sbin'
    )
    time.sleep(3)
    try:
        yield 5555, 6666
    finally:
        time.sleep(1)
        proxyserver.kill()
        t1.kill()
        t2.kill()

def test_null1():
    pr = ProxyRouter.get_proxy()
    assert type(pr) == NullRouter


def test_no_routes(config_fixture, start_proxy):
    pr = ProxyRouter.get_proxy(config_fixture)
    assert type(pr) == ProxyRouter
    assert pr.routes == {}


def test_connect_to_internal_process_via_proxy_1(config_fixture, start_proxy):
    """ Create a route to proxy but specifify the route prefix. """
    pr = ProxyRouter.get_proxy(config_fixture)
    pfx, host = pr.add("http://localhost:5555", 'test/server/1')
    assert pfx in [p[1:] for p in pr.routes.keys()]
    assert 'spool' in requests.get(f'http://localhost/{pfx}').text


def test_connect_to_internal_process_via_proxy_2(config_fixture, start_proxy):
    """ Create route to proxy but have it auto-generate a route prefix. """
    pr = ProxyRouter.get_proxy(config_fixture)
    pfx, host = pr.add("http://localhost:6666")
    assert pfx in [p[1:] for p in pr.routes.keys()]
    assert 'ldconfig' in requests.get(f'http://localhost/{pfx}').text


def test_make_and_delete_routes(config_fixture, start_proxy):
    pr = ProxyRouter.get_proxy(config_fixture)
    pfx1, host1 = pr.add("http://localhost:5555")
    pfx2, host2 = pr.add("http://localhost:6666")
    assert pr.routes
    pr.remove(pfx1)
    pr.remove(pfx2)
    assert len(pr.routes.keys()) == 0
