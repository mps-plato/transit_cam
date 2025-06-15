

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

import pygame
from pygame.event import Event


class KeyRegistry(ABC):

    @abstractmethod
    def register_key(
        self,
        key: int,
        action: Callable[[], None],
        key_up_action: Optional[Callable[[], None]] = None,
        required_modifiers: int | None = None
    ) -> None:
        pass


class KeyEventHandler(ABC):

    @abstractmethod
    def handle_key_event(self, event: pygame.event.Event) -> None:
        pass


class UnknownEventError(Exception):
    pass

@dataclass(frozen=True)
class _KeyWithModifier:
    key: int
    modifier: int

class KeyRegistryImpl(KeyRegistry, KeyEventHandler):

    def __init__(self) -> None:
        self._key_down_any_modifiers_map: dict[int, Callable[[], None]] = {}
        self._key_down_with_modifiers_map: dict[_KeyWithModifier, Callable[[], None]] = {}
        self._key_up_map: dict[int, Callable[[], None]] = {}

    def register_key(
        self,
        key: int,
        action: Callable[[], None],
        key_up_action: Callable[[], None] | None = None,
        required_modifiers: int | None = None
    ) -> None:
        if required_modifiers is None:
            self._key_down_any_modifiers_map[key] = action
        else:
            self._key_down_with_modifiers_map[_KeyWithModifier(key, required_modifiers)] = action
        if key_up_action is None:
            return
        self._key_up_map[key] = key_up_action

    def handle_key_event(self, event: Event) -> None:
        if event.type == pygame.KEYUP:
            self._handle_keyup_event(event)            
        elif event.type == pygame.KEYDOWN:
            self._handle_keydown_event(event)            
        else:
            raise UnknownEventError(f"KeyRegistryImpl.handle_key_event was called with unknown event with type {event.type}.")
        
    def _handle_keyup_event(self, event: Event) -> None:        
        key: int = event.key
        if key not in self._key_up_map:
            return
        self._key_up_map[key]()

    def _handle_keydown_event(self, event: Event) -> None:
        key: int = event.key
        if key in self._key_down_any_modifiers_map:
            self._key_down_any_modifiers_map[key]()
            return
        key_with_mod = _KeyWithModifier(key, event.mod)
        if key_with_mod not in self._key_down_with_modifiers_map:
            return
        self._key_down_with_modifiers_map[key_with_mod]()
        