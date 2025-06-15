

from abc import ABC, abstractmethod
from typing import Callable, Optional

import pygame
from pygame.event import Event


class KeyRegistry(ABC):

    @abstractmethod
    def register_key(
        self,
        key: int,
        action: Callable[[], None],
        key_up_action: Optional[Callable[[], None]] = None
    ) -> None:
        pass


class KeyEventHandler(ABC):

    @abstractmethod
    def handle_key_event(self, event: pygame.event.Event) -> None:
        pass


class UnknownEventError(Exception):
    pass

class KeyRegistryImpl(KeyRegistry, KeyEventHandler):

    def __init__(self) -> None:
        self._key_down_map: dict[int, Callable[[], None]] = {}
        self._key_up_map: dict[int, Callable[[], None]] = {}

    def register_key(
        self,
        key: int,
        action: Callable[[], None],
        key_up_action: Callable[[], None] | None = None
    ) -> None:
        self._key_down_map[key] = action
        if key_up_action is None:
            return
        self._key_up_map[key] = key_up_action

    def handle_key_event(self, event: Event) -> None:
        if event.type == pygame.KEYUP:
            action_map = self._key_up_map
        elif event.type == pygame.KEYDOWN:
            action_map = self._key_down_map
        else:
            raise UnknownEventError(f"KeyRegistryImpl.handle_key_event was called with unknown event with type {event.type}.")
        key: int = event.key
        if key not in action_map:
            return
        action_map[key]()
