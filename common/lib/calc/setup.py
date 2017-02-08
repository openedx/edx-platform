from setuptools import setup

setup(
    name="calc",
    version="0.2",
    packages=["calc"],
    install_requires=[
        "pyparsing==2.0.7",
        "numpy==1.6.2",
        "scipy==0.14.0",
    ],
)
