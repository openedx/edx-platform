from setuptools import setup

setup(
    name="chem",
    version="0.1.1",
    packages=["chem"],
    install_requires=[
        "pyparsing==1.5.6",
        "numpy",
        "scipy",
        "nltk==2.0.4",
    ],
)
