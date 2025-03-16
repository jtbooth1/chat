import unittest
import sqlite3
from db import DatabaseAccess, User, Topic, Conversation, Message, Page, Participant, Subscription

class TestDatabaseAccess(unittest.TestCase):
    def setUp(self):
        # Set up an in-memory SQLite database
        self.connection = sqlite3.connect(":memory:")
        self.db = DatabaseAccess(connection=self.connection)

    def tearDown(self):
        # Close the database connection
        self.connection.close()

    def test_create_user(self):
        user = self.db.create_user("test_user")
        self.assertEqual(user.username, "test_user")

    def test_get_user(self):
        user = self.db.create_user("test_user")
        fetched_user = self.db.get_user(user.id)
        self.assertEqual(fetched_user.username, "test_user")

    def test_create_topic(self):
        topic = self.db.create_topic("test_topic", "description")
        self.assertEqual(topic.name, "test_topic")

    def test_get_topic(self):
        topic = self.db.create_topic("test_topic", "description")
        fetched_topic = self.db.get_topic(topic.id)
        self.assertEqual(fetched_topic.name, "test_topic")

    def test_get_topics(self):
        self.db.create_topic("test_topic_1", "description_1")
        self.db.create_topic("test_topic_2", "description_2")
        topics = self.db.get_topics()
        self.assertEqual(len(topics), 2)

    def test_create_conversation(self):
        topic = self.db.create_topic("test_topic", "description")
        conversation = self.db.create_conversation(topic.id, "Test Conversation")
        self.assertEqual(conversation.topic_id, topic.id)
        self.assertEqual(conversation.name, "Test Conversation")  # Verify name field

    def test_get_conversation(self):
        topic = self.db.create_topic("test_topic", "description")
        conversation = self.db.create_conversation(topic.id, "Test Conversation")
        fetched_conversation = self.db.get_conversation(conversation.id)
        self.assertEqual(fetched_conversation.id, conversation.id)
        self.assertEqual(fetched_conversation.name, "Test Conversation")  # Verify name field

    def test_get_conversations_by_topic(self):
        topic = self.db.create_topic("test_topic", "description")
        self.db.create_conversation(topic.id, "Conversation 1")
        self.db.create_conversation(topic.id, "Conversation 2")
        conversations = self.db.get_conversations_by_topic(topic.id)
        self.assertEqual(len(conversations), 2)
        self.assertEqual(conversations[0].name, "Conversation 1")  # Verify name field
        self.assertEqual(conversations[1].name, "Conversation 2")  # Verify name field

    def test_add_message(self):
        user = self.db.create_user("test_user")
        topic = self.db.create_topic("test_topic", "description")
        conversation = self.db.create_conversation(topic.id, "Test Conversation")  # Added name
        message = self.db.add_message(conversation.id, user.id, "Hello, world!")
        self.assertEqual(message.content, "Hello, world!")

    def test_get_messages(self):
        user = self.db.create_user("test_user")
        topic = self.db.create_topic("test_topic", "description")
        conversation = self.db.create_conversation(topic.id, "Test Conversation")
        for i in range(15):
            self.db.add_message(conversation.id, user.id, f"Message {i + 1}")
        messages = self.db.get_messages(conversation.id, limit=5, offset=5)
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0].content, "Message 6")
        self.assertEqual(messages[0].author_name, "test_user")  # Verify author's name
        self.assertEqual(messages[4].content, "Message 10")
        self.assertEqual(messages[4].author_name, "test_user")  # Verify author's name

    def test_create_page(self):
        topic = self.db.create_topic("test_topic", "description")
        page = self.db.create_page(topic.id, "Page Title", "Page Content")
        self.assertEqual(page.title, "Page Title")

    def test_get_page(self):
        topic = self.db.create_topic("test_topic", "description")
        page = self.db.create_page(topic.id, "Page Title", "Page Content")
        fetched_page = self.db.get_page(page.id)
        self.assertEqual(fetched_page.title, "Page Title")

    def test_get_pages_by_topic(self):
        topic = self.db.create_topic("test_topic", "description")
        self.db.create_page(topic.id, "Page 1", "Content 1")
        self.db.create_page(topic.id, "Page 2", "Content 2")
        pages = self.db.get_pages_by_topic(topic.id)
        self.assertEqual(len(pages), 2)

    def test_add_participant(self):
        user = self.db.create_user("test_user")
        topic = self.db.create_topic("test_topic", "description")
        conversation = self.db.create_conversation(topic.id, "Test Conversation")
        participant = self.db.add_participant(conversation.id, user.id)
        self.assertEqual(participant.conversation_id, conversation.id)

    def test_remove_participant(self):
        user = self.db.create_user("test_user")
        topic = self.db.create_topic("test_topic", "description")
        conversation = self.db.create_conversation(topic.id, "Test Conversation")
        self.db.add_participant(conversation.id, user.id)
        self.db.remove_participant(conversation.id, user.id)
        participants = self.db.get_participants(conversation.id)
        self.assertEqual(len(participants), 0)

    def test_get_participants(self):
        user1 = self.db.create_user("user1")
        user2 = self.db.create_user("user2")
        topic = self.db.create_topic("test_topic", "description")
        conversation = self.db.create_conversation(topic.id, "Test Conversation")
        self.db.add_participant(conversation.id, user1.id)
        self.db.add_participant(conversation.id, user2.id)
        participants = self.db.get_participants(conversation.id)
        self.assertEqual(len(participants), 2)

    def test_subscribe_to_topic(self):
        user = self.db.create_user("test_user")
        topic = self.db.create_topic("test_topic", "description")
        subscription = self.db.subscribe_to_topic(topic.id, user.id)
        self.assertEqual(subscription.topic_id, topic.id)

    def test_unsubscribe_from_topic(self):
        user = self.db.create_user("test_user")
        topic = self.db.create_topic("test_topic", "description")
        self.db.subscribe_to_topic(topic.id, user.id)
        self.db.unsubscribe_from_topic(topic.id, user.id)
        subscriptions = self.db.get_subscriptions(user.id)
        self.assertEqual(len(subscriptions), 0)

    def test_get_subscriptions(self):
        user = self.db.create_user("test_user")
        topic1 = self.db.create_topic("topic1", "description1")
        topic2 = self.db.create_topic("topic2", "description2")
        self.db.subscribe_to_topic(topic1.id, user.id)
        self.db.subscribe_to_topic(topic2.id, user.id)
        subscriptions = self.db.get_subscriptions(user.id)
        self.assertEqual(len(subscriptions), 2)

    def test_get_subscribed_topics(self):
        user = self.db.create_user("test_user")
        topic1 = self.db.create_topic("topic1", "description1")
        topic2 = self.db.create_topic("topic2", "description2")
        self.db.subscribe_to_topic(topic1.id, user.id)
        self.db.subscribe_to_topic(topic2.id, user.id)
        subscribed_topics = self.db.get_subscribed_topics(user.id)
        self.assertEqual(len(subscribed_topics), 2)
        self.assertEqual(subscribed_topics[0].name, "topic1")
        self.assertEqual(subscribed_topics[1].name, "topic2")

if __name__ == "__main__":
    unittest.main()
