import sys
#import and init pygame
import os
import yaml
import pygame
import datetime
import pygame.camera as Camera
import random

#define some colors
WHITE = (255, 255, 255)
BLACK = (  0,   0,   0)
BLUE  = (  0,   0, 255)
GREEN = (  0, 255,   0)
RED   = (255,   0,   0)

DEFAULT_SIZE = (900, 599)

NEW_ACQUISITION = '# New acquisition\n'

CONFIG_FILE = 'transit_cam.yaml'

CAM_RECT = pygame.Rect(0, 0, 400, 300)
plot_rect = pygame.Rect(0, 480, 200, 200)
roi = pygame.Rect(100, 100, 100, 100)
logging = False
last_logging_change = datetime.datetime.now()

YAML_LEFT = 'left'
YAML_TOP = 'top'
YAML_WIDTH = 'width'
YAML_HEIGHT = 'height'
YAML_ROI = 'roi'
YAML_OUT_FILENAME = 'out_filename'
YAML_MONOCHROME = 'monochrome'

class SimStatus(object):
    def __init__(self, cam_rect, plot_rect, screen, roi, logging, last_logging_change = datetime.datetime.now()):
        self.cam_rect = cam_rect
        self.plot_rect = plot_rect
        self.screen = screen
        self.logging = logging
        self.last_logging_change = last_logging_change
        self.last_monochrome_change = last_logging_change
        self.index = 0
        self.done = False
        # saved status
        self.roi = roi
        self.out_filename = 'transit_cam.log'
        self.monochrome = False
        
    def load_stauts(self, filename = CONFIG_FILE):
        if not os.path.isfile(filename):
            return
        with open(filename, 'r') as input:
            self.from_yaml(yaml.load(input))          
            
    def save_status(self, filename = CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as out:
            yaml.dump(self.to_yaml(), out, default_flow_style=False)

    def to_yaml(self):
        return {
            YAML_OUT_FILENAME : self.out_filename,
            YAML_ROI : self.rect_to_yaml(self.roi),
            YAML_MONOCHROME : self.monochrome
        }
        
    def from_yaml(self, yaml_node):
        if YAML_ROI in yaml_node.keys(): 
            self.roi = self.rect_from_yaml(yaml_node[YAML_ROI])
        self.out_filename = yaml_node.get(YAML_OUT_FILENAME, self.out_filename)
        self.monochrome = yaml_node.get(YAML_MONOCHROME, self.monochrome)

    def toggle_monochorome(self):
        if (datetime.datetime.now() - self.last_monochrome_change).total_seconds() > 1:
            self.last_monochrome_change = datetime.datetime.now()
            self.monochrome = not self.monochrome
            self.save_status()

    def toggle_logging(self):
        if (datetime.datetime.now() - self.last_logging_change).total_seconds() > 1:
            if self.logging:
                self.end_log()
            else:
                self.begin_log()
    
    def begin_log(self):
        self.out_file = open(self.out_filename, 'a')
        self.logging = True
        self.log(NEW_ACQUISITION)
        self.last_logging_change = datetime.datetime.now()
        
    def end_log(self):
        self.out_file.close()
        self.logging = False
        self.last_logging_change = datetime.datetime.now()

    @staticmethod
    def rect_to_yaml(rect):
        return {
            YAML_LEFT : rect.left,
            YAML_TOP : rect.top,
            YAML_WIDTH : rect.width,
            YAML_HEIGHT : rect.height,
        }

    @staticmethod
    def rect_from_yaml(yaml_node):
        return pygame.Rect(
            yaml_node.get(YAML_LEFT, 0),
            yaml_node.get(YAML_TOP, 0),
            yaml_node.get(YAML_WIDTH, 0),
            yaml_node.get(YAML_HEIGHT, 0),
            )
        
    def log(self, message):
        if self.logging:
            if self.out_file is not None: 
                self.out_file.write(message)

    def draw_roi(self):
        pygame.draw.rect(self.screen, RED if self.logging else BLUE, self.roi, 1)
        
    def move_top(self, increment):
        self.roi.top += increment
        if self.roi.top < self.cam_rect.top:
            self.roi.top = self.cam_rect.top
        if self.roi.top+self.roi.height > self.cam_rect.bottom:
            self.roi.top = (self.cam_rect.bottom - self.roi.height)
        self.save_status()

    def move_left(self, increment):
        self.roi.left += increment
        if self.roi.left < self.cam_rect.left:
            self.roi.left = self.cam_rect.left
        if self.roi.left+self.roi.width > self.cam_rect.right:
            self.roi.left = (self.cam_rect.right - self.roi.width)
        self.save_status()

    def expand_down(self, increment):
        self.roi.height += increment
        if self.roi.height < 2:
            self.roi.height = 2
        if self.roi.top+self.roi.height > self.cam_rect.bottom:
            self.roi.height = (self.cam_rect.bottom - self.roi.top)
        self.save_status()

    def expand_right(self, increment):
        self.roi.width += increment
        if self.roi.width < 2:
            self.roi.width = 2
        if self.roi.left+self.roi.width > self.cam_rect.right:
            self.roi.width = (self.cam_rect.right - self.roi.left)
        self.save_status()

    def update_regions(self, new_size):
        self.plot_rect.top = self.cam_rect.bottom
        self.plot_rect.left = self.cam_rect.left
        self.plot_rect.width = new_size[0]
        self.plot_rect.height = new_size[1] - self.plot_rect.top
        
    def increment_index(self, increment=1):
        self.index += 1
        if self.index >= self.plot_rect.width:
            self.index = 0
        
    def draw_sum(self, new_sum):
    #     print(new_sum)
        scaled = [(255. - value) * self.plot_rect.height / 255. for value in new_sum]
        if self.monochrome:
            pygame.draw.rect(self.screen, BLACK, [self.index, plot_rect.top + sum(scaled) / 3, 1, 2])
        else:
            pygame.draw.rect(self.screen, RED, [self.index, plot_rect.top + scaled[0], 1, 2])
            pygame.draw.rect(self.screen, GREEN, [self.index, plot_rect.top + scaled[1], 1, 2])
            pygame.draw.rect(self.screen, BLUE, [self.index, plot_rect.top + scaled[2], 1, 2])    
    
def handle_key_event(key, value, sim_status):
    speed = 1
    if value & pygame.KMOD_SHIFT:
        speed = 10
    if key == pygame.K_ESCAPE:
        sim_status.done = True
        return True
    elif key == pygame.K_SPACE:
        sim_status.index = 0
        sim_status.screen.fill(WHITE)
        return True
    elif key == pygame.K_l:
        sim_status.toggle_logging()
        return True 
    elif key == pygame.K_m:
        sim_status.toggle_monochorome()
        return True 
    elif key == pygame.K_RCTRL or key == pygame.K_LCTRL or key == pygame.K_LSHIFT or key == pygame.K_RSHIFT:
        return True
    # handle arrow keys
    elif key == pygame.K_RIGHT:
        if value & pygame.KMOD_CTRL:
            sim_status.expand_right(speed)
        else:
            sim_status.move_left(speed)
        return True    
    elif key == pygame.K_LEFT:
        if value & pygame.KMOD_CTRL:
            sim_status.expand_right(-speed)
        else:
            sim_status.move_left(-speed)
        return True    
    elif key == pygame.K_DOWN:
        if value & pygame.KMOD_CTRL:
            sim_status.expand_down(speed)
        else:
            sim_status.move_top(speed)
        return True    
    elif key == pygame.K_UP:
        if value & pygame.KMOD_CTRL:
            sim_status.expand_down(-speed)
        else:
            sim_status.move_top(-speed)
        return True    
    return False
    
def compute_sum(surface):
    pixel_array = pygame.PixelArray(surface)
    rect = pixel_array.shape
    num_pixels = rect[0] * rect[1]
    r_sum, g_sum, b_sum = (0., 0., 0.)
    for x in range(rect[0]):
        for y in range(rect[1]):
            value = pixel_array[x, y]
            r_sum += (value & 0xFF0000) / 0x10000
            g_sum += (value & 0x00FF00) / 0x100
            b_sum += value & 0x0000FF
    return (r_sum/num_pixels, g_sum/num_pixels, b_sum/num_pixels)                

def main():
    pygame.init() 
    Camera.init()
    for camera in Camera.list_cameras():
        print(camera)
    camera = Camera.Camera(Camera.list_cameras()[0])
    camera.start()
    
    #create the screen
    size = DEFAULT_SIZE
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    regions_updated = False
    
    pygame.display.set_caption("transit_cam")
    
    # loop until the end
    done = False
    
    # init the clock
    clock = pygame.time.Clock()
    
    pressed_keys = dict()
    
    sim_status = SimStatus(CAM_RECT, plot_rect, screen, roi, logging, datetime.datetime.now())
    sim_status.load_stauts()

    # Clear the screen
    screen.fill(WHITE)
    
    # ----------- Main program loop -----------
    while not sim_status.done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("User asked to quit")
                done = True
            elif event.type == pygame.VIDEORESIZE:
                print('Video resized')
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                size = screen.get_size()
                print(size)
                sim_status.update_regions(size)
                # Clear the screen
                screen.fill(WHITE)
            elif event.type == pygame.KEYDOWN:
                pressed_keys[event.key] = event.mod
            elif event.type == pygame.KEYUP:
                del pressed_keys[event.key]
#                 print("User released a key")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                print("User pressed a mouse button")
          
        # --- App logic
        img = camera.get_image()
        timestamp = datetime.datetime.now()
        if not regions_updated:
            sim_status.cam_rect.width = img.get_size()[0]
            sim_status.cam_rect.height = img.get_size()[1]
            sim_status.update_regions(size)
            regions_updated = True
        
        # respond to pressed keys
        for key, value in pressed_keys.items():
            if handle_key_event(key, value, sim_status):
                continue
            # if an unhandled key is pressed, acquisition is reset                
            screen.fill(WHITE)
            sim_status.index = 0
            sim_status.log(NEW_ACQUISITION) 

        # --- Drawing code
        screen.blit(img, sim_status.cam_rect)
        subsurface = screen.subsurface(sim_status.roi)
        new_sum = compute_sum(subsurface)
        sim_status.log('{} {}\n'.format(timestamp, new_sum))
        sim_status.draw_roi()
        sim_status.draw_sum(new_sum)
        
        sim_status.increment_index()
        
        # --- update the screen
        pygame.display.flip()
        
        clock.tick(60) 
    
    pygame.quit()

if __name__ == '__main__':
    main()