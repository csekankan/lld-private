
# ==========================================
# ✅ Kafka-like Pub/Sub System in Python (LLD)
# ==========================================
#
# ▶️ Design Patterns Used:
# - Observer Pattern: Subscribers observe messages on topics
# - Command Pattern: Message delivery logic decoupled via threads
# - Controller Pattern: KafkaController manages coordination
#
# ▶️ Core Components:
# - Message: Encapsulates the message payload
# - ISubscriber/IPublisher: Interfaces defining contracts
# - SimpleSubscriber/SimplePublisher: Concrete implementations
# - TopicManager: Separates topic storage and operations
# - Topic: Maintains message list for a topic
# - TopicSubscriber: Tracks subscriber's position in a topic
# - TopicSubscriberController: Thread delivering messages
# - KafkaController: Coordinates topics, publishing, and delivery
#
# 🔒 Thread Safety:
# - Uses Locks + Conditions for safe waiting and notifying
# - Offset tracking for replay support
# - Message delivery via daemon threads
#
# 🎯 Interview-Ready:
# - Clean separation of concerns
# - Realistic offset reset, concurrent delivery, and topic ID tracking
# - Easily extensible for retry, ack, or partitioning

from abc import ABC, abstractmethod
from threading import Lock, Condition, Thread
from typing import List, Dict
import itertools
import time


class Message:
    def __init__(self, content: str):
        self.content = content

    def get_content(self) -> str:
        return self.content


class IPublisher(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def publish(self, topic_id: str, message: Message) -> None:
        pass


class ISubscriber(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def on_message(self, message: Message) -> None:
        pass


class SimpleSubscriber(ISubscriber):
    def __init__(self, id: str):
        self.id = id

    def get_id(self) -> str:
        return self.id

    def on_message(self, message: Message) -> None:
        print(f"Subscriber {self.id} received: {message.get_content()}")
        time.sleep(0.5)


class SimplePublisher(IPublisher):
    def __init__(self, id: str, kafka_controller: 'KafkaController'):
        self.id = id
        self.kafka_controller = kafka_controller

    def get_id(self) -> str:
        return self.id

    def publish(self, topic_id: str, message: Message) -> None:
        self.kafka_controller.publish(self, topic_id, message)
        print(f"Publisher {self.id} published: {message.get_content()} to topic {topic_id}")


class Topic:
    def __init__(self, topic_name: str, topic_id: str):
        self.topic_name = topic_name
        self.topic_id = topic_id
        self.messages: List[Message] = []
        self.lock = Lock()

    def get_topic_id(self) -> str:
        return self.topic_id

    def get_topic_name(self) -> str:
        return self.topic_name

    def add_message(self, message: Message) -> None:
        with self.lock:
            self.messages.append(message)

    def get_messages(self) -> List[Message]:
        with self.lock:
            return list(self.messages)


class TopicManager:
    def __init__(self):
        self.topics: Dict[str, Topic] = {}
        self.topic_id_counter = itertools.count(1)

    def create_topic(self, topic_name: str) -> Topic:
        topic_id = str(next(self.topic_id_counter))
        topic = Topic(topic_name, topic_id)
        self.topics[topic_id] = topic
        print(f"Created topic: {topic_name} with id: {topic_id}")
        return topic

    def get_topic(self, topic_id: str) -> Topic:
        return self.topics.get(topic_id)


class TopicSubscriber:
    # Associates a subscriber with a topic and maintains an offset and synchronization primitives
    def __init__(self, topic: Topic, subscriber: ISubscriber):
        self.topic = topic
        self.subscriber = subscriber
        self.offset = 0
        self.lock = Lock()
        self.condition = Condition(self.lock)

    def get_topic(self) -> Topic:
        return self.topic

    def get_subscriber(self) -> ISubscriber:
        return self.subscriber

    def get_offset(self) -> int:
        return self.offset

    def set_offset(self, new_offset: int) -> None:
        self.offset = new_offset


class TopicSubscriberController(Thread):
    def __init__(self, topic_subscriber: TopicSubscriber):
        super().__init__()
        self.topic_subscriber = topic_subscriber
        self.daemon = True

    def run(self):
        while True:
            with self.topic_subscriber.lock:
                while self.topic_subscriber.offset >= len(self.topic_subscriber.topic.get_messages()):
                    self.topic_subscriber.condition.wait()
                message = self.topic_subscriber.topic.get_messages()[self.topic_subscriber.offset]
                self.topic_subscriber.offset += 1
            try:
                self.topic_subscriber.get_subscriber().on_message(message)
            except Exception as e:
                print(f"[ERROR] Message processing failed: {e}")


class KafkaController:
    def __init__(self):
        self.topic_manager = TopicManager()
        self.topic_subscribers: Dict[str, List[TopicSubscriber]] = {}

    def create_topic(self, topic_name: str) -> Topic:
        topic = self.topic_manager.create_topic(topic_name)
        self.topic_subscribers[topic.get_topic_id()] = []
        return topic

    def subscribe(self, subscriber: ISubscriber, topic_id: str) -> None:
        topic = self.topic_manager.get_topic(topic_id)
        if not topic:
            print(f"[ERROR] Topic with id {topic_id} does not exist")
            return
        ts = TopicSubscriber(topic, subscriber)
        self.topic_subscribers[topic_id].append(ts)
        TopicSubscriberController(ts).start()
        print(f"Subscriber {subscriber.get_id()} subscribed to topic: {topic.get_topic_name()}")

    def publish(self, publisher: IPublisher, topic_id: str, message: Message) -> None:
        topic = self.topic_manager.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic with id {topic_id} does not exist")
        topic.add_message(message)
        for ts in self.topic_subscribers[topic_id]:
            with ts.lock:
                ts.condition.notify()
        print(f"Message \"{message.get_content()}\" published to topic: {topic.get_topic_name()}")

    def reset_offset(self, topic_id: str, subscriber: ISubscriber, new_offset: int) -> None:
        subs = self.topic_subscribers.get(topic_id, [])
        for ts in subs:
            if ts.get_subscriber().get_id() == subscriber.get_id():
                ts.set_offset(new_offset)
                with ts.lock:
                    ts.condition.notify()
                print(f"Offset for subscriber {subscriber.get_id()} on topic {ts.get_topic().get_topic_name()} reset to {new_offset}")


if __name__ == "__main__":
    kafka = KafkaController()
    topic1 = kafka.create_topic("Topic1")
    topic2 = kafka.create_topic("Topic2")

    kafka.subscribe(SimpleSubscriber("Subscriber1"), topic1.get_topic_id())
    kafka.subscribe(SimpleSubscriber("Subscriber1"), topic2.get_topic_id())
    kafka.subscribe(SimpleSubscriber("Subscriber2"), topic1.get_topic_id())
    kafka.subscribe(SimpleSubscriber("Subscriber3"), topic2.get_topic_id())

    publisher1 = SimplePublisher("Publisher1", kafka)
    publisher2 = SimplePublisher("Publisher2", kafka)

    publisher1.publish(topic1.get_topic_id(), Message("Message m1"))
    publisher1.publish(topic1.get_topic_id(), Message("Message m2"))
    publisher2.publish(topic2.get_topic_id(), Message("Message m3"))

    time.sleep(3)

    publisher2.publish(topic2.get_topic_id(), Message("Message m4"))
    publisher1.publish(topic1.get_topic_id(), Message("Message m5"))

    kafka.reset_offset(topic1.get_topic_id(), SimpleSubscriber("Subscriber1"), 0)
    time.sleep(3)
