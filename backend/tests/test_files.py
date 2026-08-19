from fastapi import HTTPException

from backend.api.files import read_and_validate_upload


class DummyUpload:
    def __init__(self, filename, content, content_type):
        self.filename = filename
        self.content_type = content_type
        self.file = type("F", (), {"read": lambda inner_self: content})()


def test_rejects_bad_extension():
    try:
        read_and_validate_upload(DummyUpload("notes.exe", b"MZ", "application/octet-stream"))
        assert False
    except HTTPException as exc:
        assert exc.status_code == 400
