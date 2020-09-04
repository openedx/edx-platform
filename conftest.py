"""
Default unit test configuration and fixtures.
"""
from __future__ import absolute_import, unicode_literals
import pytest

from django.db.models.signals import m2m_changed, post_delete, post_init, post_save, pre_delete, pre_init, pre_save

# Import hooks and fixture overrides from the cms package to
# avoid duplicating the implementation

from cms.conftest import _django_clear_site_cache, pytest_configure  # pylint: disable=unused-import


@pytest.fixture(autouse=True)
def no_webpack_loader(monkeypatch):
    monkeypatch.setattr(
        "webpack_loader.templatetags.webpack_loader.render_bundle",
        lambda entry, extension=None, config='DEFAULT', attrs='': ''
    )
    monkeypatch.setattr(
        "webpack_loader.utils.get_as_tags",
        lambda entry, extension=None, config='DEFAULT', attrs='': []
    )
    monkeypatch.setattr(
        "webpack_loader.utils.get_files",
        lambda entry, extension=None, config='DEFAULT', attrs='': []
    )


@pytest.fixture()
def mute_signals(request):
    """
    A fixture to mute all model signals.
    """
    signals = [
        pre_init,
        post_init,
        pre_save,
        post_save,
        pre_delete,
        post_delete,
        m2m_changed
    ]

    restore = {}
    for signal in signals:
        # Temporally remove the signal's receivers (a.k.a attached functions)
        restore[signal] = signal.receivers
        signal.receivers = []

    def restore_signals():
        # When the test tears down, restore the signals.
        for signal_to_restore, receivers in restore.items():
            signal_to_restore.receivers = receivers

    # Called after a test has finished.
    request.addfinalizer(restore_signals)
