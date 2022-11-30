import random
import pygame
import sys
import os
from pygame.locals import *
from resource_manager import *
import math
from utils import get_frame


class Player(pygame.sprite.Sprite):
    hitbox_offset = (24, 16, 16, 48)
    gravity = 0.25
    jump_speed = 6
    climb_speed = 0.5
    walking_speed = 0.5
    walking_accel = 0.02
    running_speed = 2
    running_accel = 0.05
    stopping_accel_strong = 0.04
    stopping_accel_light = 0.01
    braking_accel = 0.2

    def __init__(self, rect, phase):
        self.phase = phase
        pygame.sprite.Sprite.__init__(self)
        self.sheet = ResourceManager.loadSpriteSheet("player")
        print(ResourceManager.resources)
        self.coord = ResourceManager.loadCoordFile("player")
        self.image_size = (64, 64)
        self.idle = [get_frame(self, f'idle-{i}') for i in range(1, 5)]
        self.walk = [get_frame(self, f'walk-{i}') for i in range(1, 17)]
        self.run = [get_frame(self, f'run-{i}') for i in range(1, 9)]
        self.jump = [get_frame(self, f'jump-{i}') for i in range(1, 4)]
        self.climb = [get_frame(self, f'climb-{i}') for i in range(1, 6)]
        self.falling = get_frame(self, 'no-gun')

        self.image = self.idle[0]
        self.rect = self.image.get_rect()
        # The player has a hitbox to improve collision accuracy
        self.hitbox = self.rect.copy()
        self.hitbox.update(self.rect.left,
                           self.rect.top,
                           self.hitbox_offset[2], self.hitbox_offset[3])
        self.x = rect.x
        self.y = rect.y
        self.dx = self.dy = 0
        self.idle_frame = self.walk_frame = 0
        self.run_frame = self.climb_frame = 0
        self.left = self.grounded = self.climbing = False

    def animate(self):
        # If self.dx == 0, keep the last direction
        if self.dx < 0:
            self.left = True
        if self.dx > 0:
            self.left = False

        if not self.climbing:
            # Another way of removing grounded apart from jumping
            if self.dy < 0:  # Useful for portals
                self.grounded = False

            if self.grounded:
                if self.dx == 0:  # Idling on the floor
                    self.idle_frame += 0.1
                    self.idle_frame %= 4
                    self.image = self.idle[int(self.idle_frame)]
                else:
                    if abs(self.dx) <= 1:  # Walking on the floor
                        dummy = pygame.sprite.Sprite()
                        dummy.rect = self.hitbox.move(1, 0)
                        # Prevent starting to walk when next to wall
                        if not (0 < self.dx < 1 and pygame.sprite.spritecollide(
                                dummy, self.phase.solid_walls, False)):
                            self.walk_frame += 0.5 * abs(self.dx)
                            self.walk_frame %= 16
                            self.image = self.walk[int(self.walk_frame)]
                    else:  # Running on the floor
                        self.run_frame += 0.05 * abs(self.dx)
                        self.run_frame %= 8
                        self.image = self.run[int(self.run_frame)]

            if not self.grounded:
                if self.dy > 0:
                    self.image = self.falling
                else:  # If going up, play the jumping animation synced to jump
                    phase = (1 - (-self.dy / self.jump_speed)) * 3
                    phase = 0 if phase < 0 else 2 if phase > 2 else phase
                    self.image = self.jump[int(phase)]
        else:  # Climbing
            if self.dy != 0:
                self.climb_frame += 1
                self.climb_frame %= 50
            self.image = self.climb[self.climb_frame//10]

        if self.left:  # This assumes the image coming here is unflipped
            # i.e., the image is updated each frame
            self.image = pygame.transform.flip(self.image, 1, 0)

    def custom_collide(self, left, right):
        return left.hitbox.colliderect(right)

    def contained_collide(self, left, right):
        return right.rect.contains(left.hitbox)

    def solve_x_collisions(self, walls):
        hits = pygame.sprite.spritecollide(
            self, walls, False, self.custom_collide)
        if hits:
            if self.dx > 0:
                nearest = None
                # Choose the closest rect with which we collided
                for hit in hits:
                    if nearest is None or hit.rect.left < nearest:
                        nearest = hit.rect.left
                self.x = nearest - self.hitbox.w
                self.hitbox.update(self.x, self.hitbox.top,
                                   self.hitbox.w, self.hitbox.h)

            if self.dx < 0:
                nearest = None
                # Choose the closest rect with which we collided
                for hit in hits:
                    if nearest is None or hit.rect.right > nearest:
                        nearest = hit.rect.right
                self.x = nearest
                self.hitbox.update(self.x, self.hitbox.top,
                                   self.hitbox.w, self.hitbox.h)
            self.dx = 0

    def solve_y_collisions(self, walls):
        hits = pygame.sprite.spritecollide(
            self, walls, False, self.custom_collide)
        if hits:  # Reminder: positive y is down
            if self.dy < 0:
                self.grounded = False
                # Choose the closest rect with which we collided
                for hit in hits:
                    nearest = None
                    if nearest is None or hit.rect.bottom > nearest:
                        nearest = hit.rect.bottom
                self.y = nearest  # Place the player right below
                self.hitbox.update(self.hitbox.left,
                                   self.y, self.hitbox.w, self.hitbox.h)
                self.dy = 0

            elif self.dy > 0:
                for hit in hits:
                    # Choose the closest rect with which we collided
                    nearest = None
                    if nearest is None or hit.rect.top < nearest:
                        nearest = hit.rect.top
                    # Place the player right on top of the collided rect
                    self.y = nearest - self.hitbox.h

                # Only allows jumping in the collision frame for simplicity
                if self.input_jump:
                    self.dy = -self.jump_speed
                else:
                    self.dy = 0
                    self.grounded = True

                self.hitbox.update(self.hitbox.left,
                                   self.y,
                                   self.hitbox.w, self.hitbox.h)

    def collide_walls(self, all_walls, solid_walls):
        walls = solid_walls if self.climbing else all_walls

        # Solve collisions on the x axis first
        self.x += self.dx
        self.hitbox.update(self.x,
                           self.hitbox.top, self.hitbox.w, self.hitbox.h)
        self.solve_x_collisions(walls)

        if not self.climbing:  # Apply gravity if appropriate
            self.dy += self.gravity
        elif self.input_jump and not pygame.sprite.spritecollideany(
                self, all_walls, self.custom_collide):
            self.dy = -self.jump_speed
            self.climbing = False

        self.y += self.dy
        self.hitbox.update(self.hitbox.left, self.y,
                           self.hitbox.w, self.hitbox.h)
        self.solve_y_collisions(walls)

        # Resync
        self.rect.update(self.hitbox.left - self.hitbox_offset[0],
                         self.hitbox.top - self.hitbox_offset[1],
                         self.rect.w, self.rect.h)

    def resync(self):  # Used in PlayerWithPortal
        self.hitbox.update(self.x,
                           self.y, self.hitbox.w, self.hitbox.h)
        self.rect.update(self.hitbox.left - self.hitbox_offset[0],
                         self.hitbox.top - self.hitbox_offset[1],
                         self.rect.w, self.rect.h)

    def collide_ladder(self, ladders, walls):
        hit = pygame.sprite.spritecollideany(
            self, ladders, self.contained_collide)
        if hit and self.input_y != 0:  # Move up/down to start climbing
            self.climbing = True
            self.dx = 0
        elif not hit:  # Avoid climbing outside ladders
            self.climbing = False
        if self.input_dismount:
            if not pygame.sprite.spritecollideany(
                    self, walls, self.custom_collide):
                self.climbing = False

    def collide_enemies(self, enemies):
        if pygame.sprite.spritecollideany(
                self, enemies, pygame.sprite.collide_mask):
            self.phase.game_over()

    def parse_input(self, pressed):
        if pressed[K_a]:
            self.input_x = -1
        elif pressed[K_d]:
            self.input_x = 1
        else:
            self.input_x = 0

        if pressed[K_w]:
            self.input_y = -1
        elif pressed[K_s]:
            self.input_y = 1
        else:
            self.input_y = 0

        self.input_jump = pressed[K_SPACE]
        self.input_sprint = pressed[K_LSHIFT]
        self.input_dismount = pressed[K_x]

    def apply_input(self):
        if self.climbing:
            self.dy = self.climb_speed * self.input_y
            return

        if self.input_x != 0:
            if self.dx * self.input_x < 0:  # Accel faster when braking
                self.dx += self.input_x * self.braking_accel
            else:  # Moving the same direction as the input
                if (abs(self.dx) < self.walking_speed):  # Walking
                    self.dx += self.input_x * \
                        (self.walking_accel if not self.input_sprint
                            else self.running_accel)
                if (abs(self.dx) < self.running_speed) and self.input_sprint:
                    self.dx += self.input_x * self.running_accel
        # No horizontal input, slow down
        elif self.dx > 0:
            self.dx -= self.stopping_accel_strong \
                if self.dx > self.walking_speed else self.stopping_accel_light
        elif self.dx < 0:
            self.dx += self.stopping_accel_strong \
                if self.dx > self.walking_speed else self.stopping_accel_light

        # Prevent float rounding errors
        if abs(self.dx) <= 0.01:
            self.dx = 0

    def update(self, pressed):
        self.parse_input(pressed)
        self.collide_ladder(self.phase.ladders, self.phase.walls)
        self.apply_input()
        self.collide_walls(self.phase.walls, self.phase.solid_walls)
        self.collide_enemies(self.phase.enemies)
        self.animate()
