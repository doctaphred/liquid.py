#!/usr/bin/env python3
import json
import logging
from subprocess import Popen, PIPE, CalledProcessError


logger = logging.getLogger(__name__)


script = r"""
require 'json'
require 'liquid'

opts = {strict_variables: true, strict_filters: true}

loop do
    template_input = STDIN.gets
    context_input = STDIN.gets
    begin
        template = Liquid::Template.parse(JSON.load(template_input))
        context = JSON.parse(context_input)
        result = template.render(context, opts)
        ok = true
    rescue => exc
        result = exc
        ok = false
    end
    STDOUT.puts(JSON.dump({"ok" => ok, "result" => result}))
    STDOUT.flush
end
"""


class RenderError(ValueError):
    pass


def renderer():
    command = ['ruby', '-e', script]
    worker = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def send(message):
        worker.stdin.write(json.dumps(message).encode())
        worker.stdin.write(b'\n')
        worker.stdin.flush()

    def recv():
        try:
            reply = next(worker.stdout)
        except StopIteration as exc:
            logger.exception()
            raise CalledProcessError(exc)

        try:
            reply_data = json.loads(reply.decode('utf-8'))
            # TODO: replace with proper schema validation.
            ok = reply_data.pop('ok')
            result = reply_data.pop('result')
            if reply_data:
                raise ValueError(reply_data)
        except Exception as exc:
            # reply.decode, json.loads, or the validation logic may
            # raise arbitrary exceptions; they all represent an error in
            # the subprocess.
            logger.exception(reply)
            raise CalledProcessError(exc)

        if not ok:
            raise RenderError(result)
        else:
            return result

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
