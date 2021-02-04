  # lint-amnesty, pylint: disable=django-not-configured, missing-module-docstring
from setuptools import setup

setup(
    name="symmath",
    version="0.3",
    packages=["symmath"],
    install_requires=[
        "sympy",
    ],
)
