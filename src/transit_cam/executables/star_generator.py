import pygame

# define some colors

from transit_cam.colors import BLACK
from transit_cam.star_generator_state import StarGeneratorState



def main():
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
                sim_state.handle_key_event(event.key, event.mod, True)
            elif event.type == pygame.KEYUP:
                sim_state.handle_key_event(event.key, event.mod, False)
            elif event.type == pygame.VIDEORESIZE:
                print('Video resized to {}'.format(event.size))
                sim_state.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

        sim_state.handle_key_event(None, 0, False)

        sim_state.draw_star(pygame.time.get_ticks())

        # update the screen
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()


if __name__ == '__main__':
    main()