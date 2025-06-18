

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
        self.mock_key_event.mod = 0
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

    def test_that_the_callback_for_key_K_a_that_requires_KMOD_SHIFT_is_NOT_called_when_the_event_is_KEYDOWN_K_a(self):
        mock_callback = MagicMock()
        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_a

        self.sut.register_key(pygame.K_a, mock_callback,
                              required_modifiers=[pygame.KMOD_SHIFT])
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback.assert_not_called()

    def test_that_the_callback_for_key_K_a_that_requires_MOD_SHIFT_is_called_when_the_event_is_KEYDOWN_K_a_with_KMOD_SHIFT(self):
        mock_callback = MagicMock()
        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_a
        self.mock_key_event.mod = pygame.KMOD_SHIFT

        self.sut.register_key(pygame.K_a, mock_callback,
                              required_modifiers=[pygame.KMOD_SHIFT])
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback.assert_called_once_with()

    def test_that_the_callback_for_key_K_a_that_requires_MOD_SHIFT_is_called_when_the_event_is_KEYDOWN_K_a_with_KMOD_LSHIFT(self):
        mock_callback = MagicMock()
        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_a
        self.mock_key_event.mod = pygame.KMOD_LSHIFT

        self.sut.register_key(pygame.K_a, mock_callback,
                              required_modifiers=[pygame.KMOD_SHIFT])
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback.assert_called_once_with()

    def test_that_the_callback_for_key_K_a_that_requires_MOD_SHIFT_and_MOD_CTRL_is_called_when_the_event_is_KEYDOWN_K_a_with_KMOD_LSHIFT_and_KMOD_RCTRL(self):
        mock_callback = MagicMock()
        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_a
        self.mock_key_event.mod = pygame.KMOD_LSHIFT | pygame.KMOD_RCTRL

        self.sut.register_key(pygame.K_a, mock_callback, required_modifiers=[
                              pygame.KMOD_SHIFT, pygame.KMOD_CTRL])
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback.assert_called_once_with()

    def test_that_the_callback_for_key_K_a_that_requires_MOD_SHIFT_and_MOD_CTRL_is_not_called_when_the_event_is_KEYDOWN_K_a_with_KMOD_LSHIFT(self):
        mock_callback = MagicMock()
        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_a
        self.mock_key_event.mod = pygame.KMOD_LSHIFT

        self.sut.register_key(pygame.K_a, mock_callback, required_modifiers=[
                              pygame.KMOD_SHIFT, pygame.KMOD_CTRL])
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback.assert_not_called()

    def test_that_the_callback_for_key_K_a_that_requires_MOD_SHIFT_and_MOD_CTRL_is_called_when_the_event_is_KEYDOWN_K_a_with_KMOD_LSHIFT_and_KMOD_RCTRL_and_there_is_another_registered_key_for_K_a(self):
        mock_callback_with_mod = MagicMock()
        mock_callback_without_mod = MagicMock()
        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_a
        self.mock_key_event.mod = pygame.KMOD_LSHIFT | pygame.KMOD_RCTRL

        self.sut.register_key(pygame.K_a, mock_callback_with_mod, required_modifiers=[
                              pygame.KMOD_SHIFT, pygame.KMOD_CTRL])
        self.sut.register_key(pygame.K_a, mock_callback_without_mod)
        self.sut.handle_key_event(self.mock_key_event)
        mock_callback_with_mod.assert_called_once_with()

    def test_that_the_setter_registered_for_key_K_b_is_called_with_True_on_keydown_K_b(self):
        mock_setter = MagicMock()

        self.sut.register_boolean_state_setter_on_key(
            pygame.K_b,
            setter=mock_setter
        )

        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_b

        self.sut.handle_key_event(self.mock_key_event)

        mock_setter.assert_called_once_with(True)

    def test_that_the_setter_registered_for_K_b_plus_SHIFT_and_CTRL_is_correctly_called_even_if_another_setter_for_K_b_plus_only_SHIFT_was_registered_before_it(self):
        mock_setter_both_mods = MagicMock()
        mock_setter_single_mod = MagicMock()

        self.sut.register_boolean_state_setter_on_key(
            pygame.K_b,
            mock_setter_single_mod,
            required_modifiers=[pygame.KMOD_SHIFT]
        )
        self.sut.register_boolean_state_setter_on_key(
            pygame.K_b,
            mock_setter_both_mods,
            required_modifiers=[pygame.KMOD_SHIFT, pygame.KMOD_CTRL]
        )

        self.mock_key_event.type = pygame.KEYDOWN
        self.mock_key_event.key = pygame.K_b
        self.mock_key_event.mod = pygame.KMOD_SHIFT | pygame.KMOD_CTRL

        self.sut.handle_key_event(self.mock_key_event)

        mock_setter_single_mod.assert_not_called()
        mock_setter_both_mods.assert_called_once_with(True)
