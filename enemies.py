import random
import pygame
import sys
import os
from pygame.locals import *
from resource_manager import *
import math
from utils import get_frame_static


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

    def disable(self):
        pass

    def enable(self):
        pass


class Drone(Enemy):
    oscillation_offset = -40  # Oscillate upwards to not clip the floor
    images = [get_frame_static(ResourceManager.loadCoordFile('drone'),
                        ResourceManager.loadSpriteSheet('drone'),
                        f'drone-{i}') for i in range(1, 4)]

    def __init__(self, rect, path):
        Enemy.__init__(self)
        self.image = pygame.transform.flip(self.images[0], 1, 0)
        self.rect = self.image.get_rect()
        self.rect.move_ip(rect.left, rect.top)
        self.area = path  # The area the drone patrols
        self.x = self.rect.left * 10  # Multiply to avoid using float
        self.y = (self.rect.top) * 10
        self.original_y = self.y
        self.dx = 5
        self.right = True  # All drones start moving to the right
        self.image_cycle = self.oscillation_phase = 0
        self.wait = -1

    def update(self):
        # Perform the turning animation if appropriate
        if self.wait >= 0:  # Wait times an animation
            if self.wait in range(65, 100):
                self.image = self.images[0]
            elif self.wait in range(55, 65):
                self.image = self.images[1]
            elif self.wait in range(45, 55):
                self.image = self.images[2]
            elif self.wait in range(35, 45):
                # Move the hitbox to keep the drone turning in the same place
                if self.wait == 44:
                    self.x += 128 * self.dx
                    self.rect.update(self.x // 10, self.rect.top,
                                     self.rect.w, self.rect.h)
                self.image = self.images[1]
            elif self.wait in range(0, 35):
                self.image = self.images[0]

            if (self.wait >= 45 and not self.right) or \
                    (self.wait < 45 and self.right):
                self.image = pygame.transform.flip(self.image, 1, 0)
            self.wait -= 1
            return

        # Otherwise move forward until you reach the end of your area
        self.x += self.dx
        # Oscillate up and down for effect
        self.y = self.original_y + \
            math.sin(math.radians(self.oscillation_phase)) * \
            40+self.oscillation_offset
        self.oscillation_phase = (self.oscillation_phase+5) % 360
        self.rect.update(self.x // 10, self.y//10, self.rect.w, self.rect.h)

        # If you reach the end of the area
        if self.rect.left < self.area.left or self.rect.right > self.area.right:
            self.dx = -self.dx  # Prepare for moving the other way
            self.right = not self.right
            self.wait = 99  # Start the turning animation


class AirDrone(Drone):
    oscillation_offset = 40  # Oscillate downwards to avoid clipping the ceiling
    images = [get_frame_static(ResourceManager.loadCoordFile('airdrone'),
                        ResourceManager.loadSpriteSheet('airdrone'),
                        f'airdrone-{i}') for i in range(1, 4)]

    def __init__(self, drone, path):
        Drone.__init__(self, drone, path)


class SurvCamera(Enemy):
    offset = (96, 0)
    images = [get_frame_static(ResourceManager.loadCoordFile('camera'),
                        ResourceManager.loadSpriteSheet('camera'),
                        f'camera-{i}') for i in range(1, 5)]

    def __init__(self, rect):
        Enemy.__init__(self)
        self.image_disabled = self.images[3]
        self.image = self.images[0]
        self.rect = self.image.get_rect().move(rect.x - self.offset[0], rect.y)

        self.image_cycle = random.randint(0, 30) / 10
        self.disabled = False

    def update(self):
        if not self.disabled:  # Prevent update if disabled to save time
            self.image_cycle += 0.01
            self.image_cycle %= 3
            self.image = self.images[int(self.image_cycle - 0.00001)]

    def disable(self):
        if not self.disabled:
            self.disabled = True
            self.image = self.image_disabled
            self.rect.update(  # Change rect to match small sprite
                self.rect.left + self.offset[0], self.rect.top,
                self.image.get_width(), self.image.get_height())


class Turret(Enemy):
    offset = (96, 0)
    images = [get_frame_static(ResourceManager.loadCoordFile('turret'),
                        ResourceManager.loadSpriteSheet('turret'),
                        f'turret-{i}') for i in range(1, 4)]

    def __init__(self, rect):
        Enemy.__init__(self)
        self.image = self.images[0]
        self.rect = self.image.get_rect().move(rect.x - self.offset[0], rect.y)
        self.image_cycle = 1
        self.turning = False

    def update(self):
        if self.turning:  # Turning animation
            self.image_cycle += 0.01
            if self.image_cycle >= 4:  # If finished never enter again
                self.turning = False
                return
            if self.image_cycle < 3:
                # Substract to avoid float rounding
                self.image = self.images[int(self.image_cycle - 0.00001)]
                if self.image_cycle > 2.01:
                    # On the last frame make the hitbox smaller
                    self.rect = Rect(self.rect.left+self.offset[0], self.rect.top,
                                     self.rect.w-self.offset[0], self.rect.h)
                    self.turning = False
            else:
                self.turning = False
                return

    def disable(self):
        self.turning = True
