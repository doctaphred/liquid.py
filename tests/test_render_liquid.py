from .utils import assert_raises

from render_liquid import LiquidRenderer, JobError


def test_renderer():
    render = LiquidRenderer().render

    template = r"""{{greeting | capitalize}}, {{name | append:'!'}}"""

    # Does it work?
    result = render(template, {'greeting': 'hello', 'name': 'world'})
    assert result == 'Hello, world!', result

    # Try to break it
    assert_raises(JobError, render, 1, 2)
    assert_raises(JobError, render, 3, 4)

    # Does it still work?
    result = render(template, {'greeting': 'ayy', 'name': 'lmao'})
    assert result == 'Ayy, lmao!', result
