
from dataclasses import dataclass
import logging
import asyncio
from asyncio import CancelledError, Queue
from typing import Dict, List, Protocol
from abc import abstractmethod

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



@dataclass(eq=True, frozen=True)
class Topic():
    _name: str = 'DefaultTopic'

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

@dataclass
class EventPayload:
    content: str

@dataclass
class Event:
    topic: Topic
    payload: EventPayload
    sender: str

@dataclass
class DirectEvent(Event):
    receiver: str

@dataclass
class PublishEvent(Event):
    pass


class EventProcessor(Protocol):

    @abstractmethod
    def process_event(self, event: Event) -> None:
        """
        Any class that implements this method can be used as an event processor.
        """
        ...


@dataclass
class TopicSubscription():
    topic: Topic
    processor: EventProcessor





class EventStream:
    """An asynchronous event stream that processes events from a queue."""
    
    def __init__(self):
        """Initialize the event stream."""
        self._event_queue = Queue()
        
        self._processing_task = None
        self._stopped = asyncio.Event()

        # ProcessorName -> EventProcessor
        self._processors: Dict[str, EventProcessor] = {}

        self._subscriptions: List[TopicSubscription] = []
        self._topic_processor_map: Dict[Topic, List[EventProcessor]] = {}

    
    async def publish_event(self, event: Event) -> None:
        """Publish an event to the event stream.
        
        Args:
            event: The event to publish
        """
        await self._event_queue.put(event)
        logger.info(f"Published event: {event}")
    
    def register_processor(self, processor: EventProcessor, topics: list[Topic] = None) -> None:
        processor_name = type(processor).__name__
        if processor_name not in self._processors:
            self._processors[processor_name] = processor

        for topic in topics:
            new_subscription = TopicSubscription(topic=topic, processor=processor)
            self._subscriptions.append(new_subscription)

            if topic not in self._topic_processor_map:
                self._topic_processor_map[topic] = []

            self._topic_processor_map[topic].append(processor)

        logger.info(f"Registered {processor_name} for topics: {topics}")
    
    async def start(self) -> None:
        """Start processing events from the queue."""
        self._processing_task = asyncio.create_task(self._process_event())
        logger.info("Event stream started")
    
    async def stop(self) -> None:
        """Stop processing events immediately."""
        self._stopped.set()
        logger.info("Event stream stopped")
        await self._processing_task
    
    async def stop_when_idle(self) -> None:
        """Process all events in the queue and then stop."""
        await self._event_queue.join()
        self._stopped.set()
        await self._processing_task
    
    async def _process_event(self) -> None:
        """Process events from the queue until stopped."""
        try:
            while True:
                if self._stopped.is_set():
                    return
                try:
                    # Use a timeout to allow checking the running flag periodically
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                    
                    try:
                        if isinstance(event, DirectEvent):
                            # only sent to receiver
                            receiver_name = event.receiver
                            receiver_processor = self._processors.get(receiver_name)
                            if receiver_processor:
                                await receiver_processor.process_event(event)
                            else:
                                logger.warning(f"No processor found for receiver: {receiver_name}")
                        elif isinstance(event, PublishEvent):
                            # sent to all processors
                            topic = event.topic
                            for processor in self._topic_processor_map.get(topic):
                                await processor.process_event(event)
                        else:
                            logger.warning(f"Unknown event type: {type(event)}")
                            

                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                    finally:
                        # Mark the task as done regardless of whether processing succeeded
                        self._event_queue.task_done()
                
                except asyncio.TimeoutError:
                    # No event available within timeout, just continue the loop
                    pass
        
        except CancelledError:
            logger.info("Event processing was cancelled")
            # Re-raise to properly handle task cancellation
            raise
        except Exception as e:
            logger.error(f"Unexpected error in event processing: {e}")
    
class ExampleProcessor(EventProcessor):

    async def process_event(self, event: Event) -> None:
        logger.info(f"Processing event: {event}")
        await asyncio.sleep(1)
        logger.info(f"Finished processing event: {event}")


async def main():
    """Run an example of the event stream."""
    # Create the event stream
    event_stream = EventStream()
    

    example_processor = ExampleProcessor()
    # Register a handler
    event_stream.register_processor(example_processor, [Topic('test_topic')])
    
    # Start the event stream
    await event_stream.start()
    

    event = PublishEvent(
        topic=Topic('test_topic'), 
        payload=EventPayload(content='Hello, world!'), sender=type(example_processor).__name__
    )
    # Publish some events
    await event_stream.publish_event(event)

    # await event_stream.publish_event(Event(topic=Topic('test_topic'), payload=EventPayload(content='Another event'), sender=example_processor.__name__))
    
    # Wait a bit to allow events to be processed
    await asyncio.sleep(1)
    
    # Stop the event stream when all events are processed
    await event_stream.stop_when_idle()

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())