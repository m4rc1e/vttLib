from pathlib import Path

import fontTools.ttLib
import pytest
import ufo2ft
import ufoLib2

import vttLib
import vttLib.__main__


@pytest.fixture
def test_ufo_UbuTestData(original_shared_datadir):
    font = ufoLib2.Font.open(original_shared_datadir / "UbuTestData.ufo")
    return font


def test_move_ufo_data_to_file_and_roundtrip(tmp_path, test_ufo_UbuTestData):
    ufo = test_ufo_UbuTestData
    ufo_path = tmp_path / "UbuntuTestData.ufo"
    ufo.save(ufo_path)
    test_ttf_path = tmp_path / "test.ttf"
    test_ttx_path = tmp_path / "test.ttx"

    vttLib.__main__.main(["dumpfile_from_ufo", str(ufo_path), str(test_ttx_path)])
    ### Doctor TTX dump so the simple text compare further down works
    _ttx_dump = fontTools.ttLib.TTFont()
    _ttx_dump.importXML(test_ttx_path)
    _ttx_dump["maxp"].maxPoints = 54
    _ttx_dump["maxp"].maxContours = 2
    _ttx_dump.saveXML(test_ttx_path, tables=("TSI1", "TSI3", "TSI5", "maxp"))
    ###
    ufo_tmp = ufoLib2.Font.open(ufo_path)

    for legacy_data in vttLib.LEGACY_VTT_DATA_FILES:
        assert legacy_data in ufo_tmp.data.keys()

    ttx_dump = fontTools.ttLib.TTFont()
    ttx_dump.importXML(test_ttx_path)
    assert ttx_dump["maxp"].maxFunctionDefs == 89
    assert ttx_dump["maxp"].maxInstructionDefs == 0
    assert ttx_dump["maxp"].maxSizeOfInstructions == 1571
    assert ttx_dump["maxp"].maxStackElements == 542
    assert ttx_dump["maxp"].maxStorage == 47
    assert ttx_dump["maxp"].maxTwilightPoints == 16
    assert ttx_dump["maxp"].maxZones == 2

    ttf = ufo2ft.compileTTF(ufo_tmp)
    ttf.save(test_ttf_path)
    vttLib.__main__.main(["mergefile", str(test_ttx_path), str(test_ttf_path)])
    vttLib.__main__.main(["dumpfile", str(test_ttf_path), str(tmp_path / "test2.ttx")])

    assert (
        Path(tmp_path / "test.ttx").read_text()
        == Path(tmp_path / "test2.ttx").read_text()
    )

    vttLib.__main__.main(["compile", str(test_ttf_path), str(test_ttf_path), "--ship"])
    ttf = fontTools.ttLib.TTFont(test_ttf_path)
    assert "fpgm" in ttf
    assert "TSI1" not in ttf
