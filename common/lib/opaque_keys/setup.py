from setuptools import setup

setup(
    name="opaque_keys",
    version="0.1",
    packages=[
        "opaque_keys",
    ],
    install_requires=[
        "stevedore"
    ],
    entry_points={
        'opaque_keys.testing': [
            'base10 = opaque_keys.tests.test_opaque_keys:Base10Key',
            'hex = opaque_keys.tests.test_opaque_keys:HexKey',
            'dict = opaque_keys.tests.test_opaque_keys:DictKey',
        ]
    }
)
