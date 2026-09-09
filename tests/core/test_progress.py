# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import io
import sys

import pytest

try:
    from unittest import mock
except ImportError:
    import mock  # noqa

from alive_progress.core.progress import alive_bar


class FakeStdout(io.StringIO):
    def isatty(self):
        return False


@pytest.fixture
def terminal():
    stream = FakeStdout()
    with mock.patch.object(sys, 'stdout', stream), \
            mock.patch.object(sys, '__stdout__', stream), \
            mock.patch('alive_progress.core.progress.get_terminal_size', return_value=(999, 24)):
        yield stream


def test_alive_bar_rejects_non_integer_total():
    with pytest.raises(TypeError) as exc:
        with alive_bar(1.0):
            pass

    assert str(exc.value) == "integer argument expected, got 'float'."


def test_alive_bar_renders_final_receipt_in_non_tty(terminal):
    with mock.patch('alive_progress.core.progress.time.time', side_effect=(10., 15., 15.)):
        with alive_bar(3, 'Job', length=10, theme='ascii') as bar:
            assert bar.current() == 0
            bar()
            bar(incr=2)
            assert bar.current() == 3

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[?25h'
        'Job [==========] 3/3 [100%] in 5.0s (0.60/s)\n'
    )


def test_alive_bar_ignores_negative_increments(terminal):
    with mock.patch('alive_progress.core.progress.time.time', side_effect=(10., 15., 15.)):
        with alive_bar(3, length=10, theme='ascii') as bar:
            bar()
            bar(incr=-10)

    assert '[===!      ] (!) 1/3 [33%]' in terminal.getvalue()


def test_alive_bar_legacy_text_argument_warns(terminal):
    with mock.patch('alive_progress.core.progress.time.time', side_effect=(10., 15., 15.)):
        with alive_bar(1, length=10, theme='ascii') as bar:
            with pytest.warns(DeprecationWarning):
                bar(text='legacy text')

    assert 'legacy text' not in terminal.getvalue()


def test_alive_bar_manual_mode_tracks_percentage(terminal):
    with mock.patch('alive_progress.core.progress.time.time', side_effect=(10., 15., 15.)):
        with alive_bar(10, length=10, theme='ascii', manual=True) as bar:
            bar(.25)
            assert bar.current() == 3
            bar(1.)
            assert bar.current() == 10

    assert '[==========] 10/10 [100%] in 5.0s (2.00/s)' in terminal.getvalue()


def test_alive_bar_manual_mode_without_total_reports_percent(terminal):
    with mock.patch('alive_progress.core.progress.time.time', side_effect=(10., 15., 15.)):
        with alive_bar(manual=True, length=10, theme='ascii') as bar:
            bar(.25)
            assert bar.current() == .25

    assert '[==!       ] (!) 25% in 5.0s (5.00%/s)' in terminal.getvalue()
