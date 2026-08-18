def test_text_voice_and_kyr(client, headers):
    text = client.post('/api/v1/query', json={'text': 'My employer did not pay me'}, headers=headers)
    assert text.status_code == 200 and 'your_right' in text.json()
    voice = client.post('/api/v1/query/voice', files={'file': ('question.wav', b'audio', 'audio/wav')}, headers=headers)
    assert voice.status_code == 200
    kyr = client.post('/api/v1/kyr/browse', json={'beneficiary': 'worker', 'topic': 'wages'}, headers=headers)
    assert kyr.status_code == 200
