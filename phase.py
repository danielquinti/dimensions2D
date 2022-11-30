import pygame
from enemies import *
from player import *
from player_with_portal import *
from pygame.locals import *
from resource_manager import *
import os
from scene import *
from pygame.sprite import Group
import math
from utils import get_frame_static
class Phase(Scene):
    camera_boundaries = [150, 100]

    def __init__(self, director, name):
        Scene.__init__(self, director)
        self.play_music(name)
        self.camera_pos = [0, 0]  # Keep track of scrolling
        # Data loaded from Tiled
        self.map = MyTiledMap(name, self.director.DISPLAY_SIZE)
        self.solid_walls = Group()  # Walls you cannot climb through
        self.portal_walls = Group()  # Walls you can create portals in
        self.walls = Group()  # All walls
        self.ladders = Group()  # Climbable objects
        self.panels = Group()  # Interactive objects that cause prompts
        self.dynamic = Group()  # Mainly for portalballs
        self.player_group = Group()
        self.enemies = Group()
        self.disabled = Group()

        self.portals = OffsetGroup()  # OffsetGroup to draw over walls
        self.drawable = OffsetGroup()  # Dynamic assets (enemies, etc)
        self.end_portal_group = OffsetGroup()  # OffsetGroup to draw over walls

        self.hud = Group()  # GUI overlay, even if not Offset, used for drawing
        self.panel_prompt = pygame.sprite.Sprite()
        self.panel_prompt.image = pygame.font.SysFont('arial', 16).render(
            'Press E to interact', False, (255, 255, 255), (0, 0, 0))
        self.panel_prompt.rect = self.panel_prompt.image.get_rect().move(180, 200)

        self.purple_portal = None
        self.orange_portal = None

        self.parse_map()  # Populate groups with data from the map

    def parse_map(self):
        drones = []
        air_drones = []
        enemy_paths = []  # Paths inside which enemies move
        # We need to store it here to only match enemies with paths once
        # we have parsed all element

        elems = {}  # Dictionary of map IDs to built objects (i.e. enemies)

        for tile_object in self.map.tmxdata.objects:
            rect = Rect(tile_object.x, tile_object.y,
                        tile_object.width, tile_object.height)
            if tile_object.name == 'player':
                elem = Player(rect, self)
                self.player = elem
                self.player_group.add(self.player)
                self.drawable.add(self.player)
            if tile_object.name == 'player_with_portal':
                elem = PlayerWithPortal(rect, self)
                self.player = elem
                self.player_group.add(self.player)
                self.drawable.add(self.player)
            if tile_object.name == 'path':
                elem = rect
                enemy_paths.append(elem)
            if tile_object.name == 'ground_drone':
                elem = rect
                drones.append(elem)
            if tile_object.name == 'camera':
                elem = SurvCamera(rect)
                self.enemies.add(elem)
                self.drawable.add(elem)
            if tile_object.name == 'air_drone':
                elem = rect
                air_drones.append(elem)
            if tile_object.name == 'turret':
                elem = Turret(rect)
                self.enemies.add(elem)
                self.drawable.add(elem)
            if tile_object.name == 'wall':
                elem = Wall(rect)
                self.walls.add(elem)
                self.solid_walls.add(elem)
            if tile_object.name == 'portal_wall':
                elem = Wall(rect)
                self.walls.add(elem)
                self.solid_walls.add(elem)
                self.portal_walls.add(elem)
            if tile_object.name == 'wall_through':
                elem = Wall(rect)
                self.walls.add(elem)
            if tile_object.name == 'ladder':
                elem = Wall(rect)
                self.ladders.add(elem)
            if tile_object.name == 'panel':
                elem = Panel(rect, self)
                pdict = tile_object.__dict__['properties']
                # Panels in Tiled store a dictionary of refs to elements
                # controlled by them. Startswith is a workaround for having
                # several disables, etc
                for attribute in pdict:  # Parse Tiled object attributes
                    if attribute.startswith('disable'):
                        # If a panel can disable an elem, it's enabled by default
                        elem.enabled_rects.append(pdict[attribute])
                    if attribute.startswith('enable'):
                        # If a panel can enable an elem, it's disabled by default
                        elem.disabled_rects.append(pdict[attribute])
                    if attribute.startswith('hide'):
                        # If a panel can hide an elem, it's shown by default
                        elem.shown_layers.append(pdict[attribute])
                        # Stores the name of the layer
                    if attribute.startswith('show'):
                        # If a panel can show an elem, it's hidden by default
                        elem.hidden_layers.append(pdict[attribute])
                        # Stores the name of the layer
                    if attribute.startswith('add'):
                        # If a panel can add an elem, it's removed by default
                        elem.removed_rects.append(pdict[attribute])
                    if attribute.startswith('remove'):
                        # If a panel can remove an elem, it's added by default
                        elem.added_rects.append(pdict[attribute])
                self.panels.add(elem)
                self.drawable.add(elem)
            if tile_object.name == 'portal_gun':
                elem = PortalGun(rect, self, tile_object.__dict__[
                                 'properties']['action'])
                self.panels.add(elem)
                self.drawable.add(elem)
            if tile_object.name == 'end_portal':
                elem = EndPortal(rect, self, tile_object.__dict__[
                                 'properties']['action'])
                self.endPortal = elem
                self.panels.add(elem)
                self.end_portal_group.add(elem)

            # Add the created object to the dictionary
            elems[tile_object.id] = elem

        # Process panels once all elements have been built
        for panel in self.panels:
            # Change enabled_rects from IDs to actual elements
            new_enabled_rects = []
            for curr_id in panel.enabled_rects:
                elem = elems[curr_id]
                new_enabled_rects.append(elem)
            panel.enabled_rects = new_enabled_rects

            # Change disabled_rects from IDs to actual elements
            new_disabled_rects = []
            for curr_id in panel.disabled_rects:
                elem = elems[curr_id]
                new_disabled_rects.append(elem)
            panel.disabled_rects = new_disabled_rects

            # Change from IDs to actual elements and their type
            panel.added_rects = [('portal_wall' if self.portal_walls.has(elems[i])
                                  else 'wall', elems[i]) for i in panel.added_rects]
            panel.removed_rects = [('portal_wall' if self.portal_walls.has(elems[i])
                                    else 'wall', elems[i]) for i in panel.removed_rects]

            # Remove from the level those that should start removed
            for rect_type, rect in panel.removed_rects:
                rect.kill()

        # Assign paths to drones once all drones and paths have been parsed
        for path in enemy_paths:
            for drone in drones:
                if path.contains(drone):
                    ground_drone = Drone(drone, path)
                    self.enemies.add(ground_drone)
                    self.drawable.add(ground_drone)
            for drone in air_drones:
                if path.contains(drone):
                    air_drone = AirDrone(drone, path)
                    self.enemies.add(air_drone)
                    self.drawable.add(air_drone)

    def spawn(self, sprite):
        self.drawable.add(sprite)
        self.dynamic.add(sprite)

    def spawn_portal(self, portal, color):
        if color == 'purple':
            self.purple_portal = portal
        else:
            self.orange_portal = portal
        self.dynamic.add(portal)
        self.portals.add(portal)

    def events(self, event_list):
        for event in event_list:
            if (event.type == KEYDOWN) and (event.key == K_ESCAPE):
                self.director.pause()

    def collide_panels(self):
        hits = pygame.sprite.spritecollide(
            self.player, self.panels, False, self.player.custom_collide)
        if hits:
            self.hud.add(self.panel_prompt)
        else:
            self.hud.remove(self.panel_prompt)
        for panel in hits:
            self.current_panel = panel

    def update(self):
        self.pressed = pygame.key.get_pressed()
        self.player_group.update(self.pressed)
        self.collide_panels()
        if self.pressed[K_e] and self.hud.has(self.panel_prompt):
            self.current_panel.activate()
        if pygame.sprite.spritecollideany(self.player, self.enemies,
                                          pygame.sprite.collide_mask):
            self.director.game_over()

        self.enemies.update()
        self.disabled.update()
        self.panels.update()

        self.dynamic.update()

        # Records the position of the player onscreen
        camera_offset = (self.player.rect.left - self.camera_pos[0],
                         self.player.rect.top - self.camera_pos[1])

        # And scrolls until constraints are met
        if camera_offset[0] < self.camera_boundaries[0]:
            self.camera_pos[0] = self.player.rect.left - \
                self.camera_boundaries[0]
        if camera_offset[0] > self.director.DISPLAY_SIZE[0] - self.camera_boundaries[0]:
            self.camera_pos[0] = self.player.rect.left - \
                self.director.DISPLAY_SIZE[0] + self.camera_boundaries[0]
        if camera_offset[1] < self.camera_boundaries[1]:
            self.camera_pos[1] = self.player.rect.top - \
                self.camera_boundaries[1]
        if camera_offset[1] > self.director.DISPLAY_SIZE[1] - self.camera_boundaries[1]:
            self.camera_pos[1] = self.player.rect.top - \
                self.director.DISPLAY_SIZE[1] + self.camera_boundaries[1]

    def draw(self, display):
        self.map.draw(display, 'Background', self.camera_pos)
        self.end_portal_group.draw(display, self.camera_pos)
        self.drawable.draw(display, self.camera_pos)
        # Draw Foreground layer after sprites. It's mainly comprised of walls
        # and as such, drawing them later hides clipping
        self.map.draw(display, 'Foreground', self.camera_pos)
        for panel in self.panels:
            panel.draw_layers(display)
        self.portals.draw(display, self.camera_pos)

        self.hud.draw(display)  # Draw the UI
        pygame.display.update()

    def game_over(self):
        self.director.game_over()


