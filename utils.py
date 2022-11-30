import pygame
from pygame.locals import *

def get_frame(self, name):
    frame = self.coord[name]['frame']
    trim_rect = Rect(frame['x'], frame['y'], frame['w'], frame['h'])
    return self.sheet.subsurface(trim_rect)

def get_frame_static(coord, sheet, name):
    frame = coord[name]['frame']
    trim_rect = Rect(frame['x'], frame['y'], frame['w'], frame['h'])
    return sheet.subsurface(trim_rect)

def snap_to_tile(x, tilesize=16):
    return tilesize * round(float(x)/tilesize)