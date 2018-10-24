"""
Python unit and integration test utilities.
"""
import os

import pytest
from django.core.management import call_command


@pytest.fixture(autouse=True, scope='session')
def load_python_test_data(django_db_setup, django_db_blocker):
    """
    A fixture to load global python test data into the database.
    """
    with django_db_blocker.unblock():
        source_dir = os.path.dirname(os.path.abspath(__file__))
        db_fixtures_dir = os.path.join(source_dir, 'db_fixtures')
        for filename in os.listdir(db_fixtures_dir):
            if filename.endswith('.json'):
                json_file_path = os.path.join(db_fixtures_dir, filename)
                call_command('loaddata', json_file_path)
