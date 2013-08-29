from setuptools import setup

setup(
    name="calc",
    version="0.1.1",
    packages=["calc"],
    install_requires=[
        "pyparsing==1.5.6",
        "numpy",
        "scipy"
    ],
)
