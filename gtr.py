import sys
import random
import pygame
import nltk
from enum import Enum, auto
from nltk.corpus import words

class GameState(Enum):
    MENU      = auto()
    PLAYING   = auto()
    PAUSED    = auto()
    GAME_OVER = auto()

class Button:
    def __init__(self, center, radius, text, font, 
                 fill_color=(45,89,135), hover_color=(190,89,135), text_color='white', border_color='white'):
        self.x, self.y = center
        self.radius = radius
        self.text = text
        self.font = font
        self.fill_color = fill_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color

    def draw(self, surface):
        pos = pygame.mouse.get_pos()
        is_hover = (pos[0]-self.x)**2 + (pos[1]-self.y)**2 < self.radius**2
        color = self.hover_color if is_hover else self.fill_color
        pygame.draw.circle(surface, color, (self.x, self.y), self.radius)
        pygame.draw.circle(surface, self.border_color, (self.x, self.y), self.radius, 3)
        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=(self.x, self.y))
        surface.blit(txt_surf, txt_rect)

    def check_click(self, mouse_pos):
        dx, dy = mouse_pos[0]-self.x, mouse_pos[1]-self.y
        return dx*dx + dy*dy < self.radius*self.radius

class Word:
    def __init__(self, text, speed, x, y):
        self.text = text
        self.speed = speed
        self.x = x
        self.y = y

    def update(self):
        self.x -= self.speed

    def draw(self, surface, font, active_string):
        surface.blit(font.render(self.text, True, 'black'), (self.x, self.y))
        if active_string and self.text.startswith(active_string):
            surface.blit(font.render(active_string, True, 'green'), (self.x, self.y))

