def test_document_upload_and_read(client, headers):
    uploaded = client.post('/api/v1/documents/upload', files={'file': ('notice.pdf', b'pretend pdf', 'application/pdf')}, headers=headers)
    assert uploaded.status_code == 201
    assert client.get(f"/api/v1/documents/{uploaded.json()['id']}", headers=headers).status_code == 200
