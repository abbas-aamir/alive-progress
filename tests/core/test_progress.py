# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

# noinspection PyProtectedMember
from alive_progress.core.progress import _create_fps_controller


def test_fps_controller_bootstrap_speed():
    fps = _create_fps_controller(None, 100.)

    assert fps(0.) == pytest.approx(10.)


def test_fps_controller_caps_at_calibration_rate():
    fps = _create_fps_controller(100., 1000.)

    assert fps(100.) == pytest.approx(60.)
    assert fps(120.) == pytest.approx(60.)


def test_fps_controller_scales_rate_below_calibration():
    fps = _create_fps_controller(100., 1000.)

    assert 2. < fps(1.) < fps(50.) < 60.


def test_fps_controller_uses_theoretical_rate_by_default():
    explicit = _create_fps_controller(100., 1000.)
    default = _create_fps_controller(None, 100.)

    assert default(50.) == pytest.approx(explicit(50.))
