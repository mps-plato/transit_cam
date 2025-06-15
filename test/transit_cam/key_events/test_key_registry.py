

import unittest
from unittest.mock import MagicMock

import pygame

from src.transit_cam.key_events.key_registry import KeyRegistryImpl, UnknownEventError


class TestKeyRegistryImpl(unittest.TestCase):

    mock_key_event: pygame.event.Event
    sut: KeyRegistryImpl

    def setUp(self) -> None:

        self.mock_key_event = MagicMock()
        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_a
        self.sut = KeyRegistryImpl()

    def test_that_the_callback_for_key_a_is_called_when_the_event_is_KEYDOWN_K_a(self):
        mock_callback = MagicMock()
        self.sut.register_key(pygame.K_a, mock_callback)
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback.assert_called_once_with()

    def test_that_the_callback_for_key_UP_is_NOT_called_when_the_event_is_KEYDOWN_K_a(self):
        mock_callback = MagicMock()
        self.sut.register_key(pygame.K_UP, mock_callback)
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback.assert_not_called()
    
    def test_that_the_callback_for_key_a_is_not_called_when_the_event_is_KEYUP_K_a(self):
        self.mock_key_event.type = pygame.KEYUP
        mock_callback = MagicMock()
        self.sut.register_key(pygame.K_a, mock_callback)
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback.assert_not_called()
        
    def test_that_the_keyup_callback_for_key_a_is_called_when_the_event_is_KEYUP_K_a(self):
        self.mock_key_event.type = pygame.KEYUP
        mock_callback = MagicMock()
        mock_keyup_callback = MagicMock()
        self.sut.register_key(pygame.K_a, mock_callback, mock_keyup_callback)
        self.sut.handle_key_event(self.mock_key_event)
        mock_keyup_callback.assert_called_once_with()

    def test_that_the_keyup_callback_for_key_b_is_NOT_called_when_the_event_is_KEYUP_K_a(self):
        self.mock_key_event.type = pygame.KEYUP
        mock_callback = MagicMock()
        mock_keyup_callback = MagicMock()
        self.sut.register_key(pygame.K_b, mock_callback, mock_keyup_callback)
        self.sut.handle_key_event(self.mock_key_event)
        mock_keyup_callback.assert_not_called()

    def test_that_handle_key_event_throws_an_UnknownEventError_if_it_is_called_with_event_type_(self):
        self.mock_key_event.type = pygame.MOUSEMOTION
        with self.assertRaises(UnknownEventError):
            self.sut.handle_key_event(self.mock_key_event)