from setuptools import setup

setup(
    name="opaque_keys",
    version="0.2",
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
        ],
        'course_key': [
            'slashes = opaque_keys.locations:SlashSeparatedCourseKey',
            'course-locator = opaque_keys.locator:CourseLocator',
        ],
        'usage_key': [
            'location = opaque_keys.locations:Location',
            'edx = opaque_keys.locator:BlockUsageLocator',
        ],
        'asset_key': [
            'asset-location = opaque_keys.locations:AssetLocation',
        ],
        'definition_key': [
            'defx = opaque_keys.locator:DefinitionLocator',
        ],
    }
)
