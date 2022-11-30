import pygame
import sys
from scene import *
from pygame.locals import *
from menu import PauseMenu
from menu import *


class Director:
    DISPLAY_SIZE = (480, 270)
    def __init__(self):
        self.display = pygame.display.set_mode(self.DISPLAY_SIZE, flags=SCALED)
        pygame.display.set_caption("DIMENSIONS")
        self.stack = []  # contains scenes, with the current one on top
        self.exit = False  # flag for stopping the interactive loop
        self.clock = pygame.time.Clock()

        # set up audio for the whole game
        pygame.mixer.pre_init(44100, 16, 2, 4096)
        pygame.mixer.init()

    def loop(self, scene):
        self.exit = False  # clear old stopping signals

        pygame.event.clear()  # purge events before entering loop

        # interactive loop, common to every scene
        # finishes upon receiving the exit signal
        while not self.exit:
            self.clock.tick(60)  # fps synchronization

            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    self.exit_program()
            scene.events(event_list)  # pass events to the scene
            scene.update()  # update once per frame before drawing
            scene.draw(self.display)  # draw to the buffer
            pygame.display.flip()  # send the buffer to display

    def run(self):
        while len(self.stack):  # exits if the stack is empty
            # take the scene at the top of the stack
            scene = self.stack[len(self.stack)-1]
            # and run it until you receive exit
            self.loop(scene)

    def scene_exit(self):
        self.exit = True
        # if the stack is not empty, the last scene is removed
        if (len(self.stack) > 0):
            self.stack.pop()

    def exit_program(self):
        self.stack = []  # the stack is emptied
        self.exit = True  # stop the loop method on next frame

    def change_scene(self, scene):
        self.scene_exit()  # remove current scene from stack
        self.stack.append(scene)  # and stack the new one

    def push(self, scene):
        self.exit = True  # current scene will exit on next frame
        # the new scene will start playing immediately, but the old one
        # will remain under it
        self.stack.append(scene)

    def pause(self):
        # by pushing, the phase is left below to be resumed
        self.push(PauseMenu(self))

    def game_over(self):
        # remove the phase from the stack, losing its state
        self.change_scene(GameOverMenu(self))

    def action(self, action):
        if action.startswith('level'):
            self.curr_phase = action  # tell retry what to start
            self.change_scene(Phase(self, self.curr_phase))
        elif action == 'win':
            self.change_scene(WinMenu(self))

    def start(self):
        self.action('level_1')

    def retry(self):
        self.change_scene(Phase(self, self.curr_phase))
