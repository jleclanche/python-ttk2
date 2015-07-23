from __future__ import unicode_literals
from distutils import dir_util
from pytest import fixture
from ttk2.formats import Unit
from ttk2.formats._xliff import XLIFFStore
import os


@fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir


def test_read(datadir):
    store = XLIFFStore()
    source_file = datadir.join("source.xlf")
    store.read(source_file.open(), "foo", "bar")

    assert len(store.units) == 7

    def check_unit(unit, key, value, lang):
        assert unit.key == key
        assert unit.value == value
        assert unit.lang == lang

    check_unit(store.units[0], "London", "London", "en-US")
    check_unit(store.units[1], "Greece", "Greece", "en-US")
    check_unit(store.units[2], "Moscow", "Moscow", "en-US")
    check_unit(store.units[3], "Japan", "Japan", "en-US")
    check_unit(store.units[4], "London", "Londres", "pt-BR")
    check_unit(store.units[5], "Moscow", "Moscou", "pt-BR")
    check_unit(store.units[6], "Japan", "Japão", "pt-BR")


def test_serialize(datadir):
    unit_1 = Unit("A", "Alpha")
    unit_2 = Unit("B", "Bravo")
    unit_3 = Unit("C", "Charlie")
    unit_4 = Unit("D", "      ")
    unit_5 = Unit("E", None)

    store = XLIFFStore()
    store.units = [unit_1, unit_2, unit_3, unit_4, unit_5]

    result = store.serialize()
    expected_file = datadir.join("expected.xlf")
    assert result == expected_file.read()
