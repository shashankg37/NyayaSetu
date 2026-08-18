def test_timeline_and_health(client, headers):
    assert client.get('/api/v1/health').status_code == 200
    response = client.post('/api/v1/timeline/build', json={'narrative': 'I received a notice yesterday.'}, headers=headers)
    assert response.status_code == 200 and len(response.json()['events']) == 2