class OffsetGroup(pygame.sprite.Group):
    def __init__(self):
        pygame.sprite.Group.__init__(self)

    # Copied from Pygame's source code and modified to support offsets
    def draw(self, surface, offset):
        sprites = self.sprites()
        if hasattr(surface, "blits"):
            self.spritedict.update(
                zip(
                    sprites,
                    surface.blits(
                        (spr.image, spr.rect.move(-offset[0], -offset[1])) for spr in sprites)
                )
            )
        else:
            for spr in sprites:
                self.spritedict[spr] = surface.blit(
                    spr.image, spr.rect.move(-offset[0], -offset[1]))
        self.lostsprites = []


class MyTiledMap:
    def __init__(self, filename, DISPLAY_SIZE):
        self.display_size = DISPLAY_SIZE
        self.tmxdata = ResourceManager.loadMap(filename)

    # Loop over visible tile layers to draw them
    def draw(self, display, layer_name, offset):
        for layer in self.tmxdata.visible_layers:
            if (layer.name == layer_name
                    and isinstance(layer, pytmx.TiledTileLayer)):
                for x, y, tile, in layer.tiles():
                    # only draw what is within or near the scrolling window
                    if x * self.tmxdata.tilewidth - offset[0] + 30 < 0 or y * self.tmxdata.tileheight - offset[1] + 30 < 0 \
                            or x * self.tmxdata.tilewidth - offset[0] - 30 > self.display_size[0] or y * self.tmxdata.tileheight - offset[1] - 30 > self.display_size[1]:
                        continue
                    if tile:
                        # Blit taking the offset into account to support scrolling
                        display.blit(tile, (x * self.tmxdata.tilewidth - offset[0],
                                            y * self.tmxdata.tileheight - offset[1]))


