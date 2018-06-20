from unittest import TestCase
import subprocess
import pytest
import time
import requests
import uuid

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
    assert pr.is_null_proxy is True


def test_no_routes(config_fixture, start_proxy):
    pr = ProxyRouter.get_proxy(config_fixture)
    assert type(pr) == ProxyRouter
    assert pr.routes == {}


def test_connect_to_internal_process_via_proxy_1(config_fixture, start_proxy):
    """ Create a route to proxy but specifify the route prefix. """
    pr = ProxyRouter.get_proxy(config_fixture)
    pfx, host = pr.add("http://localhost:5555", 'test/server/1')
    assert host == 'http://localhost:5555'
    assert pfx in [p[1:] for p in pr.routes.keys()]
    assert 'spool' in requests.get(f'http://localhost/{pfx}').text


def test_connect_to_internal_process_via_proxy_2(config_fixture, start_proxy):
    """ Create route to proxy but have it auto-generate a route prefix. """
    pr = ProxyRouter.get_proxy(config_fixture)
    pfx, host = pr.add("http://localhost:6666")
    assert pfx in [p[1:] for p in pr.routes.keys()]
    assert 'ldconfig' in requests.get(f'http://localhost/{pfx}').text


def test_search(config_fixture, start_proxy):
    rando = str(uuid.uuid4()).replace('-', '')[:6]
    pr = ProxyRouter.get_proxy(config_fixture)
    pf1, host1 = pr.add("http://localhost:6666")
    pf2, host2 = pr.add("http://localhost:5555", f'constant/{rando}')

    assert pr.search('cat') is None
    assert pr.search('http://localhost:6666')[1:].isalnum()
    assert pr.search('http://localhost:5555') == f'/constant/{rando}'
    assert pr.search(pf1) is None
    assert pr.search(pf2) is None


def test_check(config_fixture, start_proxy):
    pr = ProxyRouter.get_proxy(config_fixture)
    pf1, host1 = pr.add("http://localhost:6666")
    pf2, host2 = pr.add("http://localhost:5555", f'constant/x')
    pf3, host3 = pr.add("http://localhost:9911", f'not/real')
    pf4, host4 = pr.add("http://12.24.111.21:22", f'should/timeout')

    r1 = pr.search("http://localhost:6666")
    r2 = pr.search("http://localhost:5555")

    t0 = time.time()
    assert pr.check(pf1) is True
    assert pr.check(pf2) is True
    assert pr.check(r1) is True
    assert pr.check(r2) is True
    assert pr.check('constant/x') is True
    assert pr.check(pf3) is False
    assert pr.check(pf4) is False
    t1 = time.time()
    # Check that timeouts timed-out super quickly
    assert t1 - t0 < 2.0


def test_make_and_delete_routes(config_fixture, start_proxy):
    pr = ProxyRouter.get_proxy(config_fixture)
    pfx1, host1 = pr.add("http://localhost:5555")
    pfx2, host2 = pr.add("http://localhost:6666")
    assert pr.routes
    pr.remove(pfx1)
    pr.remove(pfx2)
    assert len(pr.routes.keys()) == 0

