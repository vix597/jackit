'''
User controllable player
'''

import os
import pygame
from deploy import SiteDeployment
from jackit.core import BLOCK_WIDTH, BLOCK_HEIGHT
from jackit.core.patch import UserPatch
from jackit.core.animation import SpriteStripAnimation
from jackit.core import CustomEvent
from jackit.core.actor import Actor
from jackit.actors.enemy import Enemy
from jackit.entities import CodeBlock, ExitBlock, DeathBlock,\
                            DecryptionKey, Coin

class Player(Actor):
    '''
    User controlled player
    '''

    def __init__(self, game_engine, controls, spawn_point=(0, 0)):
        run_jack = os.path.join(SiteDeployment.resource_path, "sprites", "run_jack.bmp")
        stand_jack = os.path.join(SiteDeployment.resource_path, "sprites", "stand_jack.bmp")
        jack_it = os.path.join(SiteDeployment.resource_path, "sprites", "jack_it.bmp")
        jack_off = os.path.join(SiteDeployment.resource_path, "sprites", "jack_off.bmp")

        self.stand_animation = SpriteStripAnimation(
            stand_jack, (0, 0, 19, BLOCK_HEIGHT), 1, -1, False,
            int(game_engine.config.framerate / 7)
        )
        self.run_animation = SpriteStripAnimation(
            run_jack, (0, 0, 19, BLOCK_HEIGHT), 2, -1, True,
            int(game_engine.config.framerate / 7)
        )
        self.run_left_animation = SpriteStripAnimation(
            run_jack, (0, 0, 19, BLOCK_HEIGHT), 2, -1, True,
            int(game_engine.config.framerate / 7), x_mirror=True
        )

        self.jackin_it = SpriteStripAnimation(
            jack_it, (0, 0, BLOCK_WIDTH, BLOCK_HEIGHT), 10, -1, False,
            int(game_engine.config.framerate / 7)
        )

        self.jackin_off = SpriteStripAnimation(
            jack_off, (0, 0, BLOCK_WIDTH, BLOCK_HEIGHT), 8, -1, False,
            int(game_engine.config.framerate / 7)
        )

        super(Player, self).__init__(
            game_engine, 19, BLOCK_HEIGHT, spawn_point[0],
            spawn_point[1], animation=self.stand_animation
        )

        self.controls = controls
        self.use_patch = True # Use the UserPatch for player stats and player

        # Current level points
        self.level_points = 0

        # List of items the player has
        self.items = []

        # List of stored code routines (so they don't have to do the code blocks_hit
        # every time)
        self.stored_code = []

        # True if the player is alive otherwise false
        self.alive = True

        # True if the player cannot be killed
        self.invincible = False

        # Whether the animations for jackin in or jackin off are running
        self.is_jackin_in = False
        self.is_jackin_off = False

    def update(self):
        super(Player, self).update()

        if self.is_jackin_in and self.animation.done():
            self.is_jackin_in = False
        if self.is_jackin_off and self.animation.done():
            self.is_jackin_off = False

    def stop(self):
        if self.is_jackin_in or self.is_jackin_off:
            return

        if self.horizontal_movement_action != self.stop:
            self.animation = self.stand_animation.iter()
        super(Player, self).stop()

    def go_left(self):
        if self.is_jackin_in or self.is_jackin_off:
            return

        if self.horizontal_movement_action != self.go_left:
            self.animation = self.run_left_animation.iter()
        super(Player, self).go_left()

    def go_right(self):
        if self.is_jackin_in or self.is_jackin_off:
            return

        if self.horizontal_movement_action != self.go_right:
            self.animation = self.run_animation.iter()
        super(Player, self).go_right()

    def has_key(self):
        '''
        Does the player have the decryption key?
        '''
        return any(isinstance(x, DecryptionKey) for x in self.items)

    def collide(self, change_x, change_y, sprite):
        '''
        Called on each collision
        '''
        collideable = super(Player, self).collide(change_x, change_y, sprite)

        if isinstance(sprite, Coin):
            self.collides_with.remove(sprite) # So we don't accidently grab it twice
            self.level_points += sprite.points
            self.game_engine.total_points += sprite.points
            pygame.event.post(pygame.event.Event(CustomEvent.KILL_SPRITE, {"sprite":sprite}))
        elif isinstance(sprite, DecryptionKey):
            self.collides_with.remove(sprite) # So we don't accidently grab it twice
            self.items.append(sprite)
            pygame.event.post(pygame.event.Event(CustomEvent.KILL_SPRITE, {"sprite":sprite}))
            for block in self.game_engine.current_level.code_blocks:
                block.locked = False
        elif isinstance(sprite, ExitBlock):
            self.items.clear()
            self.level_points = 0
            pygame.event.post(pygame.event.Event(CustomEvent.NEXT_LEVEL))
        elif isinstance(sprite, Enemy) or isinstance(sprite, DeathBlock):
            self.kill()

        return collideable

    def reset(self):
        '''
        Reset the player
        '''
        super(Player, self).reset()
        self.alive = True
        self.invincible = False

    def kill(self):
        '''
        Kill the player
        '''
        if not self.alive or self.invincible:
            return

        self.items.clear()
        self.items = []
        self.game_engine.total_points -= self.level_points
        self.level_points = 0

        self.alive = False
        super(Player, self).kill()

    def is_on_collideable(self):
        '''
        The rare chance that we land perfectly on an enemy and miss the call to collide
        '''
        ret = super(Player, self).is_on_collideable()
        if ret:
            for block in self.frame_cache["is_on_collideable"]:
                if isinstance(block, Enemy) or isinstance(block, DeathBlock):
                    pygame.event.post(pygame.event.Event(CustomEvent.KILL_SPRITE, {"sprite":self}))
                    break
        return ret

    def collide_with(self, sprite):
        '''
        Some other sprite collided into us (we didn't collide into it)
        Happens when the other sprite is moving and this sprite is not
        '''
        if isinstance(sprite, Enemy):
            self.kill()

    def is_on_code_block(self):
        '''
        True if the Player is on a code block
        Uses frame cache to improve performance
        for subsequent calls
        '''
        if self.frame_cache.get("is_on_code_block", None) is not None:
            return True

        if not self.is_on_interactable():
            return False

        for interactable in self.frame_cache["is_on_interactable"]:
            if isinstance(interactable, CodeBlock):
                self.frame_cache["is_on_code_block"] = interactable
                return True # Level design should only allow player to be on one code block
                            # at a time. If not, too bad, I'm ignoring any others.

        return False

    def is_on_interactable(self):
        '''
        True if Player is on an interactable entity
        uses frame cache to ensure subsequent calls
        are faster
        '''

        # Speed up calls to this method if used more than once per frame
        if self.frame_cache.get("is_on_interactable", None) is not None:
            return True

        blocks_hit = self.spritecollide(
            self.game_engine.current_level.interactable_blocks,
            0, 0,
            trigger_cb=False,
            only_collideable=False
        )

        self.frame_cache["is_on_interactable"] = []
        for block in blocks_hit:
            if block.is_interactable():
                self.frame_cache["is_on_interactable"].append(block)

        if len(self.frame_cache["is_on_interactable"]) == 0:
            self.frame_cache["is_on_interactable"] = None
            return False

        return True

    def handle_event(self, event, keys):
        '''
        Handle player events (like controls and stuff)
        @param event - Current event
        @param keys - List of keys currently pressed by key ID
        '''
        if event.type == pygame.KEYUP:
            if event.key == self.controls.left and not keys[self.controls.right]:
                self.stop()
            elif event.key == self.controls.right and not keys[self.controls.left]:
                self.stop()
            elif event.key == self.controls.jump:
                self.stop_jumping()
        elif event.type == pygame.KEYDOWN:
            if event.key == self.controls.reset_code:
                print("Resetting code block")
                for block in self.game_engine.current_level.code_blocks:
                    block.restore() # Put the initial challenge text back
                UserPatch.unpatch()
            elif event.key == self.controls.kill_self:
                print("Killing self!")
                self.game_engine.hud.display_hint("You just killed yourself with 'K'. Worth it?", 2)
                self.kill()
                return False
            elif event.key == self.controls.left:
                self.go_left()
            elif event.key == self.controls.right:
                self.go_right()
            elif event.key == self.controls.jump:
                self.jump()
            elif event.key == self.controls.interact and self.is_on_code_block():
                if self.frame_cache["is_on_code_block"].is_locked() and not self.has_key():
                    return True # Continue processing events

                print(self.frame_cache["is_on_code_block"].is_locked())
                print(self.has_key())

                # Stop the player and put them over the interactable object
                # and make them invincible
                self.hard_stop()
                self.rect.left =\
                    (self.frame_cache["is_on_code_block"].rect.left - (self.rect.width / 2))

                self.rect.bottom = self.frame_cache["is_on_code_block"].rect.bottom

                # Interact with the object
                self.frame_cache["is_on_code_block"].interact()

        return True # Continue processing events
