import pygame
import sys
import os
from pygame.locals import *
import pytmx
import json


class ResourceManager():
    resources = {}

    @classmethod
    def loadSpriteSheet(cls, name):
        full_name=name+'_sheet'
        if full_name in cls.resources:
            return cls.resources[full_name]
        else:
            cls.resources[full_name] = pygame.image.load(os.path.join("assets/sprites/",(name+".png")))
            return cls.resources[full_name]

    @classmethod
    def loadMenuImage(cls, name):
        full_name=name+'_menu'
        if full_name in cls.resources:
            return cls.resources[full_name]
        else:
            cls.resources[full_name] = pygame.image.load(os.path.join("assets/sprites/menus/",(name+".png")))
            return cls.resources[full_name]

    @classmethod
    def loadImage(cls, name):
        full_name=name+'_object'
        if full_name in cls.resources:
            return cls.resources[full_name]
        else:
            cls.resources[full_name] = pygame.image.load(os.path.join("assets/sprites/",(name+".png")))
            return cls.resources[full_name]

    @classmethod
    def loadSound(cls, name):
        full_name=name+'_sound'
        if full_name in cls.resources:
            return cls.resources[full_name]
        else:
            cls.resources[full_name] = pygame.mixer.Sound(os.path.join("assets/sfx/",(name+".ogg")))
            cls.resources[full_name].set_volume(0.1)
            return cls.resources[full_name]

    @classmethod
    def loadCoordFile(cls, name):
        full_name=name+'_coord'
        if full_name in cls.resources:
            return cls.resources[full_name]
        else:
            file_name=os.path.join("assets/coords/",(name+".json"))
            file=open(file_name,"r")
            cls.resources[full_name] = json.load(file)['frames']
            file.close()
            return cls.resources[full_name]

    @classmethod
    def loadMap(cls, name):
        full_name=name+'_map'
        if full_name in cls.resources:
            return cls.resources[full_name]
        else:
            cls.resources[full_name] = pytmx.load_pygame(os.path.join("assets/maps/",name+".tmx"), pixelalpha=True)
            return cls.resources[full_name]
