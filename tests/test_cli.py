# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,unused-import,reimported
import mapology.cli as cli


def test_main_nok_too_many_arguments(capsys):
    assert cli.main(['too', 'many']) == 2
    out, err = capsys.readouterr()
    assert not err
    assert out.rstrip() == 'usage: icao.py base/r/IC[/ICAO]'