class Wall(pygame.sprite.Sprite):
    def __init__(self, rect):
        pygame.sprite.Sprite.__init__(self)
        self.rect = rect


class Panel(pygame.sprite.Sprite):
    image = ResourceManager.loadMenuImage('arrow')

    def __init__(self, rect, phase):
        pygame.sprite.Sprite.__init__(self)
        self.activate_sound = ResourceManager.loadSound("activate")
        self.phase = phase
        self.height = 0
        self.rect = rect
        self.original_y = self.rect.top*10  # Muliply by 10 to avoid floats
        self.y = self.original_y

        # Elements that can be controlled from the panel
        # These are filled in during parsing
        self.enabled_rects = []
        self.disabled_rects = []
        self.added_rects = []
        self.removed_rects = []
        self.shown_layers = []
        self.hidden_layers = []

    # The panel draws the arrow, the actual panel is on the background
    def update(self):
        self.height = (self.height+5) % 360  # Phase of the sin wave
        self.y = self.original_y + math.sin(math.radians(self.height))*20
        self.rect.update(self.rect.left, self.y // 10,
                         self.rect.w, self.rect.h)

    def activate(self):
        self.activate_sound.play()

        # Switch added and removed
        new_removed = self.added_rects
        for rect_type, rect in self.added_rects:
            rect.kill()
        for rect_type, rect in self.removed_rects:
            self.phase.solid_walls.add(rect)
            self.phase.walls.add(rect)
            if rect_type == 'portal_wall':
                self.phase.portal_walls.add(rect)
        self.added_rects = self.removed_rects
        self.removed_rects = new_removed

        # Switch disabled and enabled
        new_disabled = self.disabled_rects
        for rect in self.disabled_rects:
            rect.enable()
        for rect in self.enabled_rects:
            self.phase.enemies.remove(rect)
            self.phase.disabled.add(rect)
            rect.disable()
        self.enabled_rects = self.disabled_rects
        self.disabled_rects = new_disabled

        # Switch hidden and shown
        new_shown = self.hidden_layers
        self.hidden_layers = self.shown_layers
        self.shown_layers = new_shown
        # Deactivate panel but keep the reference to its affected layers
        self.rect.width = 0
        self.rect.height = 0
        self.phase.drawable.remove(self)

    def draw_layers(self, display):
        for layer in self.shown_layers:
            self.phase.map.draw(display, layer, self.phase.camera_pos)


class PortalGun(Panel):
    image = ResourceManager.loadImage('portal_gun')

    def __init__(self, rect, phase, action):
        self.action = action
        Panel.__init__(self, rect, phase)
        self.rect = self.image.get_rect()
        self.rect.move_ip(rect.x, rect.y)

    def activate(self):
        self.phase.director.action(self.action)


class EndPortal(Panel):
    images=[pygame.transform.scale2x(get_frame_static(ResourceManager.loadCoordFile('portal'),
                        ResourceManager.loadSpriteSheet('portal'),
                        f'endportal{i}')) for i in range(1, 9)]
    def __init__(self, rect, phase, action):
        Panel.__init__(self, rect, phase)
        self.action = action
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.move_ip(rect.x, rect.y)
        self.cycle = 0

    def update(self):
        self.cycle = (self.cycle + 0.1) % 8
        self.image = self.images[int(self.cycle)]

    def activate(self):
        self.phase.director.action(self.action)
