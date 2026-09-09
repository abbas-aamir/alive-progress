# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from alive_progress.core import progress
from alive_progress.core.progress import alive_bar


class StdoutSpy(object):
    def __init__(self, tty=False):
        self.tty = tty
        self.parts = []

    def write(self, data):
        self.parts.append(data)

    def flush(self):
        pass

    def isatty(self):
        return self.tty

    @property
    def text(self):
        return ''.join(self.parts)


@pytest.fixture
def stdout(monkeypatch):
    spy = StdoutSpy()
    monkeypatch.setattr(progress.sys, '__stdout__', spy)
    monkeypatch.setattr(progress.sys, 'stdout', spy)
    monkeypatch.setattr(progress, 'get_terminal_size', lambda: (200, 24))
    monkeypatch.setattr(progress, 'install_logging_hook', lambda: {})
    monkeypatch.setattr(progress, 'uninstall_logging_hook', lambda before: None)
    return spy


def set_clock(monkeypatch, *values):
    ticks = iter(values)
    monkeypatch.setattr(progress.time, 'time', lambda: next(ticks))


def test_alive_bar_requires_integer_total():
    with pytest.raises(TypeError) as exc:
        with alive_bar(1.5):
            pass

    assert "integer argument expected, got 'float'." == str(exc.value)


def test_alive_bar_counts_items_and_ignores_negative_increments(stdout, monkeypatch):
    set_clock(monkeypatch, 0., 2., 2.)

    with alive_bar(3, title='Loading') as bar:
        assert bar.current() == 0
        bar()
        bar(incr=2)
        bar(incr=-10)
        bar.text('Done\nnow')
        assert bar.current() == 3

    assert 'Loading' in stdout.text
    assert '3/3 [100%]' in stdout.text
    assert 'in 2.0s' in stdout.text
    assert '(1.50/s)' in stdout.text
    assert 'Done now' not in stdout.text


def test_alive_bar_enriches_print_output_with_current_count(stdout, monkeypatch):
    set_clock(monkeypatch, 0., 1., 1.)

    with alive_bar(5) as bar:
        bar()
        print('hello')

    assert 'on 1: hello\n' in stdout.text


def test_alive_bar_manual_total_updates_count_from_percentage(stdout, monkeypatch):
    set_clock(monkeypatch, 0., 2., 2.)

    with alive_bar(10, manual=True) as bar:
        bar(.25)
        assert bar.current() == 3

    assert '(!) 3/10 [25%]' in stdout.text


def test_alive_bar_zero_total_uses_unknown_counting_mode(stdout, monkeypatch):
    set_clock(monkeypatch, 0., 4., 4.)

    with alive_bar(0) as bar:
        bar()
        bar(incr=4)

    assert '5 in 4.0s' in stdout.text
    assert '(1.25/s)' in stdout.text
