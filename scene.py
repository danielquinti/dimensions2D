import pygame
import os

class Scene:
    def __init__(self, director):
        self.director = director

    def update(self, *args):
        raise NotImplementedError("update method must be implemented.")

    def events(self, *args):
        raise NotImplementedError("events method must be implemented.")

    def draw(self, display):
        raise NotImplementedError("draw method must be implemented.")

    def play_music(self, name):
        pygame.mixer.music.stop()
        pygame.mixer.music.load(os.path.join('assets/music/',name+'.ogg'))
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1)
