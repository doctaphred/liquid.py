#!/usr/bin/env python3
import json
import logging
from subprocess import Popen, PIPE


logger = logging.getLogger(__name__)


script = r"""
require 'json'
require 'liquid'

opts = {strict_variables: true, strict_filters: true}

loop do
    input = STDIN.gets
    exit 0 if input.nil?
    begin
        args = JSON.parse(input)
        template = Liquid::Template.parse(args["template"])
        result = template.render(args["context"], opts)
        ok = true
    rescue => exc
        result = exc
        ok = false
    end
    STDOUT.puts(JSON.dump({"ok" => ok, "result" => result}))
    STDOUT.flush
end
"""


class WorkerError(Exception):
    pass


class JobError(Exception):
    pass


class LiquidRenderer:

    command = ['ruby', '-e', script]

    def __init__(self):
        self.worker = Popen(self.command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def stop(self):
        self.worker.stdout.close()
        self.worker.stderr.close()
        self.worker.stdin.close()
        self.worker.wait()

    def send(self, message):
        self.worker.stdin.write(json.dumps(message).encode())
        self.worker.stdin.write(b'\n')
        self.worker.stdin.flush()

    def recv(self):
        try:
            reply = next(self.worker.stdout)
        except StopIteration as exc:
            info = self.worker.stderr.read().decode('utf-8')
            logger.error(info)
            raise WorkerError(info)

        try:
            reply_data = json.loads(reply.decode('utf-8'))
            # TODO: replace with proper schema validation.
            ok = reply_data.pop('ok')
            result = reply_data.pop('result')
            assert not reply_data
        except Exception as exc:
            # reply.decode, json.loads, or the validation logic may
            # raise arbitrary exceptions; they all represent an error in
            # the subprocess.
            logger.exception(reply)
            raise WorkerError(exc)

        if not ok:
            raise JobError(result)
        else:
            return result

    def render(self, template, context):
        self.send({'template': template, 'context': context})
        return self.recv()


if __name__ == '__main__':
    import sys
    _, template = sys.argv
    render = LiquidRenderer().render
    for line in sys.stdin:
        context = json.loads(line)
        rendered = render(template, context)
        print(rendered, flush=True)
