
import logging
import os
from math import pi, sin

import pygame
import yaml
from yaml import SafeLoader

from transit_cam.colors import BLACK, WHITE
from transit_cam.key_events.key_registry import KeyRegistryImpl

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
    _logger = logging.getLogger("transit_cam.StarGeneratorState")

    def __init__(
        self,
        screen_size: tuple[int, int] = DEFAULT_SIZE,
        star: Rect = Rect.get_default_star(DEFAULT_SIZE),
        spot: Rect = Rect.get_default_spot(DEFAULT_SIZE)
    ):
        self.done = False
        self.screen_size = screen_size
        self.pressed_keys = dict()
        self.screen = None
        self.framed = True

        self._key_registry: KeyRegistryImpl = KeyRegistryImpl()

        self.star = star
        self.spot = spot
        self.pulsating = False
        self.spot_visible = False
        self.amplitude = 20
        self.period = 1000

        self._reduce_star_is_active = False
        self._increase_star_is_active = False
        self._widen_star_is_active = False
        self._narrow_star_is_active = False
        self._reduce_spot_is_active = False
        self._increase_spot_is_active = False
        self._widen_spot_is_active = False
        self._narrow_spot_is_active = False
        self._move_spot_up_is_active = False
        self._move_spot_down_is_active = False
        self._move_spot_left_is_active = False
        self._move_spot_right_is_active = False
        self._increase_oscillation_amplitude_is_active = False
        self._decrease_oscillation_amplitude_is_active = False

        self._init_key_bindings()

    def _init_key_bindings(self) -> None:
        def set_done():
            self.done = True
        self._key_registry.register_key(pygame.K_ESCAPE, set_done)

        self._init_star_key_bindings()
        self._init_spot_key_bindings()
        self._init_oscillation_key_bindings()

    def _init_star_key_bindings(self) -> None:
        def start_reduce_star():
            self._reduce_star_is_active = True

        def stop_reduce_star():
            self._reduce_star_is_active = False

        self._key_registry.register_key(
            pygame.K_DOWN, start_reduce_star, stop_reduce_star)

        def start_increase_star():
            self._increase_star_is_active = True

        def stop_increase_star():
            self._increase_star_is_active = False

        self._key_registry.register_key(
            pygame.K_UP, start_increase_star, stop_increase_star)

        def start_widen_star():
            self._widen_star_is_active = True

        def stop_widen_star():
            self._widen_star_is_active = False

        self._key_registry.register_key(
            pygame.K_LEFT, start_widen_star, stop_widen_star)

        def start_narrow_star():
            self._narrow_star_is_active = True

        def stop_narrow_star():
            self._narrow_star_is_active = False

        self._key_registry.register_key(
            pygame.K_RIGHT, start_narrow_star, stop_narrow_star)

        self._key_registry.register_key(pygame.K_r, self.make_star_round)

        self._key_registry.register_key(
            pygame.K_DOWN, self.reset_star,
            required_modifiers=[pygame.KMOD_SHIFT, pygame.KMOD_CTRL]
        )

    def _init_spot_key_bindings(self) -> None:
        def start_reduce_spot():
            self._reduce_spot_is_active = True

        def stop_reduce_spot():
            self._reduce_spot_is_active = False

        self._key_registry.register_key(
            pygame.K_DOWN, start_reduce_spot, stop_reduce_spot,
            required_modifiers=[pygame.KMOD_ALT]
        )

        def start_increase_spot():
            self._increase_spot_is_active = True

        def stop_increase_spot():
            self._increase_spot_is_active = False

        self._key_registry.register_key(
            pygame.K_UP, start_increase_spot, stop_increase_spot,
            required_modifiers=[pygame.KMOD_ALT]
        )

        def start_widen_spot():
            self._widen_spot_is_active = True

        def stop_widen_spot():
            self._widen_spot_is_active = False

        self._key_registry.register_key(
            pygame.K_LEFT, start_widen_spot, stop_widen_spot,
            required_modifiers=[pygame.KMOD_ALT]
        )

        def start_narrow_spot():
            self._narrow_spot_is_active = True

        def stop_narrow_spot():
            self._narrow_spot_is_active = False

        self._key_registry.register_key(
            pygame.K_RIGHT, start_narrow_spot, stop_narrow_spot,
            required_modifiers=[pygame.KMOD_ALT]
        )

        self._key_registry.register_key(
            pygame.K_r, self.make_spot_round, required_modifiers=[pygame.KMOD_ALT])
        self._key_registry.register_key(
            pygame.K_DOWN, self.reset_spot,
            required_modifiers=[
                pygame.KMOD_ALT,
                pygame.KMOD_CTRL,
                pygame.KMOD_SHIFT
            ]
        )

        def start_move_spot_up():
            self._move_spot_up_is_active = True

        def stop_move_spot_up():
            self._move_spot_up_is_active = False

        self._key_registry.register_key(
            pygame.K_u, start_move_spot_up, stop_move_spot_up
        )

        def start_move_spot_down():
            self._move_spot_down_is_active = True

        def stop_move_spot_down():
            self._move_spot_down_is_active = False

        self._key_registry.register_key(
            pygame.K_j, start_move_spot_down, stop_move_spot_down,
        )

        def start_move_spot_left():
            self._move_spot_left_is_active = True

        def stop_move_spot_left():
            self._move_spot_left_is_active = False

        self._key_registry.register_key(
            pygame.K_h, start_move_spot_left, stop_move_spot_left,
        )

        def start_move_spot_right():
            self._move_spot_right_is_active = True

        def stop_move_spot_right():
            self._move_spot_right_is_active = False

        self._key_registry.register_key(
            pygame.K_k, start_move_spot_right, stop_move_spot_right,
        )

        self._key_registry.register_key(
            pygame.K_s, self.toggle_spot
        )

    def _init_oscillation_key_bindings(self):
        def start_increase_amplitude():
            self._increase_oscillation_amplitude_is_active = True

        def stop_increase_amplitude():
            self._increase_oscillation_amplitude_is_active = False

        self._key_registry.register_key(
            pygame.K_a, start_increase_amplitude, stop_increase_amplitude,
            required_modifiers=[pygame.KMOD_SHIFT]
        )

        def start_decrease_amplitude():
            self._decrease_oscillation_amplitude_is_active = True

        def stop_decrease_amplitude():
            self._decrease_oscillation_amplitude_is_active = False

        self._key_registry.register_key(
            pygame.K_a, start_decrease_amplitude, stop_decrease_amplitude
        )

        self._key_registry.register_key(
            pygame.K_a, self.reset_amplitude,
            required_modifiers=[pygame.KMOD_CTRL]
        )
        self._key_registry.register_key(
            pygame.K_p, self.toggle_pulsation
        )

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

    def on_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            print("User asked to quit")
            self.done = True
        elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            self._key_registry.handle_key_event(event)
        elif event.type == pygame.VIDEORESIZE:
            print('Video resized to {}'.format(event.size))
            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

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
            StarGeneratorState._logger.info(
                "No config file found. Creating a blank StarGeneratorState.")
            return StarGeneratorState()
        with open(CONFIG_FILE, 'r') as in_file:
            StarGeneratorState._logger.info(
                "Loading StarGeneratorState from file %s.", CONFIG_FILE)
            return StarGeneratorState.from_yaml(yaml.load(in_file, Loader=SafeLoader))

    def update_screen(self):
        if self.framed:
            self.screen = pygame.display.set_mode(
                self.screen_size, pygame.RESIZABLE)
        else:
            self.screen = pygame.display.set_mode(
                self.screen_size, pygame.RESIZABLE | pygame.NOFRAME)

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

    def on_loop(self) -> None:
        if self._reduce_star_is_active:
            self.reduce_star()
        elif self._increase_star_is_active:
            self.enlarge_star()
        elif self._widen_star_is_active:
            self.widen_star()
        elif self._narrow_star_is_active:
            self.narrow_star()

        if self._reduce_spot_is_active:
            self.reduce_spot()
        elif self._increase_spot_is_active:
            self.enlarge_spot()
        elif self._widen_spot_is_active:
            self.widen_spot()
        elif self._narrow_spot_is_active:
            self.narrow_spot()

        if self._move_spot_up_is_active:
            self.move_spot_up()
        elif self._move_spot_down_is_active:
            self.move_spot_down()
        if self._move_spot_left_is_active:
            self.move_spot_left()
        elif self._move_spot_right_is_active:
            self.move_spot_right()

        if self._increase_oscillation_amplitude_is_active:
            self.increase_amplitude()
        elif self._decrease_oscillation_amplitude_is_active:
            self.decrease_amplitude()

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
