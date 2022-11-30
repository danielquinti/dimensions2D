import pygame
from pygame.locals import *
import sys
from menu import StartMenu
from director import Director


def main():
    pygame.init()
    # the director configures the display
    director = Director()
    # include start menu in the stack
    director.push(StartMenu(director))
    # select last scene in stack and run interactive loop
    director.run()
    # when the director has no scenes left, the game quits
    pygame.quit()


if __name__ == "__main__":
    main()
