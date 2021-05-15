# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,unused-import,reimported
import pytest  # type: ignore

import mapology.cli as cli


def test_main_nok_too_many_arguments():
    message = r'main\(\) takes from 0 to 1 positional arguments but 2 were given'
    with pytest.raises(TypeError, match=message):
        cli.main(1, 2)


def test_main_nok_empty_list(capsys):
    assert cli.main([]) is None
    expect_err = 'ERROR arguments expected.'
    out, err = capsys.readouterr()
    assert err.strip() == expect_err


def test_main_ok_int(capsys):
    assert cli.main([42]) is None
    out, err = capsys.readouterr()
    assert out.strip() == ''
