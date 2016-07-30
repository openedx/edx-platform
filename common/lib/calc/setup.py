from setuptools import setup

setup(
    name="calc",
    version="0.2",
    packages=["calc"],
    install_requires=[
        "pyparsing==2.0.1",
        "numpy",
        "scipy<0.18"
    ],
)
