from __future__ import annotations
import http.client
import json
import threading
import unittest
from qwerty.server import LocalServer, run_isolated


class WorkerTests(unittest.TestCase):
    def test_worker_run(self):
        result = run_isolated('run', 'sayit(addit(2, 3));', '')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['output'], '5\n')
        self.assertIn('CALL', result['bytecode'])

    def test_worker_compile_only(self):
        result = run_isolated('check', 'divit(1, 0);', '')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['output'], '')

    def test_worker_error(self):
        result = run_isolated('run', 'divit(1, 0);', '')
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'], 'Q3002')

    def test_worker_limits(self):
        result = run_isolated('run', 'whilst aye {}', '')
        self.assertFalse(result['ok'])
        self.assertIn('LimitError', result['error']['formatted'])

    def test_worker_input(self):
        result = run_isolated('run', 'sayit(askit());', 'Ada')
        self.assertEqual(result['output'], 'Ada\n')


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LocalServer(0)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=12)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result

    def test_index(self):
        status, body, headers = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn(b'Language Studio', body)
        self.assertNotIn(b'__QWERTY_TOKEN__', body)
        self.assertIn('Content-Security-Policy', headers)

    def test_functions(self):
        status, body, _ = self.request('GET', '/api/functions')
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)['functions']), 80)

    def test_unknown_path(self):
        self.assertEqual(self.request('GET', '/../../qwerty/server.py')[0], 404)

    def test_disallowed_host(self):
        self.assertEqual(self.request('GET', '/', headers={'Host': 'attacker.example'})[0], 403)

    def test_missing_token(self):
        self.assertEqual(self.request('POST', '/api/execute', body='{}', headers={'Content-Type': 'application/json'})[0], 403)

    def test_wrong_origin(self):
        headers = {'Origin': 'http://attacker.example', 'X-Qwerty-Token': self.server.token, 'Content-Type': 'application/json'}
        self.assertEqual(self.request('POST', '/api/execute', '{}', headers)[0], 403)

    def test_valid_run(self):
        headers = {'Origin': f'http://127.0.0.1:{self.port}', 'X-Qwerty-Token': self.server.token, 'Content-Type': 'application/json'}
        status, body, _ = self.request('POST', '/api/execute', json.dumps({'source': 'sayit(80);', 'action': 'run'}), headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['output'], '80\n')

    def test_malformed_request(self):
        headers = {'Origin': f'http://127.0.0.1:{self.port}', 'X-Qwerty-Token': self.server.token, 'Content-Type': 'application/json'}
        for body in ('not-json', '[]', '{"source": 123}', '{"source":"", "action": "delete"}'):
            self.assertEqual(self.request('POST', '/api/execute', body, headers)[0], 400)


if __name__ == '__main__':
    unittest.main()
