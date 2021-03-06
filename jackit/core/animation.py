'''
Handles a sprite sheet and animation
'''

import pygame

class SpriteSheetError(Exception):
    '''
    Triggered when there is an error setting up the sprite sheet
    '''
    pass

class SpriteSheet:
    '''
    Handles a sprite sheet.
    '''
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error as e:
            raise SpriteSheetError("Unable to load spritesheet image: {}. {}".format(filename, e))

    def image_at(self, rect, colorkey=None, x_mirror=False, y_mirror=False, rotation=0):
        '''
        Load image at rect
        '''
        rect = pygame.Rect(rect)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)

        if x_mirror or y_mirror:
            image = pygame.transform.flip(image, x_mirror, y_mirror)
        if rotation > 0:
            image = pygame.transform.rotate(image, rotation)

        # Determine the color key after transforms. Fix for weird graphics issue
        # in pygame_sdl2 refs #62
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)

        return image

    def images_at(self, rects, colorkey=None, x_mirror=False, y_mirror=False, rotation=0):
        '''
        Load image at each rect and return as list
        '''
        return [self.image_at(rect, colorkey, x_mirror, y_mirror, rotation) for rect in rects]

    def load_strip(self, rect, image_count, colorkey=None,
                   x_mirror=False, y_mirror=False, rotation=0):
        '''
        Load an entire strip
        '''
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3]) for x in range(image_count)]
        return self.images_at(tups, colorkey, x_mirror, y_mirror, rotation)


class SpriteStripAnimation:
    '''
    Animator for a spritesheet
    '''
    def __init__(
            self, filename, rect, count, colorkey=None,
            loop=False, frames=1, x_mirror=False, y_mirror=False, rotation=0):

        self.filename = filename

        # Load the sprite sheet and the srip
        sheet = SpriteSheet(filename)
        self.images = sheet.load_strip(rect, count, colorkey, x_mirror, y_mirror, rotation)

        self.i = 0

        # True means keep looping, False raises StopIteration at end of strip
        self.loop = loop

        # Number of frames to return the same image before the next image is returned
        self.frames = frames
        self.f = frames

    def iter(self):
        '''
        Get an iterator for the list
        '''
        self.i = 0
        self.f = self.frames
        return self

    def done(self):
        '''
        True if not looping and the end of the animation has been reached
        '''
        if self.i >= len(self.images) and not self.loop:
            return True
        return False

    def next(self):
        '''
        Get the next image in the spritesheet
        '''

        # Should we loop or stop iteration
        if self.i >= len(self.images):
            if not self.loop:
                return self.images[-1]
            else:
                self.i = 0

        image = self.images[self.i]
        self.f -= 1
        if self.f == 0:
            self.i += 1
            self.f = self.frames

        return image

    def __add__(self, ss):
        self.images.extend(ss.images)
        return self
