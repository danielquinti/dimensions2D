import pygame
from pygame.locals import *
from scene import *
from phase import Phase
from resource_manager import ResourceManager


class GUIElement:
    def __init__(self, menu, image_name, rect):
        # A GUIElement must have an image to draw
        self.image = ResourceManager.loadMenuImage(image_name)
        self.image = pygame.transform.scale(self.image, (rect.w, rect.h))
        self.rect = self.image.get_rect().move(rect.left, rect.top)

    def position_in_element(self, pos):
        # Returns True if pos is a position tuple within the button
        return (pos[0] >= self.rect.left) and (pos[0] <= self.rect.right) \
            and (pos[1] >= self.rect.top) and (pos[1] <= self.rect.bottom)

    def draw(self, display):
        display.blit(self.image, self.rect)

    def action(self):
        pass


class Button(GUIElement):
    # A Button is a GUIElement that performs an action when clicked on
    def __init__(self, menu, image_name, rect, callback=None):
        GUIElement.__init__(self, menu, image_name, rect)
        self.callback = callback

    def draw(self, display):
        GUIElement.draw(self, display)

    def action(self):
        if self.callback is not None:
            self.callback()


class Menu(Scene):
    def __init__(self, director, background_name):
        Scene.__init__(self, director)
        self.director = director
        self.background = ResourceManager.loadMenuImage(background_name)
        self.background = pygame.transform.scale(self.background, (480, 270))
        self.elements = []  # List of GUIElements

    def events(self, event_list):
        for event in event_list:
            if event.type == MOUSEBUTTONDOWN:
                self.click_element = None
                for element in self.elements:
                    if element.position_in_element(event.pos):
                        # Keep track of the element you clicked on
                        self.click_element = element
            if event.type == MOUSEBUTTONUP:
                for element in self.elements:
                    if element.position_in_element(event.pos):
                        # If the click released on the same element
                        if (element == self.click_element):
                            element.action()

    def draw(self, display):
        display.blit(self.background, self.background.get_rect())
        for element in self.elements:
            element.draw(display)


class StartMenu(Menu):
    def __init__(self, director):
        Menu.__init__(self, director, 'background')
        self.elements.append(GUIElement(
            self, 'gametitle', Rect(170, 70, 140, 20)))
        self.elements.append(GUIElement(
            self, 'gamesubtitle', Rect(140, 130, 200, 40)))
        self.elements.append(Button(
            self, 'startgame', Rect(180, 190, 120, 20), self.run_game))
        self.elements.append(Button(
            self, 'quit', Rect(210, 230, 60, 20), self.director.exit_program))

    def update(self, *args):
        pass

    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.director.exit_program()  # ESC on the start menu exits
        Menu.events(self, event_list)

    def draw(self, display):
        Menu.draw(self, display)

    def run_game(self):
        self.director.start()


class PauseMenu(Menu):
    def __init__(self, director):
        Menu.__init__(self, director, 'background')
        self.elements.append(GUIElement(
            self, 'gamepaused', Rect(160, 60, 160, 60)))
        self.elements.append(Button(
            self, 'resume', Rect(180, 150, 120, 20), self.director.scene_exit))
        self.elements.append(Button(
            self, 'quit', Rect(210, 200, 60, 20), self.director.exit_program))

    def update(self, *args):
        pass

    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.director.scene_exit()  # ESC on the pause menu resumes
        Menu.events(self, event_list)

    def draw(self, display):
        Menu.draw(self, display)


class GameOverMenu(Menu):
    def __init__(self, director):
        Menu.__init__(self, director, 'background')
        self.play_music('game_over')
        self.elements.append(
            GUIElement(self, 'game_over', Rect(180, 40, 120, 50)))
        self.elements.append(
            GUIElement(self, 'detected', Rect(120, 110, 250, 50)))
        self.elements.append(
            Button(self, 'retry', Rect(205, 190, 50, 20), self.director.retry))
        self.elements.append(Button(
            self, 'quit', Rect(205, 230, 50, 20), self.director.exit_program))

    def update(self, *args):
        pass

    def events(self, event_list):
        Menu.events(self, event_list)

    def draw(self, display):
        Menu.draw(self, display)


class WinMenu(Menu):
    def __init__(self, director):
        Menu.__init__(self, director, 'background')
        self.play_music('win')
        self.elements.append(GUIElement(
            self, 'stage_complete_subtitle', Rect(40, 50, 400, 90)))
        self.elements.append(Button(
            self, 'play_again', Rect(200, 190, 80, 20), self.director.start))
        self.elements.append(Button(
            self, 'quit', Rect(215, 230, 50, 20), self.director.exit_program))

    def update(self, *args):
        pass

    def events(self, event_list):
        Menu.events(self, event_list)

    def draw(self, display):
        Menu.draw(self, display)
