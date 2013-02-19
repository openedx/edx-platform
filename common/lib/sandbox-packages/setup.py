from setuptools import setup

setup(
    name="sandbox-packages",
    version="0.1",
    packages=[
        "symmath",
        "verifiers",
    ],
    py_modules=[
        "eia",
    ],
    install_requires=[
        # symmath needs:
        "sympy", "requests", "lxml",
    ],
)