class TypingRacer:
    WIDTH, HEIGHT = 800, 600
    SPAWN_X_MIN, SPAWN_X_MAX = WIDTH, WIDTH + 1000
    MAX_LIVES = 5
    FPS = 60

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption('Typing Racer')
        self.clock = pygame.time.Clock()

        self.fonts = {
            'header': pygame.font.Font('assets/fonts/carre.ttf',   50),
            'word':   pygame.font.Font('assets/fonts/char2.ttf', 48),
            'button': pygame.font.Font('assets/fonts/char1.ttf',      38),
            'banner': pygame.font.Font('assets/fonts/char1.ttf',      28),
        }

        pygame.mixer.init()
        self.sounds = {
            'click': pygame.mixer.Sound('assets/sounds/sound1.mp3'),
            'woosh': pygame.mixer.Sound('assets/sounds/sound2.mp3'),
            'wrong': pygame.mixer.Sound('assets/sounds/instru.mp3'),
        }
        for s in self.sounds.values():
            s.set_volume(0.3)
        pygame.mixer.music.load('assets/sounds/sound4.mp3')
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)

        try:
            with open('high_score.txt','r') as f:
                self.high_score = int(f.read().strip())
        except:
            self.high_score = 0

        self.state         = GameState.MENU
        self.level         = 1
        self.score         = 0
        self.lives         = self.MAX_LIVES
        self.active_string = ''
        self.submit        = ''
        self.word_objects  = []

        self.choices = [True] + [False]*6

        nltk.download('words', quiet=True)
        wl = sorted(words.words(), key=len)
        self.wordlist = wl
        self.len_slices = []
        current_len = len(wl[0])
        start = 0
        for i,w in enumerate(wl):
            if len(w) != current_len:
                self.len_slices.append((current_len, start, i))
                current_len = len(w)
                start = i
        self.len_slices.append((current_len, start, len(wl)))

        self.btn_pause  = Button((self.WIDTH - 52, self.HEIGHT - 52), 35, 'II', self.fonts['button'])
        self.btn_resume = Button((260, 200),                           35, '>',  self.fonts['button'])
        self.btn_quit   = Button((460, 200),                           35, 'X',  self.fonts['button'])
        self.length_buttons = [
            Button((160 + i*80, 350), 35, str(i+2), self.fonts['button'])
            for i in range(len(self.choices))
        ]

    def run(self):
        while True:
            self.clock.tick(self.FPS)
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()

    def handle_events(self):
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                self.check_high_score()
                pygame.quit()
                sys.exit()

            if evt.type == pygame.KEYDOWN:

                if evt.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING

                if self.state == GameState.PLAYING:
                    if evt.unicode.isalpha():
                        self.active_string += evt.unicode.lower()
                        self.sounds['click'].play()
                    elif evt.key == pygame.K_BACKSPACE:
                        self.active_string = self.active_string[:-1]
                    elif evt.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.submit = self.active_string
                        self.active_string = ''

            if evt.type == pygame.MOUSEBUTTONUP and evt.button == 1:
                mx,my = evt.pos
                if self.state == GameState.PLAYING:
                    if self.btn_pause.check_click((mx,my)):
                        self.state = GameState.PAUSED
                elif self.state == GameState.PAUSED:
                    if self.btn_resume.check_click((mx,my)):
                        self.state = GameState.PLAYING
                    if self.btn_quit.check_click((mx,my)):
                        self.check_high_score()
                        pygame.quit()
                        sys.exit()
                    for i,btn in enumerate(self.length_buttons):
                        if btn.check_click((mx,my)):
                            self.choices[i] = not self.choices[i]

    def update(self):
        if self.state == GameState.PLAYING:
            if not self.word_objects:
                self.new_level()
            for w in list(self.word_objects):
                w.update()
                if w.x < -200:
                    self.word_objects.remove(w)
                    self.lives -= 1

            if self.submit:
                old = self.score
                self.score = self.check_answer(self.submit)
                self.submit = ''
                if self.score == old:
                    self.sounds['wrong'].play()

            if self.lives < 0:
                self.state = GameState.GAME_OVER

        elif self.state == GameState.GAME_OVER:
            self.reset_game()
            self.state = GameState.MENU

    def draw(self):
        self.screen.fill('gray')
        pygame.draw.rect(self.screen, (68,42,32), (0, self.HEIGHT-100, self.WIDTH, 100))
        pygame.draw.line(self.screen, 'white', (0,self.HEIGHT-100), (self.WIDTH, self.HEIGHT-100), 2)
        txt_l = self.fonts['header'].render(f'Level: {self.level}', True, 'white')
        txt_a = self.fonts['header'].render(f'"{self.active_string}"', True, 'white')
        self.screen.blit(txt_l, (10, self.HEIGHT-75))
        self.screen.blit(txt_a, (270, self.HEIGHT-75))

        if self.state in (GameState.PLAYING, GameState.PAUSED):
            for w in self.word_objects:
                w.draw(self.screen, self.fonts['word'], self.active_string)

        if self.state == GameState.PLAYING:
            self.btn_pause.draw(self.screen)

        if self.state == GameState.PAUSED:
            overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            pygame.draw.rect(overlay, (50,50,50,220), (100,100,600,400), border_radius=8)
            self.screen.blit(overlay, (0,0))

            title = self.fonts['header'].render('PAUSED', True, 'white')
            self.screen.blit(title, (340, 120))

            self.btn_resume.draw(self.screen)
            self.btn_quit.draw(self.screen)

            lbl = self.fonts['header'].render('Letter Lengths:', True, 'white')
            self.screen.blit(lbl, (110, 250))
            for i,btn in enumerate(self.length_buttons):
                btn.draw(self.screen)
                if self.choices[i]:
                    pygame.draw.circle(self.screen, 'green', (btn.x, btn.y), btn.radius, 4)

        if self.state == GameState.MENU:
            title = self.fonts['header'].render('TYPING RACER', True, 'white')
            self.screen.blit(title, (240, 220))
            play = self.fonts['banner'].render('Press ENTER to Play', True, 'white')
            self.screen.blit(play, (260, 300))
            if pygame.key.get_pressed()[pygame.K_RETURN]:
                self.state = GameState.PLAYING

        hud = self.fonts['banner'].render(f'Score: {self.score}   Lives: {max(self.lives,0)}   High: {self.high_score}', True, 'white')
        self.screen.blit(hud, (10,10))

    def new_level(self):
        self.word_objects.clear()
        vertical_space = (self.HEIGHT - 150) // max(self.level,1)
        for i in range(self.level):
            speed = random.randint(1,3)
            y = random.randint(10 + i*vertical_space, (i+1)*vertical_space)
            x = random.randint(self.SPAWN_X_MIN, self.SPAWN_X_MAX)
            valid = [s for s,c in zip(self.len_slices, self.choices) if c]
            if not valid:
                valid = [self.len_slices[0]]
            length, start, end = random.choice(valid)
            text = self.wordlist[random.randint(start, end-1)].lower()
            self.word_objects.append(Word(text, speed, x, y))
        self.level += 1

    def check_answer(self, submitted):
        for w in self.word_objects:
            if w.text == submitted:
                pts = w.speed * len(w.text) * 10
                self.word_objects.remove(w)
                self.sounds['woosh'].play()
                return self.score + pts
        return self.score

    def check_high_score(self):
        if self.score > self.high_score:
            with open('high_score.txt','w') as f:
                f.write(str(self.score))

    def reset_game(self):
        self.level = 1
        self.score = 0
        self.lives = self.MAX_LIVES
        self.word_objects.clear()
        self.active_string = ''
        self.submit = ''
        self.choices = [True] + [False]*6

if __name__ == '__main__':
    game = TypingRacer()
    game.run()
