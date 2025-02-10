
import logging
import os
from math import pi, sin

import pygame
import yaml
from yaml import SafeLoader

from transit_cam.colors import BLACK, WHITE

DEFAULT_SIZE = (900, 600)

SIZE_STEP = 1

YAML_AMPLITUDE = 'Amplitude'
YAML_STAR = 'Star'
YAML_SPOT = 'Spot'
YAML_PULSATING = 'Pulsating'
YAML_SPOT_VISIBLE = 'Spot Visible'
YAML_PERIOD = 'Period'
YAML_LEFT = 'Left'
YAML_TOP = 'Top'
YAML_WIDTH = 'Width'
YAML_HEIGHT = 'Height'

CONFIG_FILE = 'star_generator.yaml'


class Rect(pygame.Rect):

    def __init__(self, left: int, top: int, width: int, height: int) -> None:
        pygame.Rect.__init__(self, left, top, width, height)

    def to_yaml(self):
        return {
            YAML_LEFT: self.left,
            YAML_TOP: self.top,
            YAML_WIDTH: self.width,
            YAML_HEIGHT: self.height,
        }

    def enlarged(self, step: int) -> 'Rect':
        return Rect(
            self.left - step,
            self.top - step,
            self.width + 2 * step,
            self.height + 2 * step,
        )

    def reduced(self, step: int) -> 'Rect':
        if self.width > 2 * step and self.height > 2 * step:
            return Rect(
                self.left + step,
                self.top + step,
                self.width - 2 * step,
                self.height - 2 * step,
            )
        return self

    def widened(self, step: int) -> 'Rect':
        return Rect(
            self.left - step,
            self.top,
            self.width + 2 * step,
            self.height,
        )

    def narrowed(self, step: int) -> 'Rect':
        if self.width > 2 * step:
            return Rect(
                self.left + step,
                self.top,
                self.width - 2 * step,
                self.height,
            )
        return self

    def rounded(self) -> 'Rect':
        return Rect(
            self.left + (self.width - self.height) // 2,
            self.top,
            self.height,
            self.height,
        )

    @staticmethod
    def from_yaml(yaml_node: dict[str, int]) -> 'Rect':
        if yaml_node is None:
            return Rect(left=0, top=0, width=0, height=0)
        return Rect(
            yaml_node.get(YAML_LEFT, 0),
            yaml_node.get(YAML_TOP, 0),
            yaml_node.get(YAML_WIDTH, 0),
            yaml_node.get(YAML_HEIGHT, 0),
        )

    @staticmethod
    def get_default_star(size) -> 'Rect':
        return Rect(
            size[0] / 2 - min(size) / 4,
            size[1] / 2 - min(size) / 4,
            min(size) / 2,
            min(size) / 2,
        )

    @staticmethod
    def get_default_spot(size) -> 'Rect':
        default_star = Rect.get_default_star(size)
        return Rect(
            default_star.left + default_star.width // 4,
            default_star.top + default_star.height // 4,
            default_star.width // 2,
            default_star.height // 2,
        )


