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


class DummyThread(object):
    instances = []

    def __init__(self, target, args):
        self.target = target
        self.args = args
        self.daemon = False
        self.started = False
        self.joined = False
        self.__class__.instances.append(self)

    def start(self):
        self.started = True

    def join(self):
        self.joined = True


@pytest.fixture
def terminal():
    fake_stdout = FakeStdout()
    fake_terminal = FakeStdout()
    with mock.patch.object(sys, 'stdout', fake_stdout), \
            mock.patch.object(sys, '__stdout__', fake_terminal):
        yield fake_terminal


@pytest.fixture
def terminal_size():
    with mock.patch('alive_progress.core.progress.get_terminal_size') as mocked:
        mocked.return_value = (200, 24)
        yield


def test_alive_bar_rejects_non_integer_total():
    with pytest.raises(TypeError, match="integer argument expected, got 'float'"):
        with alive_bar(1.0):
            pass


@pytest.mark.parametrize('total', [0, -1])
def test_alive_bar_non_positive_total_uses_unknown_mode(total, terminal, terminal_size):
    with mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.side_effect = [10., 12., 12.]
        with alive_bar(total, theme='ascii', length=5) as bar:
            bar()

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[?25h'
        '[=====] 1 in 2.0s (0.50/s)\n'
    )


def test_alive_bar_counts_and_enriches_prints(terminal, terminal_size):
    with mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.side_effect = [10., 15., 15.]
        with alive_bar(2, 'Job', theme='ascii', length=5) as bar:
            print('hello')
            bar()
            bar(incr=2)
            bar(incr=-10)
            print('bye')

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[2K\ron 0: hello\n'
        '\033[2K\ron 3: bye\n'
        '\033[?25h'
        'Job [=====x (!) 3/2 [150%] in 5.0s (0.60/s)\n'
    )


def test_alive_bar_can_disable_print_enrichment(terminal, terminal_size):
    with mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.side_effect = [10., 12., 12.]
        with alive_bar(2, 'Job', theme='ascii', length=5, enrich_print=False) as bar:
            print('plain')
            bar()

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[2K\rplain\n'
        '\033[?25h'
        'Job [==!  ] (!) 1/2 [50%] in 2.0s (0.50/s)\n'
    )


def test_alive_bar_legacy_text_argument_warns(terminal, terminal_size):
    with mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.side_effect = [10., 15., 15.]
        with alive_bar(2, 'Job', theme='ascii', length=5) as bar:
            with pytest.warns(DeprecationWarning, match=r"use bar\.text\(''\) instead"):
                bar(text='legacy')

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[?25h'
        'Job [==!  ] (!) 1/2 [50%] in 5.0s (0.20/s)\n'
    )


def test_alive_bar_exposes_current_and_text_helpers(terminal, terminal_size):
    with mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.side_effect = [10., 15., 15.]
        with alive_bar(2, 'Job', theme='ascii', length=5) as bar:
            bar()
            assert bar.current() == 1
            bar.text('wide 😺\ntext')

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[?25h'
        'Job [==!  ] (!) 1/2 [50%] in 5.0s (0.20/s)\n'
    )


def test_alive_bar_manual_mode_without_total_uses_percent_current(terminal, terminal_size):
    with mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.side_effect = [10., 15., 15.]
        with alive_bar(manual=True, theme='ascii', length=5) as bar:
            with pytest.warns(DeprecationWarning, match='percent will be mandatory'):
                bar()
            with pytest.warns(DeprecationWarning, match=r"use bar\.text\(''\) instead"):
                bar(.5, text='half')
            assert bar.current() == .5
            print('hi')

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[2K\ron 0: hi\n'
        '\033[?25h'
        '[==!  ] (!) 50% in 5.0s (10.00%/s)\n'
    )


def test_alive_bar_manual_mode_tracks_absolute_percentage(terminal, terminal_size):
    with mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.side_effect = [1., 3., 3.]
        with alive_bar(10, 'Manual', theme='ascii', length=5, manual=True) as bar:
            bar(.34)
            assert bar.current() == 4

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[?25h'
        'Manual [=!   ] (!) 4/10 [34%] in 2.0s (2.00/s)\n'
    )


def test_alive_bar_force_tty_exposes_pause_and_joins_renderer(terminal, terminal_size):
    DummyThread.instances = []
    with mock.patch('alive_progress.core.progress.threading.Thread', DummyThread), \
            mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.return_value = 10.
        with alive_bar(theme='ascii', length=5, force_tty=True) as bar:
            assert hasattr(bar, 'pause')
            with bar.pause():
                print('paused')

    assert [(x.daemon, x.started, x.joined) for x in DummyThread.instances] == [
        (True, True, True)
    ]
    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[?25h'
        '[>    ] 0 in 0s (0.0/s)\n'
        'paused\n'
        '\033[?25l'
        '\033[?25h'
        '[=====] 0 in 0.0s (0.00/s)\n'
    )


def test_alive_bar_unknown_total_counts_without_eta(terminal, terminal_size):
    with mock.patch('alive_progress.core.progress.time.time') as mocked_time:
        mocked_time.side_effect = [10., 14., 14.]
        with alive_bar(theme='ascii', length=5) as bar:
            bar()
            bar()

    assert terminal.getvalue() == (
        '\033[?25l'
        '\033[?25h'
        '[=====] 2 in 4.0s (0.50/s)\n'
    )
