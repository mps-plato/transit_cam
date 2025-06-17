import pygame
import datetime
import pygame.camera as py_camera

from transit_cam.executables.shared_logging_setup_for_executables import init_logging, parse_logging_args
from transit_cam.key_events.key_registry import KeyRegistryImpl
from transit_cam.transit_cam_state import TransitCamState
from transit_cam.transit_cam_state import plot_rect


DEFAULT_SIZE = (900, 599)

CAM_RECT = pygame.Rect(0, 0, 400, 300)
roi = pygame.Rect(100, 100, 100, 100)
last_logging_change = datetime.datetime.now()


def main():
    log_level = parse_logging_args()
    init_logging(log_level)

    pygame.init()
    py_camera.init(None)
    for camera in py_camera.list_cameras():
        print(camera)
    camera = py_camera.Camera(py_camera.list_cameras()[0])
    camera.start()

    size = DEFAULT_SIZE
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)

    pygame.display.set_caption("transit_cam")

    clock = pygame.time.Clock()

    key_registry = KeyRegistryImpl()

    sim_state = TransitCamState(
        key_registry,
        key_registry,
        camera,
        CAM_RECT,
        plot_rect,
        screen,
        roi,
        datetime.datetime.now()
    )
    sim_state.load_state()

    while not sim_state.done:
        for event in pygame.event.get():
            sim_state.on_event(event)
        sim_state.on_loop()

        sim_state.on_draw()
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()


if __name__ == '__main__':
    main()
