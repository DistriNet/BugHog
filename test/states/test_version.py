import pytest
from bughog.version_control.version import Version


def test_version_parsing():
    v = Version('100.0.5')
    assert v.major == 100
    assert v.minor == 0
    assert v.patch == 5
    assert not v.is_pre_release


def test_version_pre_release():
    v = Version('0.1.2')
    assert v.major == 0
    assert v.minor == 1
    assert v.patch == 2
    assert v.is_pre_release


def test_servo_version():
    v = Version('0.0.1-abc123f')
    assert v.major == 0
    assert v.minor == 0
    assert v.patch == 1
    # packaging.version local segment will contain the hash
    assert str(v) == '0.0.1-abc123f'


def test_selectable_version_major():
    assert Version('100.0.5').selectable_version == '100'
    assert Version('1.2.3').selectable_version == '1'


def test_selectable_version_pre_release():
    assert Version('0.1.2').selectable_version == '0.1'
    # Now includes patch when minor is also 0
    assert Version('0.0.1').selectable_version == '0.0.1'


def test_version_comparison():
    assert Version('100.0.0') > Version('99.0.0')
    assert Version('0.1.2') > Version('0.1.1')
    assert Version('0.1.2') < Version('1.0.0')
    assert Version('100.0.1') == Version('100.0.1')


def test_padded_version():
    assert Version('100.0.5').padded() == '0100.0000.0005'
    assert Version('0.1.2').padded() == '0000.0001.0002'
    # Servo style
    assert Version('0.0.1-abc123f').padded() == '0000.0000.0001-abc123f'


def test_invalid_version():
    with pytest.raises(Exception):
        Version('not-a-version')
