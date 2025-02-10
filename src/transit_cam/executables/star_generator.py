from argparse import ArgumentParser
import logging
import logging.config
import pygame

from transit_cam.logging_config import logging_config
from transit_cam.colors import BLACK
from transit_cam.star_generator_state import StarGeneratorState



def main():
    log_level = _parse_args()
    _init_logging(log_level)
    print(log_level)
    pygame.init()

    sim_state: StarGeneratorState = StarGeneratorState.load_state()

    sim_state.update_screen()
    sim_state.clear_screen(BLACK)

    pygame.display.set_caption("star_generator")

    clock = pygame.time.Clock()

    # main loop    
    while not sim_state.done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("User asked to quit")
                sim_state.done = True            
            elif event.type == pygame.KEYDOWN:
                sim_state.handle_key_down_event(event.key, event.mod)
            elif event.type == pygame.KEYUP:
                sim_state.handle_key_up_event(event.key)
            elif event.type == pygame.VIDEORESIZE:
                print('Video resized to {}'.format(event.size))
                sim_state.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

        sim_state.trigger_key_events()

        sim_state.draw_star(pygame.time.get_ticks())

        # update the screen
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()

def _parse_args() -> str:
    parser = ArgumentParser()
    parser.add_argument(
        "--log", 
        choices=["debug", "info", "warning", "error"], 
        default="warning", 
        dest="log_level"
    )
    args = parser.parse_args()
    return args.log_level

def _init_logging(log_level: str) -> None:
    logging.INFO
    logging_config["loggers"]["transit_cam"]["level"] = log_level.upper()
    logging_config["handlers"]["console"]["level"] = log_level.upper()
    logging.config.dictConfig(logging_config)


if __name__ == '__main__':
    main()