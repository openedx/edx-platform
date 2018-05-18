from setuptools import setup

setup(
    name="chem",
    version="0.1.2",
    packages=["chem"],
    install_requires=[
        "pyparsing==2.2.0",
        "numpy==1.6.2",
        "scipy==0.14.0",
        "nltk",
    ],
)
