from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import sqlite3

# Dataclasses for database objects
@dataclass
class User:
    id: int
    username: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

@dataclass
class Topic:
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Topic":
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

@dataclass
class Conversation:
    id: int
    topic_id: int
    name: str  # Added name field
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Conversation":
        return cls(
            id=row["id"],
            topic_id=row["topic_id"],
            name=row["name"],  # Added name field
            created_at=datetime.fromisoformat(row["created_at"])
        )

@dataclass
class Message:
    id: int
    conversation_id: int
    author_id: int
    content: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Message":
        return cls(
            id=row["id"],
            conversation_id=row["conversation_id"],
            author_id=row["author_id"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

@dataclass
class Page:
    id: int
    topic_id: int
    title: str
    content: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Page":
        return cls(
            id=row["id"],
            topic_id=row["topic_id"],
            title=row["title"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

@dataclass
class Participant:
    conversation_id: int
    user_id: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Participant":
        return cls(
            conversation_id=row["conversation_id"],
            user_id=row["user_id"]
        )

@dataclass
class Subscription:
    topic_id: int
    user_id: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Subscription":
        return cls(
            topic_id=row["topic_id"],
            user_id=row["user_id"]
        )

@dataclass
class MessageWithAuthor:
    id: int
    conversation_id: int
    author_id: int
    author_name: str
    content: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "MessageWithAuthor":
        return cls(
            id=row["id"],
            conversation_id=row["conversation_id"],
            author_id=row["author_id"],
            author_name=row["author_name"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

class TopicWithConversations:
    """Class representing a Topic with its associated Conversations."""
    
    def __init__(self, topic, conversations=None):
        self.id = topic.id
        self.name = topic.name
        self.description = topic.description
        self.conversations = conversations or []

class DatabaseAccess:
    def __init__(self, db_path: str = "", connection: Optional[sqlite3.Connection] = None, seed_data: bool = False):
        """
        Initialize the database connection. Optionally seed the database with dummy data.
        """
        if db_path and connection:
            raise ValueError("Specify either a database path or a connection, not both")
        if not db_path and not connection:
            raise ValueError("Specify either a database path or a connection")
        if db_path:
            self.connection = sqlite3.connect(db_path)
        else:
            self.connection = connection
        # if the database is not initialized, run schema.sql
        if self.connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users'").fetchone() is None:
            with open("schema.sql") as f:
                self.connection.executescript(f.read())
        self.connection.row_factory = sqlite3.Row  # Enable named access to columns

        if seed_data:
            self._seed_database()

    def _seed_database(self):
        """
        Seed the database with dummy data for testing and development.
        """
        # Check if the database is empty
        user_count = self.connection.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
        if user_count > 0:
            return  # Database is not empty, skip seeding

        # Create dummy users
        user1 = self.create_user("alice")
        user2 = self.create_user("bob")
        user3 = self.create_user("charlie")

        # Create dummy topics
        topic1 = self.create_topic("General Discussion", "A place for general chat")
        topic2 = self.create_topic("Tech Talk", "Discuss the latest in technology")
        topic3 = self.create_topic("Random Thoughts", "Anything goes here")

        # Create dummy conversations
        conversation1 = self.create_conversation(topic1.id, "General Chat")
        conversation2 = self.create_conversation(topic2.id, "Tech Updates")
        conversation3 = self.create_conversation(topic3.id, "Random Musings")

        # Add dummy messages
        self.add_message(conversation1.id, user1.id, "Hello, everyone!")
        self.add_message(conversation1.id, user2.id, "Hi Alice!")
        self.add_message(conversation2.id, user1.id, "What's the latest in tech?")
        self.add_message(conversation2.id, user3.id, "AI is taking over!")
        self.add_message(conversation3.id, user2.id, "Random thoughts are the best.")
        self.add_message(conversation3.id, user3.id, "I agree!")

        # Create dummy pages
        self.create_page(topic1.id, "Welcome", "Welcome to the General Discussion topic!")
        self.create_page(topic2.id, "Tech Trends", "A summary of the latest trends in technology.")
        self.create_page(topic3.id, "Random Ideas", "A collection of random ideas and thoughts.")

        self.add_participant(conversation1.id, user1.id)
        self.add_participant(conversation1.id, user2.id)
        self.add_participant(conversation2.id, user1.id)
        self.add_participant(conversation2.id, user3.id)
        self.add_participant(conversation3.id, user2.id)

        self.subscribe_to_topic(topic1.id, user1.id)
        self.subscribe_to_topic(topic1.id, user2.id)
        self.subscribe_to_topic(topic2.id, user1.id)
        self.subscribe_to_topic(topic2.id, user3.id)
        self.subscribe_to_topic(topic3.id, user2.id)

    def create_user(self, username: str) -> User:
        """
        Create a new user and return the User object.
        """
        query = "INSERT INTO Users (username) VALUES (?)"
        cursor = self.connection.execute(query, (username,))
        self.connection.commit()
        user_id = cursor.lastrowid
        return self.get_user(user_id)

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user by ID.
        """
        query = "SELECT * FROM Users WHERE id = ?"
        cursor = self.connection.execute(query, (user_id,))
        row = cursor.fetchone()
        if row:
            return User.from_row(row)
        return None

    def create_topic(self, name: str, description: Optional[str] = None) -> Topic:
        """
        Create a new topic and return the Topic object.
        """
        query = "INSERT INTO Topics (name, description) VALUES (?, ?)"
        cursor = self.connection.execute(query, (name, description))
        self.connection.commit()
        topic_id = cursor.lastrowid
        return self.get_topic(topic_id)

    def get_topic(self, topic_id: int) -> Optional[Topic]:
        """
        Retrieve a topic by ID.
        """
        query = "SELECT * FROM Topics WHERE id = ?"
        cursor = self.connection.execute(query, (topic_id,))
        row = cursor.fetchone()
        if row:
            return Topic.from_row(row)
        return None

    def get_topics(self) -> List[Topic]:
        """
        Retrieve all topics.
        """
        query = "SELECT * FROM Topics"
        cursor = self.connection.execute(query)
        rows = cursor.fetchall()
        return [Topic.from_row(row) for row in rows]

    def create_conversation(self, topic_id: int, name: str) -> Conversation:
        """
        Create a new conversation under a topic and return the Conversation object.
        """
        query = "INSERT INTO Conversations (topic_id, name) VALUES (?, ?)"
        cursor = self.connection.execute(query, (topic_id, name))
        self.connection.commit()
        conversation_id = cursor.lastrowid
        return self.get_conversation(conversation_id)

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID.
        """
        query = "SELECT * FROM Conversations WHERE id = ?"
        cursor = self.connection.execute(query, (conversation_id,))
        row = cursor.fetchone()
        if row:
            return Conversation.from_row(row)
        return None

    def get_conversations_by_topic(self, topic_id: int) -> List[Conversation]:
        """
        Retrieve all conversations under a specific topic.
        """
        query = "SELECT * FROM Conversations WHERE topic_id = ? ORDER BY created_at ASC"
        cursor = self.connection.execute(query, (topic_id,))
        rows = cursor.fetchall()
        return [Conversation.from_row(row) for row in rows]

    def add_message(self, conversation_id: int, author_id: int, content: str) -> Message:
        """
        Add a message to a conversation and return the Message object.
        """
        query = "INSERT INTO Messages (conversation_id, author_id, content) VALUES (?, ?, ?)"
        cursor = self.connection.execute(query, (conversation_id, author_id, content))
        self.connection.commit()
        message_id = cursor.lastrowid
        query = "SELECT * FROM Messages WHERE id = ?"
        row = self.connection.execute(query, (message_id,)).fetchone()
        return Message.from_row(row)

    def get_messages(self, conversation_id: int, limit: int, offset: int) -> List[MessageWithAuthor]:
        """
        Retrieve messages for a conversation with pagination, including the author's name.
        """
        query = """
        SELECT Messages.*, Users.username AS author_name
        FROM Messages
        INNER JOIN Users ON Messages.author_id = Users.id
        WHERE Messages.conversation_id = ?
        ORDER BY Messages.created_at ASC
        LIMIT ? OFFSET ?
        """
        cursor = self.connection.execute(query, (conversation_id, limit, offset))
        rows = cursor.fetchall()
        return [MessageWithAuthor.from_row(row) for row in rows]

    def create_page(self, topic_id: int, title: str, content: str) -> Page:
        """
        Create a new page under a topic and return the Page object.
        """
        query = "INSERT INTO Pages (topic_id, title, content) VALUES (?, ?, ?)"
        cursor = self.connection.execute(query, (topic_id, title, content))
        self.connection.commit()
        page_id = cursor.lastrowid
        return self.get_page(page_id)

    def get_page(self, page_id: int) -> Optional[Page]:
        """
        Retrieve a page by ID.
        """
        query = "SELECT * FROM Pages WHERE id = ?"
        cursor = self.connection.execute(query, (page_id,))
        row = cursor.fetchone()
        if row:
            return Page.from_row(row)
        return None

    def get_pages_by_topic(self, topic_id: int) -> List[Page]:
        """
        Retrieve all pages under a specific topic.
        """
        query = "SELECT * FROM Pages WHERE topic_id = ? ORDER BY created_at ASC"
        cursor = self.connection.execute(query, (topic_id,))
        rows = cursor.fetchall()
        return [Page.from_row(row) for row in rows]

    def add_participant(self, conversation_id: int, user_id: int) -> Participant:
        """
        Add a participant to a conversation and return the Participant object.
        """
        query = "INSERT INTO Participants (conversation_id, user_id) VALUES (?, ?)"
        self.connection.execute(query, (conversation_id, user_id))
        self.connection.commit()
        return Participant(conversation_id=conversation_id, user_id=user_id)

    def remove_participant(self, conversation_id: int, user_id: int) -> None:
        """
        Remove a participant from a conversation.
        """
        query = "DELETE FROM Participants WHERE conversation_id = ? AND user_id = ?"
        self.connection.execute(query, (conversation_id, user_id))
        self.connection.commit()

    def get_participants(self, conversation_id: int) -> List[Participant]:
        """
        Retrieve all participants for a conversation.
        """
        query = "SELECT * FROM Participants WHERE conversation_id = ?"
        cursor = self.connection.execute(query, (conversation_id,))
        rows = cursor.fetchall()
        return [Participant.from_row(row) for row in rows]

    def subscribe_to_topic(self, topic_id: int, user_id: int) -> Subscription:
        """
        Subscribe a user to a topic and return the Subscription object.
        """
        query = "INSERT INTO Subscriptions (topic_id, user_id) VALUES (?, ?)"
        self.connection.execute(query, (topic_id, user_id))
        self.connection.commit()
        return Subscription(topic_id=topic_id, user_id=user_id)

    def unsubscribe_from_topic(self, topic_id: int, user_id: int) -> None:
        """
        Unsubscribe a user from a topic.
        """
        query = "DELETE FROM Subscriptions WHERE topic_id = ? AND user_id = ?"
        self.connection.execute(query, (topic_id, user_id))
        self.connection.commit()

    def get_subscriptions(self, user_id: int) -> List[Subscription]:
        """
        Retrieve all topics a user is subscribed to.
        """
        query = "SELECT * FROM Subscriptions WHERE user_id = ?"
        cursor = self.connection.execute(query, (user_id,))
        rows = cursor.fetchall()
        return [Subscription.from_row(row) for row in rows]

    def get_subscribed_topics(self, user_id: int) -> List[TopicWithConversations]:
        """
        Retrieve all topics a user is subscribed to.
        """
        query = """
        SELECT Topics.*
        FROM Topics
        INNER JOIN Subscriptions ON Topics.id = Subscriptions.topic_id
        WHERE Subscriptions.user_id = ?
        """
        cursor = self.connection.execute(query, (user_id,))
        rows = cursor.fetchall()
        topics_with_conversations = []
        for row in rows:
            topic = Topic.from_row(row)
            conversations = self.get_conversations_by_topic(topic.id)
            topic_with_conversations = TopicWithConversations(topic, conversations)
            topics_with_conversations.append(topic_with_conversations)
        return topics_with_conversations
