from rest_framework.test import APITestCase
from django.urls import reverse


class HealthTests(APITestCase):
    def test_health(self):
        url = reverse('Health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Server is up!"})


class AuthChatFlowTests(APITestCase):
    def test_register_login_ask_and_history(self):
        # Register
        res = self.client.post(reverse('Register'), {"username": "alice", "password": "secret123"})
        self.assertIn(res.status_code, [200, 201])

        # Login
        res = self.client.post(reverse('Login'), {"username": "alice", "password": "secret123"})
        self.assertEqual(res.status_code, 200)

        # Ask new conversation
        res = self.client.post(reverse('Ask'), {"question": "What's the weather in Paris tomorrow?"})
        self.assertIn(res.status_code, [200, 201])
        conv_id = res.data["conversation_id"]
        self.assertTrue(conv_id)
        self.assertTrue(res.data["answer"])

        # Ask follow-up using same conversation
        res2 = self.client.post(reverse('Ask'), {"question": "How about on 2025-09-01 in the same city?", "conversation_id": conv_id})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.data["conversation_id"], conv_id)

        # List conversations
        res3 = self.client.get(reverse('Conversations'))
        self.assertEqual(res3.status_code, 200)
        self.assertTrue(isinstance(res3.data, list))
        self.assertGreaterEqual(len(res3.data), 1)

        # Conversation detail
        res4 = self.client.get(reverse('ConversationDetail', args=[conv_id]))
        self.assertEqual(res4.status_code, 200)
        self.assertIn("messages", res4.data)
        self.assertGreaterEqual(len(res4.data["messages"]), 2)
