def test_draft_lifecycle_and_missing_fields(client, headers):
    draft = client.post('/api/v1/draft/start', json={'doc_type': 'rti_application'}, headers=headers).json()
    assert draft['missing_fields']
    missing = client.post(f"/api/v1/draft/{draft['id']}/generate", headers=headers)
    assert missing.status_code == 400 and 'missing_fields' in missing.json()['detail']
    values = {'applicant_name': 'Asha', 'address': 'Pune', 'public_authority': 'Municipal Corporation', 'information_requested': 'Road spending'}
    answered = client.post(f"/api/v1/draft/{draft['id']}/answer", json={'fields': values}, headers=headers)
    assert answered.status_code == 200
    generated = client.post(f"/api/v1/draft/{draft['id']}/generate", headers=headers)
    assert generated.status_code == 200
    assert client.get(f"/api/v1/draft/{draft['id']}/download", headers=headers).status_code == 200
