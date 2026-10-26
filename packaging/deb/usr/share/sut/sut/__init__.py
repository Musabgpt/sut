"""SUT — البائع السوري."""

__all__ = ["SutApp", "main"]


def __getattr__(name: str):
    if name in {"SutApp", "main"}:
        from .app import SutApp, main

        globals()[name] = {"SutApp": SutApp, "main": main}[name]
        return globals()[name]
    raise AttributeError(name)
