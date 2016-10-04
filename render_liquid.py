#!/usr/bin/env python3
import json
from functools import partial
from subprocess import Popen, PIPE


script = r"""
require 'json'
require 'liquid'

opts = {strict_variables: true, strict_filters: true}

loop do
    template = Liquid::Template.parse(JSON.load(STDIN.gets()))
    context = JSON.parse(STDIN.gets())
    result = template.render(context, opts)
    STDOUT.puts JSON.dump(result)
    STDOUT.flush
end
"""


def renderer():
    command = ['ruby', '-e', script]
    worker = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def send(message):
        worker.stdin.write(json.dumps(message).encode())
        worker.stdin.write(b'\n')
        worker.stdin.flush()

    def recv():
        try:
            output = next(worker.stdout)
        except StopIteration:
            raise Exception(worker.stderr.read().decode('utf-8'))
        else:
            reply = json.loads(output.decode('utf-8'))
            return reply

    def render(template, context):
        send(template)
        send(context)
        return recv()

    return render


if __name__ == '__main__':
    import sys
    _, template = sys.argv
    render = renderer()
    for line in sys.stdin:
        context = json.loads(line)
        rendered = render(template, context)
        print(rendered, flush=True)
