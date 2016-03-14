from setuptools import setup

setup(
    name="chem",
    version="0.1.1",
    packages=["chem"],
    install_requires=[
        "pyparsing==2.0.1",
        "numpy",
        "scipy",
        "nltk<3.0",
    ],
)
