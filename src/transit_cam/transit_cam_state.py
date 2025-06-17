import logging
from pathlib import Path
import pygame.camera
from transit_cam.colors import BLACK, BLUE, GREEN, RED, WHITE


import pygame
import yaml


import datetime
import os

from transit_cam.key_events.key_registry import KeyEventHandler, KeyRegistry


YAML_LEFT = 'left'
YAML_TOP = 'top'
YAML_WIDTH = 'width'
YAML_HEIGHT = 'height'
YAML_ROI = 'roi'
YAML_OUTPUT_FOLDER = 'output_folder'
YAML_MONOCHROME = 'monochrome'

NORMAL_SPEED = 1
FAST_SPEED = 10
CONFIG_FILE = 'transit_cam.yaml'
plot_rect = pygame.Rect(0, 480, 200, 200)


class TransitCamState:

    _logger = logging.getLogger("transit_cam.TransitCamState")

    def __init__(
        self,
        key_registry: KeyRegistry,
        key_event_handler: KeyEventHandler,
        camera: pygame.camera.Camera,
        cam_rect,
        plot_rect,
        screen: pygame.Surface,
        roi,
        last_logging_change=datetime.datetime.now()
    ):
        self.cam_rect = cam_rect
        self.plot_rect = plot_rect
        self.screen = screen
        self.recording = False
        self.last_recording_change = last_logging_change
        self.last_monochrome_change = last_logging_change
        self.index = 0
        self.done = False
        # saved status
        self.roi = roi
        self.output_folder = Path("transit_cam_records")
        self.output_folder.mkdir(exist_ok=True)
        self.output_file_handle = None
        self.monochrome = False

        # Clear the screen
        screen.fill(WHITE)

        self._key_registry = key_registry
        self._key_event_handler = key_event_handler
        self._camera = camera

        self._expanding_right = False
        self._expanding_right_fast = False
        self._expanding_left = False
        self._expanding_left_fast = False
        self._expanding_up = False
        self._expanding_up_fast = False
        self._expanding_down = False
        self._expanding_down_fast = False
        self._moving_left = False
        self._moving_left_fast = False
        self._moving_right = False
        self._moving_right_fast = False
        self._moving_up = False
        self._moving_up_fast = False
        self._moving_down = False
        self._moving_down_fast = False
        self._camera_regions_initialized = False

        self._init_key_bindings()

    def _init_key_bindings(self) -> None:
        def set_done():
            self.done = True
        self._key_registry.register_key(pygame.K_ESCAPE, set_done)
        self._key_registry.register_key(
            pygame.K_SPACE, self.reset_data_display
        )
        self._key_registry.register_key(
            pygame.K_l, self.toggle_recording
        )
        self._key_registry.register_key(
            pygame.K_m, self.toggle_monochrome
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_RIGHT, self._set_expanding_right,
            required_modifiers=[pygame.KMOD_CTRL]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_RIGHT, self._set_expanding_right_fast,
            required_modifiers=[pygame.KMOD_SHIFT, pygame.KMOD_CTRL]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_LEFT, self._set_expanding_left,
            required_modifiers=[pygame.KMOD_CTRL]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_LEFT, self._set_expanding_left_fast,
            required_modifiers=[pygame.KMOD_SHIFT, pygame.KMOD_CTRL]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_UP, self._set_expanding_up,
            required_modifiers=[pygame.KMOD_CTRL]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_UP, self._set_expanding_up_fast,
            required_modifiers=[pygame.KMOD_SHIFT, pygame.KMOD_CTRL]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_DOWN, self._set_expanding_down,
            required_modifiers=[pygame.KMOD_CTRL]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_DOWN, self._set_expanding_down_fast,
            required_modifiers=[pygame.KMOD_SHIFT, pygame.KMOD_CTRL]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_RIGHT, self._set_moving_right
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_RIGHT, self._set_moving_right_fast,
            required_modifiers=[pygame.KMOD_SHIFT]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_LEFT, self._set_moving_left
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_LEFT, self._set_moving_left_fast,
            required_modifiers=[pygame.KMOD_SHIFT]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_UP, self._set_moving_up
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_UP, self._set_moving_up_fast,
            required_modifiers=[pygame.KMOD_SHIFT]
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_DOWN, self._set_moving_down
        )
        self._key_registry.register_boolean_state_setter_on_key(
            pygame.K_DOWN, self._set_moving_down_fast,
            required_modifiers=[pygame.KMOD_SHIFT]
        )

    def _set_expanding_right(self, state: bool) -> None:
        self._expanding_right = state

    def _set_expanding_right_fast(self, state: bool) -> None:
        self._expanding_right_fast = state

    def _set_expanding_left(self, state: bool) -> None:
        self._expanding_left = state

    def _set_expanding_left_fast(self, state: bool) -> None:
        self._expanding_left_fast = state

    def _set_expanding_up(self, state: bool) -> None:
        self._expanding_up = state

    def _set_expanding_up_fast(self, state: bool) -> None:
        self._expanding_up_fast = state

    def _set_expanding_down(self, state: bool) -> None:
        self._expanding_down = state

    def _set_expanding_down_fast(self, state: bool) -> None:
        self._expanding_down_fast = state

    def _set_moving_left(self, state: bool) -> None:
        self._moving_left = state

    def _set_moving_left_fast(self, state: bool) -> None:
        self._moving_left_fast = state

    def _set_moving_right(self, state: bool) -> None:
        self._moving_right = state

    def _set_moving_right_fast(self, state: bool) -> None:
        self._moving_right_fast = state

    def _set_moving_up(self, state: bool) -> None:
        self._moving_up = state

    def _set_moving_up_fast(self, state: bool) -> None:
        self._moving_up_fast = state

    def _set_moving_down(self, state: bool) -> None:
        self._moving_down = state

    def _set_moving_down_fast(self, state: bool) -> None:
        self._moving_down_fast = state

    def reset_data_display(self) -> None:
        self.index = 0
        self.screen.fill(WHITE)

    def on_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            print("User asked to quit")
        elif event.type == pygame.VIDEORESIZE:
            print('Video resized')
            screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            size = screen.get_size()
            print(size)
            self._update_regions(size)
            screen.fill(WHITE)
        elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            self._key_event_handler.handle_key_event(event)

    def on_loop(self) -> None:
        if self._expanding_right_fast:
            self._expand_horizontally(FAST_SPEED)
        elif self._expanding_right:
            self._expand_horizontally(NORMAL_SPEED)

        if self._expanding_left_fast:
            self._expand_horizontally(-FAST_SPEED)
        elif self._expanding_left:
            self._expand_horizontally(-NORMAL_SPEED)

        if self._expanding_up_fast:
            self._expand_vertically(-FAST_SPEED)
        elif self._expanding_up:
            self._expand_vertically(-NORMAL_SPEED)

        if self._expanding_down_fast:
            self._expand_vertically(FAST_SPEED)
        elif self._expanding_down:
            self._expand_vertically(NORMAL_SPEED)

        if self._moving_left_fast:
            self._move_horizontally(-FAST_SPEED)
        elif self._moving_left:
            self._move_horizontally(-NORMAL_SPEED)

        if self._moving_right_fast:
            self._move_horizontally(FAST_SPEED)
        elif self._moving_right:
            self._move_horizontally(NORMAL_SPEED)

        if self._moving_up_fast:
            self._move_vertically(-FAST_SPEED)
        elif self._moving_up:
            self._move_vertically(-NORMAL_SPEED)

        if self._moving_down_fast:
            self._move_vertically(FAST_SPEED)
        elif self._moving_down:
            self._move_vertically(NORMAL_SPEED)

        self._increment_index()

    def on_draw(self) -> None:

        # --- App logic
        img = self._camera.get_image()
        timestamp = datetime.datetime.now()
        if not self._camera_regions_initialized:
            self.cam_rect.width = img.get_size()[0]
            self.cam_rect.height = img.get_size()[1]
            self._update_regions(self.screen.get_size())
            self._camera_regions_initialized = True

        # --- Drawing code
        self.screen.blit(img, self.cam_rect)
        subsurface: pygame.Surface = self.screen.subsurface(self.roi)
        new_sum = compute_sum(subsurface)
        self.record('{} {}\n'.format(timestamp, new_sum))
        self._draw_roi()
        self.draw_sum(new_sum)

    def load_state(self, filename=CONFIG_FILE):
        if not os.path.isfile(filename):
            return
        self._logger.info("Loading state from %s", filename)
        with open(filename, 'r') as in_file:
            self.from_yaml(yaml.load(in_file, Loader=yaml.SafeLoader))

    def save_status(self):
        with open(CONFIG_FILE, 'w') as out:
            yaml.dump(self.to_yaml(), out, default_flow_style=False)

    def to_yaml(self):
        return {
            YAML_OUTPUT_FOLDER: str(self.output_folder),
            YAML_ROI: self.rect_to_yaml(self.roi),
            YAML_MONOCHROME: self.monochrome
        }

    def from_yaml(self, yaml_node):
        if YAML_ROI in yaml_node.keys():
            self.roi = self.rect_from_yaml(yaml_node[YAML_ROI])
        self.output_folder = Path(yaml_node.get(
            YAML_OUTPUT_FOLDER, self.output_folder))
        self.monochrome = yaml_node.get(YAML_MONOCHROME, self.monochrome)

    def toggle_monochrome(self):
        if (datetime.datetime.now() - self.last_monochrome_change).total_seconds() > 1:
            self.last_monochrome_change = datetime.datetime.now()
            self.monochrome = not self.monochrome
            self.save_status()

    def toggle_recording(self):
        if (datetime.datetime.now() - self.last_recording_change).total_seconds() > 1:
            if self.recording:
                self.end_record()
            else:
                self.begin_record()

    def begin_record(self):
        now_str: str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = self.output_folder / f"{now_str}_transit_cam.log"
        self._logger.info("Recording light intensity in %s", file_path)
        self.output_file_handle = open(file_path, 'w')
        self.recording = True
        self.last_recording_change = datetime.datetime.now()

    def end_record(self) -> None:
        if self.output_file_handle is None:
            return
        self.output_file_handle.close()
        self.recording = False
        self.last_recording_change = datetime.datetime.now()

    @staticmethod
    def rect_to_yaml(rect):
        return {
            YAML_LEFT: rect.left,
            YAML_TOP: rect.top,
            YAML_WIDTH: rect.width,
            YAML_HEIGHT: rect.height,
        }

    @staticmethod
    def rect_from_yaml(yaml_node):
        return pygame.Rect(
            yaml_node.get(YAML_LEFT, 0),
            yaml_node.get(YAML_TOP, 0),
            yaml_node.get(YAML_WIDTH, 0),
            yaml_node.get(YAML_HEIGHT, 0),
        )

    def record(self, message: str) -> None:
        if self.recording:
            if self.output_file_handle is not None:
                self.output_file_handle.write(message)

    def _draw_roi(self):
        pygame.draw.rect(
            self.screen, RED if self.recording else BLUE, self.roi, 1)

    def _move_vertically(self, increment):
        self.roi.top += increment
        if self.roi.top < self.cam_rect.top:
            self.roi.top = self.cam_rect.top
        if self.roi.top+self.roi.height > self.cam_rect.bottom:
            self.roi.top = (self.cam_rect.bottom - self.roi.height)
        self.save_status()

    def _move_horizontally(self, increment):
        self.roi.left += increment
        if self.roi.left < self.cam_rect.left:
            self.roi.left = self.cam_rect.left
        if self.roi.left+self.roi.width > self.cam_rect.right:
            self.roi.left = (self.cam_rect.right - self.roi.width)
        self.save_status()

    def _expand_vertically(self, increment):
        self.roi.height += increment
        if self.roi.height < 2:
            self.roi.height = 2
        if self.roi.top+self.roi.height > self.cam_rect.bottom:
            self.roi.height = (self.cam_rect.bottom - self.roi.top)
        self.save_status()

    def _expand_horizontally(self, increment):
        self.roi.width += increment
        if self.roi.width < 2:
            self.roi.width = 2
        if self.roi.left+self.roi.width > self.cam_rect.right:
            self.roi.width = (self.cam_rect.right - self.roi.left)
        self.save_status()

    def _update_regions(self, new_size):
        self.plot_rect.top = self.cam_rect.bottom
        self.plot_rect.left = self.cam_rect.left
        self.plot_rect.width = new_size[0]
        self.plot_rect.height = new_size[1] - self.plot_rect.top

    def _increment_index(self, increment=1):
        self.index += increment
        if self.index >= self.plot_rect.width:
            self.index = 0

    def draw_sum(self, new_sum):
        scaled = [(255. - value) * self.plot_rect.height /
                  255. for value in new_sum]
        if self.monochrome:
            pygame.draw.rect(self.screen, BLACK, [
                             self.index, plot_rect.top + sum(scaled) / 3, 1, 2])
        else:
            pygame.draw.rect(self.screen, RED, [
                             self.index, plot_rect.top + scaled[0], 1, 2])
            pygame.draw.rect(self.screen, GREEN, [
                             self.index, plot_rect.top + scaled[1], 1, 2])
            pygame.draw.rect(self.screen, BLUE, [
                             self.index, plot_rect.top + scaled[2], 1, 2])


def compute_sum(surface: pygame.Surface) -> tuple[float, float, float]:
    pixel_array = pygame.PixelArray(surface)
    rect = pixel_array.shape
    num_pixels = rect[0] * rect[1]
    r_sum, g_sum, b_sum = (0., 0., 0.)
    for x in range(rect[0]):
        for y in range(rect[1]):
            value = pixel_array[x, y]  # type: ignore
            r_sum += (value & 0xFF0000) / 0x10000
            g_sum += (value & 0x00FF00) / 0x100
            b_sum += value & 0x0000FF
    return r_sum/num_pixels, g_sum/num_pixels, b_sum/num_pixels
