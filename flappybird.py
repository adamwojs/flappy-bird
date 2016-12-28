import os, sys, pygame, random

FRAMES_PER_SECOND = 30
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 700
GAP_SIZE = 100
BIRD_GRAVITY = 1
BIRD_VELOCITY = 12
WALL_SPEED = 10
WALL_WIDTH = 100


class Assets(object):
    ASSETS_DIR = "assets"

    BACKGROUND = None
    WALL_TOP = None
    WALL_BOTTOM = None
    BIRD_DEAD = None
    BIRD_FRAMES = None

    @staticmethod
    def init():
        print "Loading assets"
        Assets.BACKGROUND = Assets.load_image("background.png")
        Assets.WALL_TOP = Assets.load_image("top.png")
        Assets.WALL_BOTTOM = Assets.load_image("bottom.png")
        Assets.BIRD_DEAD = Assets.load_image("dead.png")
        Assets.BIRD_FRAMES = map(lambda x: Assets.load_image(x), [
            "0.png", "1.png", "2.png"
        ])

    @staticmethod
    def load_image(name):
        fullpath = os.path.join(Assets.ASSETS_DIR, name)
        print "Loading image: " + fullpath
        if not os.path.isfile(fullpath):
            raise IOError("Could not load file: " + fullpath)

        return pygame.image.load(fullpath).convert_alpha()


class ScoreCounter(pygame.sprite.Sprite):
    FONT_SIZE = 24
    FONT_COLOR = (255, 255, 255)
    PADDING_TOP = 10

    def __init__(self):
        super(ScoreCounter, self).__init__()
        self.font = pygame.font.Font(pygame.font.get_default_font(), self.FONT_SIZE)
        self.score = 0
        self.distance = 0
        self._update_score(0)

    def update(self, det):
        self.distance += WALL_SPEED
        if self.distance >= SCREEN_WIDTH + WALL_WIDTH:
            self.distance = 0
            self._update_score(1)

    def restart(self):
        self.score = 0
        self.distance = 0
        self._update_score(0)

    def _update_score(self, score):
        self.score += score
        self.image = self.font.render(str(self.score), True, self.FONT_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = (SCREEN_WIDTH - self.rect.w) / 2
        self.rect.y = self.PADDING_TOP


class BirdSprite(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.current_frame = 0
        self.image = Assets.BIRD_FRAMES[self.current_frame]
        self.rect = self.image.get_rect()
        self.is_jumping = False
        self.velocity = 0

    def update(self, deltat):
        if self.is_jumping:
            self.rect.y -= self.velocity
            self.velocity -= BIRD_GRAVITY
            if self.velocity == 0:
                self.is_jumping = False
        else:
            self.velocity += BIRD_GRAVITY
            self.rect.y += self.velocity

        self.image = Assets.BIRD_FRAMES[self.current_frame]
        self.current_frame = (self.current_frame + 1) % 3

    def jump(self):
        self.is_jumping = True
        self.velocity = BIRD_VELOCITY

    def restart(self):
        self.current_frame = 0
        self.image = Assets.BIRD_FRAMES[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = self.rect.w / 2
        self.rect.y = (SCREEN_HEIGHT / 2) - (self.rect.h / 2)
        self.is_jumping = False
        self.velocity = 0

    def set_dead(self):
        self.image = Assets.BIRD_DEAD


class WallSprite(pygame.sprite.Sprite):
    DIRECTION_TOP = "top"
    DIRECTION_BOTTOM = "bottom"

    def __init__(self, direction, init_gap_y, init_gap_size):
        super(WallSprite, self).__init__()

        self.direction = direction
        self.image = Assets.WALL_TOP if direction == self.DIRECTION_TOP else Assets.WALL_BOTTOM
        self.rect = self.image.get_rect()
        self.set_gap(init_gap_y, init_gap_size)

    def update_position(self):
        if self.rect.x < -self.rect.w:
            self.rect.x = SCREEN_WIDTH
        else:
            self.rect.x -= WALL_SPEED

    def set_gap(self, gap_y, gap_size):
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        if self.direction == self.DIRECTION_TOP:
            self.rect.y = 0
            self.rect.move_ip(0, -(gap_y + gap_size))
        else:
            self.rect.y = SCREEN_HEIGHT
            self.rect.move_ip(0, -(gap_y - gap_size))


class WallPair(pygame.sprite.Group):
    def __init__(self):
        gap_y = self._generate_gap_y()

        super(WallPair, self).__init__([
            WallSprite(WallSprite.DIRECTION_TOP, gap_y, GAP_SIZE),
            WallSprite(WallSprite.DIRECTION_BOTTOM, gap_y, GAP_SIZE)
        ])

        self.next_gap_y = self._generate_gap_y()

    def update(self, daltat):
        super(WallPair, self).update(daltat)
        generate_next_gap = False
        for wall in self.sprites():
            if wall.rect.x < -wall.rect.w:
                wall.rect.x = SCREEN_WIDTH
                wall.set_gap(self.next_gap_y, GAP_SIZE)
                generate_next_gap = True
            else:
                wall.rect.x -= WALL_SPEED

        if generate_next_gap:
            self.next_gap_y = self._generate_gap_y()

    def is_collide(self, obj):
        for wall in self.sprites():
            is_collide = pygame.sprite.collide_mask(obj, wall)
            if is_collide:
                return True
        return False

    def restart(self):
        for wall in self.sprites():
            wall.rect.x = SCREEN_WIDTH
            wall.set_gap(self.next_gap_y, GAP_SIZE)
        self.next_gap_y = self._generate_gap_y()

    def _generate_gap_y(self):
        # TODO: Refactoring
        return random.randint(13, (SCREEN_HEIGHT - 130) / 10) * 10


class FlappyBird(object):
    def __init__(self, screen):
        self.screen = screen
        self.background = Assets.BACKGROUND

        self.bird = BirdSprite()
        self.score = ScoreCounter()
        self.bird_group = pygame.sprite.RenderPlain(self.bird)
        self.walls = WallPair()
        self.hud = pygame.sprite.RenderPlain(self.score)
        self.the_end = False

    def run(self):
        clock = pygame.time.Clock()
        while True:
            det = clock.tick(FRAMES_PER_SECOND)
            self._handle_events()
            self._update(det)
            self._draw()

    def restart(self):
        if self.the_end:
            self.score.restart()
            self.bird.restart()
            self.walls.restart()
            self.the_end = False

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.bird.jump()
                elif event.key == pygame.K_ESCAPE:
                    self.restart()
            elif event.type == pygame.QUIT:
                sys.exit()

    def _update(self, det):
        if not self.the_end:
            self.bird_group.update(det)
            self.walls.update(det)
            self.hud.update(det)
            self.the_end = self.walls.is_collide(self.bird)
        else:
            self.bird.set_dead()

    def _draw(self):
        self.screen.blit(self.background, (0, 0))
        self.walls.draw(self.screen)
        self.bird_group.draw(self.screen)
        self.hud.draw(self.screen)
        pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("Flappy Bird")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    Assets.init()

    app = FlappyBird(screen)
    app.run()