class StarGeneratorState:

    def __init__(
        self,
        screen_size: tuple[int, int] = DEFAULT_SIZE,
        star: Rect = Rect.get_default_star(DEFAULT_SIZE),
        spot: Rect = Rect.get_default_spot(DEFAULT_SIZE)
    ):
        self._logger = logging.getLogger("transit_cam.StarGeneratorState")
        self.done = False
        self.screen_size = screen_size
        self.pressed_keys = dict()
        self.screen = None
        self.framed = True

        self.star = star
        self.spot = spot
        self.pulsating = False
        self.spot_visible = False
        self.amplitude = 20
        self.period = 1000

    @property
    def screen(self):
        return self._screen

    @screen.setter
    def screen(self, screen):
        if screen is None:
            return

        if not isinstance(screen, pygame.Surface):
            raise ValueError('screen has to be of type Surface')

        self._screen = screen
        self.screen_size = screen.get_size()
        self.update_regions(self.screen_size)

    def to_yaml(self):
        return {
            YAML_AMPLITUDE: self.amplitude,
            YAML_STAR: self.star.to_yaml(),
            YAML_SPOT: self.spot.to_yaml(),
            YAML_PULSATING: self.pulsating,
            YAML_SPOT_VISIBLE: self.spot_visible,
            YAML_PERIOD: self.period,
        }

    @staticmethod
    def from_yaml(yaml_node):
        result = StarGeneratorState(
            DEFAULT_SIZE, Rect.get_default_star(DEFAULT_SIZE))

        result.amplitude = yaml_node.get(YAML_AMPLITUDE, result.amplitude)
        result.pulsating = yaml_node.get(YAML_PULSATING, result.pulsating)
        result.spot_visible = yaml_node.get(
            YAML_SPOT_VISIBLE, result.spot_visible)
        result.period = yaml_node.get(YAML_PERIOD, result.period)
        if YAML_STAR in yaml_node.keys():
            result.star = Rect.from_yaml(yaml_node[YAML_STAR])
        if YAML_SPOT in yaml_node.keys():
            result.spot = Rect.from_yaml(yaml_node[YAML_SPOT])

        return result

    def save_state(self):
        with open(CONFIG_FILE, 'w') as out:
            yaml.dump(self.to_yaml(), out, default_flow_style=False)

    @staticmethod
    def load_state():
        if not os.path.isfile(CONFIG_FILE):
            return StarGeneratorState()
        with open(CONFIG_FILE, 'r') as in_file:
            return StarGeneratorState.from_yaml(yaml.load(in_file, Loader=SafeLoader))

    def update_screen(self):
        if self.framed:
            self.screen = pygame.display.set_mode(
                self.screen_size, pygame.RESIZABLE)
        else:
            self.screen = pygame.display.set_mode(
                self.screen_size, pygame.RESIZABLE | pygame.NOFRAME)

    def toggle_frame(self):
        self._logger.debug('Toggling frame')
        self.framed = not self.framed
        self.update_screen()
        self.save_state()

    def increase_amplitude(self):
        self._logger.debug('Increasing amplitude')
        self.amplitude += SIZE_STEP
        self.save_state()

    def reset_amplitude(self):
        self._logger.debug('Resetting amplitude')
        self.amplitude = 20
        self.save_state()

    def decrease_amplitude(self):
        self._logger.debug('Decreasing amplitude')
        if self.amplitude > SIZE_STEP:
            self.amplitude -= SIZE_STEP
        self.save_state()

    def toggle_pulsation(self):
        self._logger.debug('Toggling pulsation')
        self.pulsating = not self.pulsating
        self.save_state()

    def toggle_spot(self):
        self._logger.debug('Toggling pulsation')
        self.spot_visible = not self.spot_visible
        self.save_state()

    def reduce_star(self):
        self._logger.debug('Reducing star')
        self.star = self.star.reduced(SIZE_STEP)
        self.save_state()

    def enlarge_star(self):
        self._logger.debug('Enlarging star')
        self.star = self.star.enlarged(SIZE_STEP)
        self.save_state()

    def widen_star(self):
        self._logger.debug('Widening star')
        self.star = self.star.widened(SIZE_STEP)
        self.save_state()

    def narrow_star(self):
        self._logger.debug('Narrowing star')
        self.star = self.star.narrowed(SIZE_STEP)
        self.save_state()

    def reduce_spot(self):
        self._logger.debug('Reducing spot')
        self.spot = self.spot.reduced(SIZE_STEP)
        self.save_state()

    def enlarge_spot(self):
        self._logger.debug('Enlarging spot')
        self.spot = self.spot.enlarged(SIZE_STEP)
        self.save_state()

    def widen_spot(self):
        self._logger.debug('Widening spot')
        self.spot = self.spot.widened(SIZE_STEP)
        self.save_state()

    def narrow_spot(self):
        self._logger.debug('Narrowing spot')
        self.spot = self.spot.narrowed(SIZE_STEP)
        self.save_state()

    def move_spot_left(self):
        self._logger.debug('Moving spot left')
        if self.spot.left > 2 * SIZE_STEP:
            self.spot.left -= 2 * SIZE_STEP
        self.save_state()

    def move_spot_right(self):
        self._logger.debug('Moving spot right')
        if self.spot.right < self.screen_size[0] - 2 * SIZE_STEP:
            self.spot.left += 2 * SIZE_STEP
        self.save_state()

    def move_spot_up(self):
        self._logger.debug('Moving spot up')
        if self.spot.top > 2 * SIZE_STEP:
            self.spot.top -= 2 * SIZE_STEP
        self.save_state()

    def move_spot_down(self):
        self._logger.debug('Moving spot down')
        if self.spot.bottom < self.screen_size[1] - 2 * SIZE_STEP:
            self.spot.top += 2 * SIZE_STEP
        self.save_state()

    def reset_star(self):
        self._logger.debug('Resetting star')
        self.star = Rect.get_default_star(self.screen_size)
        self.save_state()

    def reset_spot(self):
        self._logger.debug('Resetting spot')
        self.spot = Rect.get_default_spot(self.screen_size)
        self.save_state()

    def make_star_round(self):
        self._logger.debug('Rounding star')
        self.star = self.star.rounded()
        self.save_state()

    def make_spot_round(self):
        self._logger.debug('Rounding spot')
        self.spot = self.spot.rounded()
        self.save_state()

    def handle_key_up_event(self, key: int) -> None:
        self._logger.debug('Released key %s', key)
        if key in self.pressed_keys.keys():
            del self.pressed_keys[key]
        self.trigger_key_events()

    def handle_key_down_event(self, key: int, key_mod: int):
        # if value contains the NUM pad modifier, remove it,
        # because the code in trigger_key_events compares
        # against values without NUM pad modifier.
        key_mod -= (key_mod & pygame.KMOD_NUM)
        self._logger.debug('Pressed key %s with value %s', key, key_mod)
        self.pressed_keys[key] = key_mod
        self.trigger_key_events()

    def trigger_key_events(self) -> None:
        # if pressed escape, quit
        if self.pressed_keys.get(pygame.K_ESCAPE, None) in [0]:
            self.done = True
        # if pressed Alt+F4, quit
        elif self.pressed_keys.get(pygame.K_F4, None) in [pygame.KMOD_RALT, pygame.KMOD_LALT]:
            self.done = True
        #
        # Frame
        #
        # if pressed 'f', toggle frame
        elif self.pressed_keys.get(pygame.K_f, None) == 0:
            self.toggle_frame()
            del self.pressed_keys[pygame.K_f]
        #
        # Star size
        #
        # if pressed down, reduce size
        elif self.pressed_keys.get(pygame.K_DOWN, None) == 0:
            self.reduce_star()
        # if pressed up, increase size
        elif self.pressed_keys.get(pygame.K_UP, None) == 0:
            self.enlarge_star()
        # if pressed left, increase width
        elif self.pressed_keys.get(pygame.K_LEFT, None) == 0:
            self.widen_star()
        # if pressed right, reduce width
        elif self.pressed_keys.get(pygame.K_RIGHT, None) == 0:
            self.narrow_star()
        # if pressed 'r', make round
        elif self.pressed_keys.get(pygame.K_r, None) == 0:
            self.make_star_round()
            del self.pressed_keys[pygame.K_r]
        # if pressed 'Ctrl+Shift+Down', reset size
        elif self.pressed_keys.get(pygame.K_DOWN, None) in [pygame.KMOD_LCTRL | pygame.KMOD_LSHIFT,
                                                            pygame.KMOD_RCTRL | pygame.KMOD_RSHIFT]:
            self.reset_star()
            del self.pressed_keys[pygame.K_DOWN]
        #
        # Spot size
        #
        # if pressed Alt+down, reduce spot size
        elif self.pressed_keys.get(pygame.K_DOWN, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.reduce_spot()
        # if pressed Alt+up, increase spot size
        elif self.pressed_keys.get(pygame.K_UP, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.enlarge_spot()
        # if pressed Alt+left, increase spot width
        elif self.pressed_keys.get(pygame.K_LEFT, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.widen_spot()
        # if pressed Alt+right, reduce spot width
        elif self.pressed_keys.get(pygame.K_RIGHT, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.narrow_spot()
        # if pressed 'Alt+r', make round
        elif self.pressed_keys.get(pygame.K_r, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.make_spot_round()
            del self.pressed_keys[pygame.K_r]
        # if pressed 'Ctrl+Alt+Shift+Down', reset size
        elif self.pressed_keys.get(pygame.K_DOWN, None) in [pygame.KMOD_LCTRL | pygame.KMOD_LALT | pygame.KMOD_LSHIFT,
                                                            pygame.KMOD_RCTRL | pygame.KMOD_RALT | pygame.KMOD_RSHIFT]:
            self.reset_spot()
            del self.pressed_keys[pygame.K_DOWN]
        ###
        # Spot position
        ###
        # if pressed Alt+u, move spot up
        elif self.pressed_keys.get(pygame.K_u, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.move_spot_up()
        # if pressed Alt+j, move spot down
        elif self.pressed_keys.get(pygame.K_j, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.move_spot_down()
        # if pressed Alt+h, move spot left
        elif self.pressed_keys.get(pygame.K_h, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.move_spot_left()
        # if pressed Alt+k, move spot up
        elif self.pressed_keys.get(pygame.K_k, None) in [pygame.KMOD_LALT, pygame.KMOD_RALT]:
            self.move_spot_right()

        #
        # Oscillation amplitude
        #
        # if pressed 'A', increase amplitude
        elif self.pressed_keys.get(pygame.K_a, None) in [pygame.KMOD_LSHIFT, pygame.KMOD_RSHIFT]:
            self.increase_amplitude()
        # if pressed 'a', increase amplitude
        elif self.pressed_keys.get(pygame.K_a, None) == 0:
            self.decrease_amplitude()
        # if pressed 'Ctrl+A', reset amplitude
        elif self.pressed_keys.get(pygame.K_a, None) in [pygame.KMOD_LCTRL, pygame.KMOD_RCTRL]:
            self.reset_amplitude()
            del self.pressed_keys[pygame.K_a]
        # if pressed 'p', toggle pulsation
        elif self.pressed_keys.get(pygame.K_p, None) == 0:
            self.toggle_pulsation()
            del self.pressed_keys[pygame.K_p]
        # if pressed 's', toggle spot
        elif self.pressed_keys.get(pygame.K_s, None) == 0:
            self.toggle_spot()
            del self.pressed_keys[pygame.K_s]

    def clear_screen(self, color):
        self.screen.fill(color)

    def draw_star(self, time):
        self.clear_screen(BLACK)
        if self.pulsating:
            amplitudes = (self.amplitude, self.amplitude)
            rect = self.sine_rect(self.star, amplitudes, time, self.period)
            spot = self.sine_rect(self.spot, amplitudes, time, self.period)
        else:
            rect = self.star
            spot = self.spot
        pygame.draw.ellipse(self.screen, WHITE, rect)
        if self.spot_visible:
            pygame.draw.ellipse(self.screen, BLACK, spot)

    @staticmethod
    def sine_rect(base_rect, amplitudes, time, period):
        ratio = 0.5 * sin(2 * pi * time / period)
        return Rect(
            base_rect.left - amplitudes[0] * ratio,
            base_rect.top - amplitudes[1] * ratio,
            base_rect.width + 2 * amplitudes[0] * ratio,
            base_rect.height + 2 * amplitudes[1] * ratio,
        )

    def update_regions(self, size):
        spot_offset = (self.spot.left - self.star.left,
                       self.spot.top - self.star.top)
        self.star.left = (size[0] - self.star.width) / 2
        self.star.top = (size[1] - self.star.height) / 2
        self.spot.left = self.star.left + spot_offset[0]
        self.spot.top = self.star.top + spot_offset[1]
