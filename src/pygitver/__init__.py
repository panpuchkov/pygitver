from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version


def _get_version() -> str:
    try:
        return _pkg_version("pygitver")
    except PackageNotFoundError:
        return "unknown"


__version__ = _get_version()
