import ttobak


def test_package_imports():
    assert ttobak is not None


def test_version_is_a_nonempty_string():
    assert isinstance(ttobak.__version__, str)
    assert ttobak.__version__ != ""
