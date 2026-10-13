# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from alive_progress.core.progress import (
    _create_fps_controller, _normalize_total, _resolve_progress_mode, alive_bar,
)


class TestNormalizeTotal:
    def test_none_stays_none(self):
        assert _normalize_total(None) is None

    def test_zero_or_negative_becomes_none(self):
        assert _normalize_total(0) is None
        assert _normalize_total(-10) is None

    def test_positive_int_is_kept(self):
        assert _normalize_total(100) == 100

    def test_non_int_raises_type_error(self):
        with pytest.raises(TypeError):
            _normalize_total('100')
        with pytest.raises(TypeError):
            _normalize_total(1.5)


class TestResolveProgressMode:
    def test_known_total_counts_items(self):
        assert _resolve_progress_mode(100, False) == (100, 'f', 1.e6, 'count')

    def test_known_total_with_manual_still_counts_items(self):
        assert _resolve_progress_mode(100, True) == (100, 'f', 1.e6, 'count')

    def test_no_total_not_manual_counts_items_unknown_mode(self):
        assert _resolve_progress_mode(None, False) == (None, 'f', 1.e6, 'count')

    def test_no_total_manual_tracks_percentage(self):
        assert _resolve_progress_mode(None, True) == (1., '%', 1., 'percent')


class TestFpsController:
    def test_bootstrap_speed_when_rate_not_positive(self):
        fps = _create_fps_controller(lambda: 0., calibrate=None, factor=1.e6)
        assert fps() == 10.
        fps = _create_fps_controller(lambda: -5., calibrate=None, factor=1.e6)
        assert fps() == 10.

    def test_max_fps_when_rate_reaches_calibrate(self):
        fps = _create_fps_controller(lambda: 1000., calibrate=100., factor=1.e6)
        assert fps() == 60.

    def test_fps_increases_with_rate_below_calibrate(self):
        slow = _create_fps_controller(lambda: 1., calibrate=100., factor=1.e6)
        fast = _create_fps_controller(lambda: 50., calibrate=100., factor=1.e6)
        assert slow() < fast() <= 60.


class TestAliveBarSmoke:
    def test_definite_mode(self):
        with alive_bar(10, force_tty=True) as bar:
            for _ in range(10):
                bar()

    def test_manual_mode(self):
        with alive_bar(manual=True, force_tty=True) as bar:
            bar(0.5)
            bar(1.0)

    def test_unknown_mode(self):
        with alive_bar(force_tty=True) as bar:
            for _ in range(5):
                bar()
