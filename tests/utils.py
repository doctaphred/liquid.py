from contextlib import contextmanager


@contextmanager
def _assert_raises(exc_type):
    try:
        yield
    except exc_type:
        pass
    except Exception as exc:
        raise AssertionError(
            'Expected {}; got {}: {}'.format(
                exc_type.__name__, type(exc).__name__, exc))
    else:
        raise AssertionError('{} was not raised'.format(exc_type.__name__))


def assert_raises(exc_type, func=None, *args, **kwargs):
    if func is None:
        return _assert_raises(exc_type)
    else:
        with _assert_raises(exc_type):
            func(*args, **kwargs)
