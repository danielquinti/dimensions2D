import random
import pygame
import sys
import os
from pygame.locals import *
from resource_manager import *
from player import *
import math
from utils import get_frame_static, snap_to_tile


class Portal(pygame.sprite.Sprite):
    def __init__(self, x, y, dir, color):
        pygame.sprite.Sprite.__init__(self)
        self.dir = dir
        self.color = color
        self.cycle = 0
        self.images = [get_frame_static(ResourceManager.loadCoordFile('portal'),
                                        ResourceManager.loadSpriteSheet(
                                            "portal"), f'{color}portal{i}')
                       for i in range(1, 9)]

        if self.dir == 'right':
            self.images = [pygame.transform.flip(
                image, 1, 0) for image in self.images]
        if self.dir == 'down':
            self.images = [pygame.transform.rotate(
                image, -90) for image in self.images]
        if self.dir == 'up':
            self.images = [pygame.transform.rotate(
                image, 90) for image in self.images]
        self.image = self.images[0]
        self.rect = self.image.get_rect().move(x, y)
        self.hitbox = self.rect.copy()
        # We use a hitbox to improve the collisions with the player
        if self.dir == 'down':
            self.hitbox.update(self.hitbox.left, self.hitbox.top,
                               self.hitbox.width, self.hitbox.height + 32)
        if self.dir == 'up':
            self.hitbox.update(self.hitbox.left, self.hitbox.top -
                               32, self.hitbox.width, self.hitbox.height + 64)

    def update(self):
        self.cycle += 0.1
        self.cycle %= 8
        self.image = self.images[int(self.cycle)]


class PortalBall(pygame.sprite.Sprite):
    speed = 3
    # 3 is the speed of the ball, which diagonally is approx. sqrt(2^2+2^2)
    diag_speed = 2

    def __init__(self, x, y, dir, color, phase):
        pygame.sprite.Sprite.__init__(self)
        self.phase = phase
        self.image = get_frame_static(ResourceManager.loadCoordFile("portal"),
                                      ResourceManager.loadSpriteSheet(
                                          "portal"), f'{color}-blast')
        self.create_sound = ResourceManager.loadSound("create")
        self.dx = -self.speed if dir == 'left' else self.speed \
            if dir == 'right' else 0
        self.dy = -self.speed if dir == 'up' else self.speed \
            if dir == 'down' else 0
        if dir == 'up_right':
            self.dx = self.diag_speed
            self.dy = -self.diag_speed
        if dir == 'up_left':
            self.dx = -self.diag_speed
            self.dy = -self.diag_speed
        if dir == 'down_right':
            self.dx = self.diag_speed
            self.dy = self.diag_speed
        if dir == 'down_left':
            self.dx = -self.diag_speed
            self.dy = self.diag_speed

        self.dir = dir
        self.color = color

        dir_to_rotation = {'right': 0, 'up_right': 45, 'up': 90,
                           'up_left': 135, 'left': 180, 'down_left': -135,
                           'down': -90, 'down_right': -45}
        self.image = pygame.transform.rotate(self.image, dir_to_rotation[dir])
        self.rect = self.image.get_rect()
        self.rect.move_ip(x, y)

    def ball_collide(self, left, right):
        # bugs when shooting off angle, cannot fix
        return left.rect.inflate(-8, -8).colliderect(right.rect)

    def update(self):
        # The ball is moving straight, "easy" case
        if self.dir in ['up', 'down', 'left', 'right']:
            self.rect.move_ip(self.dx, self.dy)
            pygame.sprite.spritecollide(self, self.phase.portals, True)

            for wall in pygame.sprite.spritecollide(
                    self, self.phase.portal_walls, False, self.ball_collide):
                opposite = {'left': 'right', 'right': 'left', 'up': 'down',
                            'down': 'up'}
                portal_dir = opposite[self.dir]
                portalx = snap_to_tile(
                    # If the ball is not going to the right, move 16 left to
                    # spawn the portal inside the wall
                    self.rect.x + (0 if self.dir == 'right' else -16))
                portaly = snap_to_tile(
                    # If the ball is going up, move 16 more up to spawn inside
                    self.rect.y if self.dir == 'down' else self.rect.y - 16)

                # Make sure that the spawned portal is within the portal_wall
                if self.dir == 'left' or self.dir == 'right':
                    if portaly < wall.rect.y:
                        portaly = wall.rect.y
                    if portaly > wall.rect.bottom - 64:
                        portaly = wall.rect.bottom - 64
                if self.dir == 'up' or self.dir == 'down':
                    if portalx < wall.rect.x:
                        portalx = wall.rect.x
                    if portalx > wall.rect.right - 64:
                        portalx = wall.rect.right - 64

                self.create_sound.play()
                self.phase.spawn_portal(Portal(portalx, portaly, portal_dir,
                                               self.color), self.color)
                self.kill()
        else:  # Diagonal balls require direction checks on impact
            for curr in ['h', 'v']:  # Check both horizontal and vertical
                if curr == 'h':
                    self.rect.move_ip(self.dx, 0)
                else:
                    self.rect.move_ip(0, self.dy)

                pygame.sprite.spritecollide(self, self.phase.portals, True)

                for wall in pygame.sprite.spritecollide(
                        self, self.phase.portal_walls, False, self.ball_collide):
                    portal_dir = 'left' if curr == 'h' and self.dx > 0 else \
                        'right' if curr == 'h' else 'up' \
                        if curr == 'v' and self.dy > 0 else 'down'
                    # Same as above but with calculated direction
                    portalx = snap_to_tile(
                        self.rect.x + (0 if portal_dir == 'left' else -16))
                    portaly = snap_to_tile(
                        self.rect.y if portal_dir == 'up' else self.rect.y - 16)

                    # Make sure that the new portal is within the portal_wall
                    if portal_dir == 'left' or portal_dir == 'right':
                        if portaly < wall.rect.y:
                            portaly = wall.rect.y
                        if portaly > wall.rect.bottom - 64:
                            portaly = wall.rect.bottom - 64
                    if portal_dir == 'up' or portal_dir == 'down':
                        if portalx < wall.rect.x:
                            portalx = wall.rect.x
                        if portalx > wall.rect.right - 64:
                            portalx = wall.rect.right - 64
                    self.create_sound.play()
                    self.phase.spawn_portal(Portal(portalx, portaly, portal_dir,
                                                   self.color), self.color)
                    self.kill()
                    return

        if pygame.sprite.spritecollideany(self, self.phase.walls,
                                          self.ball_collide):
            self.kill()


