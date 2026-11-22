"""PB-18 add a resume, PB-19 replace it."""
import io
import zipfile

from tests.conftest import RESUME_TEXT, auth_header


def make_docx(text: str) -> bytes:
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    paragraphs = "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in text.splitlines())
    xml = f'<?xml version="1.0"?><w:document xmlns:w="{ns}"><w:body>{paragraphs}</w:body></w:document>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return buffer.getvalue()


def upload(client, token, name, data, mime="application/octet-stream"):
    return client.post("/api/resumes/upload", files={"file": (name, data, mime)}, headers=auth_header(token))


def test_upload_txt_becomes_current(client, student_token):
    response = upload(client, student_token, "resume.txt", RESUME_TEXT.encode())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["is_current"] is True and body["source"] == "txt"
    assert "FastAPI" in body["text"]
    current = client.get("/api/resumes/current", headers=auth_header(student_token)).json()
    assert current["id"] == body["id"]


def test_upload_docx_extracts_text(client, student_token):
    response = upload(client, student_token, "resume.docx", make_docx(RESUME_TEXT))
    assert response.status_code == 201, response.text
    assert "Teaching Assistant" in response.json()["text"]


def test_paste_text(client, student_token):
    response = client.post("/api/resumes/text", json={"text": RESUME_TEXT}, headers=auth_header(student_token))
    assert response.status_code == 201
    assert response.json()["source"] == "pasted"


def test_rejects_unsupported_empty_large_and_short_files(client, student_token):
    assert upload(client, student_token, "photo.png", b"\x89PNG....").status_code == 400
    assert upload(client, student_token, "resume.txt", b"").status_code == 400
    assert upload(client, student_token, "resume.txt", b"a" * (2 * 1024 * 1024 + 10)).status_code == 400
    short = upload(client, student_token, "resume.txt", b"Just a name")
    assert short.status_code == 400
    assert "paste" in short.json()["detail"].lower()
    broken = upload(client, student_token, "resume.docx", b"not really a zip file")
    assert broken.status_code == 400
    # Nothing was saved by the failed uploads
    assert client.get("/api/resumes", headers=auth_header(student_token)).json() == []


def test_replacing_keeps_history_with_one_current(client, student_token):
    first = upload(client, student_token, "v1.txt", RESUME_TEXT.encode()).json()
    second = upload(client, student_token, "v2.txt", (RESUME_TEXT + "\nNew: Docker").encode()).json()
    versions = client.get("/api/resumes", headers=auth_header(student_token)).json()
    assert [v["id"] for v in versions if v["is_current"]] == [second["id"]]
    assert len(versions) == 2
    # Switch back to the first version
    client.post(f"/api/resumes/{first['id']}/make-current", headers=auth_header(student_token))
    assert client.get("/api/resumes/current", headers=auth_header(student_token)).json()["id"] == first["id"]


def test_deleting_current_promotes_latest_remaining(client, student_token):
    first = upload(client, student_token, "v1.txt", RESUME_TEXT.encode()).json()
    second = upload(client, student_token, "v2.txt", RESUME_TEXT.encode()).json()
    assert client.delete(f"/api/resumes/{second['id']}", headers=auth_header(student_token)).status_code == 204
    assert client.get("/api/resumes/current", headers=auth_header(student_token)).json()["id"] == first["id"]


def test_resumes_are_private(client, student_token, other_student_token):
    mine = upload(client, student_token, "v1.txt", RESUME_TEXT.encode()).json()
    other = auth_header(other_student_token)
    assert client.get(f"/api/resumes/{mine['id']}", headers=other).status_code == 404
    assert client.get("/api/resumes/current", headers=other).status_code == 404
    assert client.delete(f"/api/resumes/{mine['id']}", headers=other).status_code == 404
