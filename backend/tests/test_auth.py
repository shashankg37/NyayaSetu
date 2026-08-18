def test_registration_always_creates_citizen(client):
    response = client.post('/api/v1/auth/register', json={'email': 'a@example.com', 'password': 'secure-pass-123', 'role': 'admin'})
    assert response.status_code == 201
    assert response.json()['role'] == 'citizen'


def test_login_refresh_and_me(client):
    client.post('/api/v1/auth/register', json={'email': 'a@example.com', 'password': 'secure-pass-123'})
    login = client.post('/api/v1/auth/login', json={'email': 'a@example.com', 'password': 'secure-pass-123'})
    assert login.status_code == 200
    assert client.post('/api/v1/auth/refresh', json={'refresh_token': login.json()['refresh_token']}).status_code == 200
    me = client.get('/api/v1/users/me', headers={'Authorization': f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200
