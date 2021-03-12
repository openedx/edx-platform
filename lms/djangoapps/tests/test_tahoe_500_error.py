"""
Test case to address slow 500 error failures.
"""

import pytest

from django.urls import reverse


@pytest.mark.django_db
def test_working_contact_page(client):
    """
    Sanity check to ensure contact page works.

    If this test fails just pick another page like login.
    """
    url = reverse('contact')
    response = client.get(url)
    assert response.status_code == 200, response.content


def test_failing_contact_page(client, capsys):
    """
    Ensure no repeated handling of exceptions showing in views tests failures.

    Otherwise debugging test failures views means scrolling through thousands of error lines of the same error below:

     - "During handling of the above exception, another exception occurred"

    This test needs `pytest.mark.django_db` but removing it on purpose to simulate a broken test which results in an
    HTTP 500 error.
    """
    url = reverse('contact')
    with pytest.raises(Exception) as exception:
        # Simulates a server-error
        client.get(url)
    assert 'Context is already bound to a template' not in str(exception), 'Avoid nested errors in server-error.html'
    assert 'Database access not allowed, use the "django_db" mark' in str(exception)

    captured = capsys.readouterr()
    nested_errors_message = 'During handling of the above exception, another exception occurred:'
    assert captured.count(nested_errors_message) == 0, 'No nested errors in server-error.html should happen'
