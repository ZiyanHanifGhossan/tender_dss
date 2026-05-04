from modules import reporting
import io


def test_save_get_delete_logo(tmp_path):
    path = tmp_path / "test_logo.png"
    data = b"ABC"
    # save
    reporting.save_global_logo_bytes(data, path=str(path), backup_old=False)
    # get
    got = reporting.get_global_logo_bytes(path=str(path))
    assert got == data
    # delete
    assert reporting.delete_global_logo(path=str(path)) is True
    assert reporting.get_global_logo_bytes(path=str(path)) is None


def test_backup_on_replace(tmp_path):
    path = tmp_path / "test_logo.png"
    data1 = b"FIRST"
    data2 = b"SECOND"
    reporting.save_global_logo_bytes(data1, path=str(path), backup_old=False)
    # replace with backup
    reporting.save_global_logo_bytes(data2, path=str(path), backup_old=True)
    # original should have backup
    backups = list(tmp_path.glob("test_logo.png.*.bak"))
    assert len(backups) == 1
    # current content should be data2
    assert reporting.get_global_logo_bytes(path=str(path)) == data2