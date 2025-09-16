from rest_framework.test import APITestCase
from django.urls import reverse
from unittest.mock import patch

class HealthTests(APITestCase):
    def test_health(self):
        url = reverse('Health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Server is up!"})

class ChatTests(APITestCase):
    @patch("api.views._get_openai_client")
    def test_chat_requires_question(self, mock_client):
        url = reverse('Chat')
        response = self.client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    @patch("api.views._get_openai_client")
    def test_chat_success(self, mock_client):
        class DummyChoice:
            def __init__(self):
                self.message = type("M", (), {"content": "Hello!"})

        class DummyCompletion:
            def __init__(self):
                self.choices = [DummyChoice()]

        class DummyChatCompletions:
            def create(self, **kwargs):
                return DummyCompletion()

        class DummyChat:
            def __init__(self):
                self.completions = DummyChatCompletions()

        class DummyClient:
            def __init__(self):
                self.chat = DummyChat()

        mock_client.return_value = DummyClient()

        url = reverse('Chat')
        response = self.client.post(url, data={"question": "Hi"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("answer"), "Hello!")
