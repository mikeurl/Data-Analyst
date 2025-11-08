"""Hugging Face Spaces entry point for the Higher Education AI Analyst."""

from importlib.util import find_spec
import sys
import types


def _ensure_matplotlib_stub():
    """Provide a lightweight matplotlib placeholder when the package is absent.

    Some cached deployments may still attempt to import ``matplotlib`` from older
    versions of the assistant. Hugging Face Spaces does not ship the dependency
    by default, so we register a tiny stub that raises a clear runtime error if
    any plotting routine is invoked. This keeps the application from crashing at
    import time while signalling that charting features are unavailable.
    """

    try:
        spec = find_spec("matplotlib")
    except ModuleNotFoundError:
        spec = None

    if spec is not None:
        return

    stub = types.ModuleType("matplotlib")

    class _PyplotStub(types.ModuleType):
        """Placeholder for ``matplotlib.pyplot`` that explains the limitation."""

        def __getattr__(self, name):
            raise RuntimeError(
                "Matplotlib is not installed in this deployment. Install the "
                "'matplotlib' package to enable plotting support."
            )

        def show(self, *args, **kwargs):  # pragma: no cover - defensive stub
            raise RuntimeError(
                "Matplotlib is not installed in this deployment. Install the "
                "'matplotlib' package to enable plotting support."
            )

    stub.pyplot = _PyplotStub("matplotlib.pyplot")

    def _unavailable(*_args, **_kwargs):  # pragma: no cover - defensive stub
        raise RuntimeError(
            "Matplotlib is not installed in this deployment. Install the "
            "'matplotlib' package to enable plotting support."
        )

    stub.use = _unavailable
    stub.__all__ = ["pyplot", "use"]

    sys.modules.setdefault("matplotlib", stub)


_ensure_matplotlib_stub()

from ai_sql_python_assistant import main


if __name__ == "__main__":
    main()
