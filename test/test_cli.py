# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,unused-import,reimported
import mapology.cli as cli


def test_main_nok_too_many_arguments(capsys):
    assert cli.main(['too', 'many']) == 2
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == cli.USAGE.rstrip()


def test_main_ok_too_few_arguments(capsys):
    assert cli.main([]) == 0
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == cli.USAGE.rstrip()


def test_main_ok_short_help_argument(capsys):
    assert cli.main(['-h']) == 0
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == cli.USAGE.rstrip()


def test_main_ok_long_help_argument(capsys):
    assert cli.main(['--help']) == 0
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == cli.USAGE.rstrip()


def test_main_ok_short_help_argument_and_then_some(capsys):
    assert cli.main(['-h', 'and', 'then', 'some']) == 0
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == cli.USAGE.rstrip()


def test_main_nok_icao_without_parameter(capsys):
    assert cli.main(['icao']) == 2
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == 'usage: mapology icao base/r/[IC/[ICAO]]'


def test_main_nok_prefix_and_then_some(capsys):
    assert cli.main(['prefix', 'and', 'then', 'some']) == 2
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == 'usage: mapology prefix'


def test_main_nok_index_and_then_some(capsys):
    assert cli.main(['index', 'and', 'then', 'some']) == 2
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == 'usage: mapology index'


def test_main_nok_shave_what(capsys):
    assert cli.main(['shave']) == 2
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == 'usage: mapology shave countries-to-be-shaved-geo.json-file'
