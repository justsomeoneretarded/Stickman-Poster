"""A bounded local llama.cpp worker; no paid service or arbitrary code generation."""
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

LLAMA_VERSION = 'b11729'
LLAMA_SHA256 = 'ef0db60597825a63534a536bd60d3c290cf82631b2a48461278dc2c9eb436c25'
MODEL_FILE = 'Qwen3-4B-Instruct-2507-Q4_K_M.gguf'


class LocalWriter:
    def __init__(self, model_dir, out):
        self.model = Path(model_dir) / MODEL_FILE
        self.out = Path(out)
        self.proc = None
        self.log = None
        # These requests address only the loopback server, not Internet egress.
        self.http = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def __enter__(self):
        if not self.model.is_file():
            raise ValueError(f'Missing local writer model {self.model}; run ci/download_models.py')
        binary = os.environ.get('STUDIO_LLAMA_SERVER', f'work/llama-cpu/llama-{LLAMA_VERSION}/llama-server')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        self.url = f'http://127.0.0.1:{port}'
        self.log = (self.out/'llama-server.log').open('wb')
        self.proc = subprocess.Popen([binary, '-m', str(self.model), '--host', '127.0.0.1', '--port', str(port),
                                      '-c', '32768', '-t', '4', '-tb', '4', '-np', '1', '-ngl', '0', '--no-webui'],
                                     stdout=self.log, stderr=subprocess.STDOUT)
        started = time.monotonic()
        try:
            while time.monotonic()-started < 180:
                if self.proc.poll() is not None:
                    raise RuntimeError('Local writer server exited; inspect llama-server.log')
                try:
                    with self.http.open(self.url+'/health', timeout=2) as response:
                        if response.status == 200:
                            return self
                except (OSError, urllib.error.URLError):
                    time.sleep(.3)
            raise RuntimeError('Local writer server did not become ready')
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def complete(self, messages, schema, max_tokens):
        payload = {'model': 'local-writer', 'messages': messages, 'max_tokens': max_tokens,
                   'temperature': .65, 'top_p': .9, 'seed': 42,
                   'response_format': {'type': 'json_schema', 'json_schema': {'name': 'story', 'strict': True, 'schema': schema}}}
        req = urllib.request.Request(self.url+'/v1/chat/completions', data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json'})
        with self.http.open(req, timeout=3600) as response:
            result = json.load(response)
        choice = result['choices'][0]
        if choice.get('finish_reason') == 'length':
            raise ValueError('Writer output hit the token budget; reduce episode length')
        return choice['message']['content']

    def __exit__(self, *args):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill(); self.proc.wait()
        if self.log:
            self.log.close()
