
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
import uuid

# ===============================
# Interfaces & Enums
# ===============================

class ISubscriber(ABC):
    @abstractmethod
    def notify(self, message: str) -> None:
        pass


class NotificationType(Enum):
    FRIEND_REQUEST = 1
    FRIEND_REQUEST_ACCEPTED = 2
    LIKE = 3
    COMMENT = 4
    MENTION = 5


# ===============================
# Core Entities
# ===============================

class Comment:
    def __init__(self, id: str, user_id: str, post_id: str, content: str):
        self.id: str = id
        self.user_id: str = user_id
        self.post_id: str = post_id
        self.content: str = content
        self.timestamp: datetime = datetime.now()


class Notification:
    def __init__(self, id: str, user_id: str, notification_type: NotificationType, content: str):
        self.id: str = id
        self.user_id: str = user_id
        self.type: NotificationType = notification_type
        self.content: str = content
        self.timestamp: datetime = datetime.now()


class User:
    def __init__(self, id: str, name: str, email: str, password: str):
        self.id: str = id
        self.name: str = name
        self.email: str = email
        self.password: str = password
        self.friends: List[str] = []
        self.posts: List['Post'] = []

    def add_friend(self, user_id: str) -> None:
        if user_id not in self.friends:
            self.friends.append(user_id)

    def add_post(self, post: 'Post') -> None:
        self.posts.append(post)


# ===============================
# Observer + Post
# ===============================

class Observable:
    def __init__(self):
        self.subscribers: List[ISubscriber] = []

    def subscribe(self, subscriber: ISubscriber) -> None:
        self.subscribers.append(subscriber)

    def notify_all(self, message: str) -> None:
        for subscriber in self.subscribers:
            subscriber.notify(message)


class Post(Observable):
    def __init__(self, id: str, user_id: str, content: str):
        super().__init__()
        self.id: str = id
        self.user_id: str = user_id
        self.content: str = content
        self.timestamp: datetime = datetime.now()
        self.likes: List[str] = []
        self.comments: List[Comment] = []

    def like(self, user_id: str) -> None:
        if user_id not in self.likes:
            self.likes.append(user_id)
            self.notify_all(f"Your post was liked by {user_id}")

    def add_comment(self, comment: Comment) -> None:
        self.comments.append(comment)
        self.notify_all(f"Your post received a comment from {comment.user_id}")


# ===============================
# Notification Service
# ===============================

class NotificationService(ISubscriber):
    def __init__(self):
        self.notifications: Dict[str, List[Notification]] = {}

    def notify(self, message: str) -> None:
        print(f"[NOTIFY] {message}")

    def add_notification(self, user_id: str, notification: Notification) -> None:
        if user_id not in self.notifications:
            self.notifications[user_id] = []
        self.notifications[user_id].append(notification)

    def get_notifications(self, user_id: str) -> List[Notification]:
        return self.notifications.get(user_id, [])


# ===============================
# Feed Provider
# ===============================

class IFeedProvider(ABC):
    @abstractmethod
    def get_feed(self, user_id: str) -> List[Post]:
        pass


class SimpleFeedProvider(IFeedProvider):
    def __init__(self, user_repo: 'UserRepository'):
        self.user_repo = user_repo

    def get_feed(self, user_id: str) -> List[Post]:
        user = self.user_repo.get(user_id)
        posts: List[Post] = []
        for fid in user.friends:
            friend = self.user_repo.get(fid)
            posts.extend(friend.posts)
        posts.extend(user.posts)
        return sorted(posts, key=lambda x: x.timestamp, reverse=True)


# ===============================
# User Repository
# ===============================

class UserRepository:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def add(self, user: User) -> None:
        self.users[user.id] = user

    def get(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def find_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None


# ===============================
# User Service
# ===============================

class UserService:
    def __init__(self, user_repo: UserRepository, notification_service: NotificationService):
        self.user_repo = user_repo
        self.notification_service = notification_service

    def register(self, user: User) -> None:
        self.user_repo.add(user)

    def login(self, email: str, password: str) -> Optional[User]:
        user = self.user_repo.find_by_email(email)
        return user if user and user.password == password else None

    def send_friend_request(self, sender_id: str, receiver_id: str) -> None:
        receiver = self.user_repo.get(receiver_id)
        if receiver:
            notification = Notification(str(uuid.uuid4()), receiver.id, NotificationType.FRIEND_REQUEST,
                                        f"Friend request from {sender_id}")
            self.notification_service.add_notification(receiver.id, notification)

    def accept_friend_request(self, user_id: str, friend_id: str) -> None:
        user = self.user_repo.get(user_id)
        friend = self.user_repo.get(friend_id)
        if user and friend:
            user.add_friend(friend_id)
            friend.add_friend(user_id)
            notification = Notification(str(uuid.uuid4()), friend_id, NotificationType.FRIEND_REQUEST_ACCEPTED,
                                        f"Friend request accepted by {user_id}")
            self.notification_service.add_notification(friend_id, notification)


# ===============================
# Post Service
# ===============================

class PostService:
    def __init__(self, user_repo: UserRepository, notification_service: NotificationService):
        self.user_repo = user_repo
        self.notification_service = notification_service

    def create_post(self, user_id: str, content: str) -> Post:
        post = Post(str(uuid.uuid4()), user_id, content)
        post.subscribe(self.notification_service)
        user = self.user_repo.get(user_id)
        user.add_post(post)
        return post

    def like_post(self, user_id: str, post: Post) -> None:
        post.like(user_id)

    def comment_on_post(self, post: Post, comment: Comment) -> None:
        post.add_comment(comment)


# ===============================
# Feed Service
# ===============================

class FeedService:
    def __init__(self, feed_provider: IFeedProvider):
        self.feed_provider = feed_provider

    def get_newsfeed(self, user_id: str) -> List[Post]:
        return self.feed_provider.get_feed(user_id)


# ===============================
# Testing Example
# ===============================

if __name__ == "__main__":
    user_repo = UserRepository()
    notification_service = NotificationService()
    feed_provider = SimpleFeedProvider(user_repo)

    user_service = UserService(user_repo, notification_service)
    post_service = PostService(user_repo, notification_service)
    feed_service = FeedService(feed_provider)

    # Create and register users
    user1 = User("1", "Alice", "alice@example.com", "pass")
    user2 = User("2", "Bob", "bob@example.com", "pass")
    user_service.register(user1)
    user_service.register(user2)

    # Send and accept friend request
    user_service.send_friend_request("1", "2")
    user_service.accept_friend_request("2", "1")

    # Create post and like/comment
    post = post_service.create_post("1", "Hello World!")
    post_service.like_post("2", post)
    comment = Comment("c1", "2", post.id, "Nice post!")
    post_service.comment_on_post(post, comment)

    # Fetch and print newsfeed
    feed = feed_service.get_newsfeed("2")
    for p in feed:
        print(f"Post by {p.user_id}: {p.content}")

    # Show notifications
    print("Notifications for User 1:")
    for n in notification_service.get_notifications("1"):
        print(f"- {n.content}")

    print("Notifications for User 2:")
    for n in notification_service.get_notifications("2"):
        print(f"- {n.content}")