class PlayerWithPortal(Player):
    def __init__(self, rect, phase):
        Player.__init__(self, rect, phase)
        self.aiming = False
        self.shoot_cooldown = 60  # 1 second
        self.portal_color = 'orange'
        self.aim = get_frame(self, 'shoot')
        self.aim_up = get_frame(self, 'shoot-up')
        self.aim_down = get_frame(self, 'shoot-down')
        self.aim_diagonal_up = get_frame(self, 'shoot-up-diagonal')
        self.aim_diagonal_down = get_frame(self, 'shoot-down-diagonal')
        self.falling = get_frame(self, 'gun')
        self.shoot_sound = ResourceManager.loadSound('shoot')
        self.portal_sound = ResourceManager.loadSound('portal')

    def custom_contained(self, left, right):
        return right.hitbox.contains(left.hitbox)

    def collide_portals_and_walls(self, all_walls, solid_walls):
        walls = solid_walls if self.climbing else all_walls

        # Resolve collisions on the x axis first
        self.x += self.dx
        self.hitbox.update(self.x,
                           self.hitbox.top, self.hitbox.w, self.hitbox.h)

        self.collide_portals()

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

        self.collide_portals()

        self.solve_y_collisions(walls)

        # Resync
        self.rect.update(self.hitbox.left - self.hitbox_offset[0],
                         self.hitbox.top - self.hitbox_offset[1],
                         self.rect.w, self.rect.h)

    def collide_portals(self):
        for portal in pygame.sprite.spritecollide(
                self, self.phase.portals, False, self.custom_contained):

            other_portal = self.phase.orange_portal \
                if portal == self.phase.purple_portal \
                else self.phase.purple_portal

            if other_portal is None:
                return

            self.portal_sound.play()
            px = other_portal.rect.x  # Exit x
            py = other_portal.rect.y  # Exit y
            pdir = other_portal.dir  # Exit direction
            edir = portal.dir  # Entry direction

            # Calculate offset from the exit portal
            self.x = px + (24 if pdir == 'right' else -
                           8 if pdir == 'left' else 32)  # 8 offset
            self.y = py + (32 if pdir == 'down' else -
                           64 if pdir == 'up' else 16)  # 8 offset as well

            # Calculate entry speed
            entry_speed = -self.dx if edir == 'right' else self.dx \
                if edir == 'left' else self.dy if edir == 'up' else -self.dy

            # Calculate the exit direction to apply exit speed
            if pdir == 'up' or pdir == 'down':
                self.dx = 0
                self.dy = -entry_speed if pdir == 'up' else entry_speed
            else:
                self.dx = -entry_speed if pdir == 'left' else entry_speed
                self.dy = 0

            self.dx *= 0.9  # Portals are 90% efficient in conserving momentum
            self.dy *= 0.9
            self.resync()

    def shoot(self):
        if self.shoot_cooldown:
            return
        self.shoot_sound.play()
        self.shoot_cooldown = 60

        # Calculation of starting position of the ball
        # These are the offsets of the ball w.r.t the player
        offsetx = 0 if self.aiming == 'up' else \
            -8 if self.aiming == 'down' and self.left else \
            10 if self.aiming == 'down' else \
            -24 if self.left else 24
        offsety = -16 if self.aiming == 'up' else \
            20 if self.aiming == 'down' else 0
        if self.aiming == 'diagonal_up':
            offsety = -16
            offsetx = -20 if self.left else 16
        if self.aiming == 'diagonal_down':
            offsety = 12
            offsetx = -20 if self.left else 16

        # Calculate the direction of the ball from player's direction
        dir = 'left' if self.left else 'right'
        if self.aiming == 'up':
            dir = 'up'
        if self.aiming == 'down':
            dir = 'down'
        if self.aiming == 'diagonal_down':
            dir = 'down_left' if self.left else 'down_right'
        if self.aiming == 'diagonal_up':
            dir = 'up_left' if self.left else 'up_right'

        self.phase.spawn(PortalBall(self.x + offsetx, self.y + offsety,
                                    dir, self.portal_color, self.phase))

        if self.portal_color == 'orange':
            if self.phase.orange_portal is not None:
                self.phase.orange_portal.kill()
                self.phase.orange_portal = None
            self.portal_color = 'purple'
        else:
            if self.phase.purple_portal is not None:
                self.phase.purple_portal.kill()
                self.phase.purple_portal = None
            self.portal_color = 'orange'

    def animate(self):
        if self.input_aim:
            if self.aiming == 'neutral':
                self.image = self.aim
            elif self.aiming == 'up':
                self.image = self.aim_up
            elif self.aiming == 'down':
                self.image = self.aim_down
            elif self.aiming == 'diagonal_up':
                self.image = self.aim_diagonal_up
            elif self.aiming == 'diagonal_down':
                self.image = self.aim_diagonal_down
            if self.left:
                self.image = pygame.transform.flip(self.image, 1, 0)
        else:
            Player.animate(self)

    def parse_input(self, pressed):
        Player.parse_input(self, pressed)

        self.input_aim = pygame.mouse.get_pressed()[2]
        self.input_shoot = pygame.mouse.get_pressed()[0]

        if not self.input_aim:
            self.aiming = False
            return

        position_on_display = (self.x - self.phase.camera_pos[0],
                               self.y - self.phase.camera_pos[1])

        # Offset of the mouse w.r.t. the player
        aim_offset = (pygame.mouse.get_pos()[0] - position_on_display[0],
                      pygame.mouse.get_pos()[1] - position_on_display[1])

        if aim_offset[0] < 0:  # The mouse is left of the player
            self.left = True
            if aim_offset[1] < 2.5 * aim_offset[0]:
                self.aiming = 'up'
            elif aim_offset[1] < 0.5 * aim_offset[0]:
                self.aiming = 'diagonal_up'
            elif aim_offset[1] < -0.5 * aim_offset[0]:
                self.aiming = 'neutral'
            elif aim_offset[1] < -2.5 * aim_offset[0]:
                self.aiming = 'diagonal_down'
            else:
                self.aiming = 'down'

        # If the mouse is inside of the player don't change direction
        if aim_offset[0] > 16:  # The mouse is right of the player
            self.left = False
            if aim_offset[1] < -2.5 * (aim_offset[0] - 16):
                self.aiming = 'up'
            elif aim_offset[1] < -0.5 * (aim_offset[0] - 16):
                self.aiming = 'diagonal_up'
            elif aim_offset[1] < 0.5 * (aim_offset[0] - 16):
                self.aiming = 'neutral'
            elif aim_offset[1] < 2.5 * (aim_offset[0] - 16):
                self.aiming = 'diagonal_down'
            else:
                self.aiming = 'down'

    def apply_input(self):
        if self.climbing:
            self.dy = self.climb_speed * self.input_y
            return

        if self.input_x != 0 and not self.input_aim:
            if self.dx * self.input_x < 0:  # Accel faster when braking
                self.dx += self.input_x * self.braking_accel
            else:  # Moving the same direction as the input
                if (abs(self.dx) < self.walking_speed):  # Walking
                    self.dx += self.input_x * \
                        (self.walking_accel if not self.input_sprint else
                            self.running_accel)
                if (abs(self.dx) < self.running_speed) and self.input_sprint:
                    self.dx += self.input_x * self.running_accel
        # No horizontal input, slow down
        elif self.dx > 0:
            self.dx -= self.stopping_accel_strong \
                if self.dx > self.walking_speed else self.stopping_accel_light
        elif self.dx < 0:
            self.dx += self.stopping_accel_strong \
                if self.dx > self.walking_speed else self.stopping_accel_light
        if self.input_aim and self.grounded:
            self.dx *= 0.9

        # Prevent float rounding errors
        if abs(self.dx) <= 0.01:
            self.dx = 0

    def update(self, pressed):
        self.parse_input(pressed)
        self.collide_ladder(self.phase.ladders, self.phase.walls)
        self.apply_input()
        self.collide_portals_and_walls(
            self.phase.walls, self.phase.solid_walls)
        self.collide_enemies(self.phase.enemies)
        if self.input_shoot and self.aiming:
            self.shoot()
        if self.shoot_cooldown:
            self.shoot_cooldown -= 1
        self.animate()
