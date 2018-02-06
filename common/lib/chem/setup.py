from setuptools import setup

setup(
    name="chem",
    version="0.2.0-ginkgo",
    packages=["chem"],
    install_requires=[
        "pyparsing==2.0.7",
        "numpy==1.6.2",
        "scipy==0.14.0",
        "nltk==3.2.5",
        "markupsafe",  # Should be replaced by other utilities. See LEARNER-5853 for more details.
    ],
)
