import pygame

from transit_cam.colors import BLACK
from transit_cam.executables.shared_logging_setup_for_executables import init_logging, parse_logging_args
from transit_cam.star_generator_state import StarGeneratorState


def main():
    log_level = parse_logging_args()
    init_logging(log_level)
    pygame.init()

    sim_state: StarGeneratorState = StarGeneratorState.load_state()

    sim_state.update_screen()
    sim_state.clear_screen(BLACK)

    pygame.display.set_caption("star_generator")

    clock = pygame.time.Clock()

    # main loop
    while not sim_state.done:
        for event in pygame.event.get():
            sim_state.on_event(event)
        sim_state.on_loop()
        sim_state.draw_star(pygame.time.get_ticks())

        # update the screen
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()


if __name__ == '__main__':
    main()
