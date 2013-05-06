from setuptools import setup, find_packages

setup(
    name="capa",
    version="0.1",
    packages=find_packages(exclude=["tests"]),
    install_requires=['distribute==0.6.28', 'pyparsing==1.5.6'],
)
