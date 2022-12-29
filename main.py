import pygame
import random
import time
import math

EPS = 1e-12
COLLIDE_TREE_MIN_SIZE = 5

FPS = 59
FPS_TIME = 1. / FPS
COLOR_BG = pygame.Color(23, 23, 23)
PIX_PER_METER = 75
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 600

MU = 0.0
G = 9.8
INTER_G = 6.67 * 1e-11
# K_AIR = 1.2258
K_AIR = 0
KEY_ACC = 25

DEAD_COUNT = 1
BALL_COUNT = 5

GRAVITY_SWITCH = False
INTER_GRAVITY_SWITCH = True

ELASTIC_SWITCH = True

AVOID_INTER_SUBMERGE = False
AVOID_EDGE_SUBMERGE = False

WEIGHT1 = 1e9
WEIGHT2 = 1e9

IMG_SRC1 = 'pic/earth_96.png'
IMG_SRC2 = 'pic/satern_16.png'


class MainGame:
    _display = pygame.display
    window = None
    ball_list = []
    clock = pygame.time.Clock()
    collides = []
    hide_ball0 = False
    fps_pause = False

    def start_game(self):
        self._display.init()
        self.window = self._display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
        self.create_my_ball()
        self.create_dead_ball()
        self._display.set_caption("球球模拟器")

        last_time = 0
        max_power = 0.
        while True:
            self.clock.tick(FPS)

            time_begin = time.time()

            self.window.fill(COLOR_BG)

            self.get_event()
            if not self.fps_pause:
                self.update_all_ball()

            for d in self.ball_list:
                d.display(self.window)  # !!!
            self._display.update()

            time_end = time.time()

            max_power = max(max_power, (time_end - time_begin) / FPS_TIME)

            timestamp = int(round(time.time() * 1000))
            if timestamp - last_time > 500:
                last_time = timestamp
                print('FPS:', self.clock.get_fps())
                print('Power used:', max_power * 100, '%')
                max_power = 0.

    def create_my_ball(self):
        my = Ball(random.random() * (SCREEN_WIDTH / PIX_PER_METER),
                  random.random() * ((SCREEN_HEIGHT / 2 + 10) / PIX_PER_METER),
                  # 2,
                  img_src=IMG_SRC1, weight=WEIGHT1)
        self.ball_list.append(my)  # 可操作的球员总是在 0 号

    def create_dead_ball(self):
        # y = 1.
        # place_list = []
        # for i in range(7):
        #     place_list.append(float(i + 1))

        # for _ in range(DEAD_COUNT):
        #     c = random.randrange(len(place_list))
        #     dead = Ball(place_list[c], y, img_src='pic/satern_big.png', weight=1.0)
        #     del place_list[c]
        #     self.ball_list.append(dead)
        for i in range(BALL_COUNT):
            self.ball_list.append(Ball(random.random() * (SCREEN_WIDTH / PIX_PER_METER),
                                       random.random() * ((SCREEN_HEIGHT / 2 + 10) / PIX_PER_METER),
                                       # 2,
                                       img_src=IMG_SRC2, weight=WEIGHT2))

    def collide_split(self, node_list: list, x1, y1, x2, y2):
        if len(node_list) == 0:
            return

        points = [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]
        pygame.draw.lines(self.window, (0, 127, 0), True, points, 1)
        pygame.draw.line(self.window, (255, 255, 255), (25, 50), (25 + PIX_PER_METER, 50), 1)

        if len(node_list) <= COLLIDE_TREE_MIN_SIZE:
            for d1 in node_list:
                for d2 in node_list:
                    if (d1, d2) in self.collides or (d2, d1) in self.collides:
                        continue
                    if d1 != d2 and d1.hit_other(d2):
                        self.collides.append((d1, d2))
            return
        father_list = []
        son_list = []
        x0 = (x1 + x2) / 2
        y0 = (y1 + y2) / 2
        for d in node_list:
            if d.rect.left <= x0 < d.rect.left + d.rect.width or d.rect.top <= y0 < d.rect.top + d.rect.height:
                father_list.append(d)
            else:
                son_list.append(d)
        for d1 in father_list:
            for d2 in node_list:
                if (d1, d2) in self.collides or (d2, d1) in self.collides:
                    continue
                if d1 != d2 and d1.hit_other(d2):
                    self.collides.append((d1, d2))
        son_list1 = []
        son_list2 = []
        son_list3 = []
        son_list4 = []
        for d in son_list:
            if d.rect.left + d.rect.width < 0. or d.rect.left > SCREEN_WIDTH or \
                    d.rect.top + d.rect.height < 0. or d.rect.top > SCREEN_HEIGHT:
                continue
            if d.rect.left > x0 and d.rect.top > y0:
                son_list1.append(d)
            elif d.rect.left + d.rect.width <= x0 and d.rect.top > y0:
                son_list2.append(d)
            elif d.rect.left + d.rect.width <= x0 and d.rect.top + d.rect.height <= y0:
                son_list3.append(d)
            elif d.rect.left > x0 and d.rect.top + d.rect.height <= y0:
                son_list4.append(d)
        self.collide_split(son_list1, x0, y0, x2, y2)
        self.collide_split(son_list2, x1, y0, x0, y2)
        self.collide_split(son_list3, x1, y1, x0, y0)
        self.collide_split(son_list4, x0, y1, x2, y0)

    def inter_gravity(self):
        # g_sum_x, g_sum_y = 0., 0.
        # m_sum = 0.
        # for d in self.ball_list:
        #     g_sum_x += d.x * d.weight
        #     g_sum_y += d.y * d.weight
        #     m_sum += d.weight
        # for d in self.ball_list:
        #     g_sum_x_no_d = g_sum_x - d.x * d.weight
        #     g_sum_y_no_d = g_sum_y - d.y * d.weight
        #     m_sum_no_d = m_sum - d.weight
        #     center_x, center_y = g_sum_x_no_d / m_sum_no_d, g_sum_y_no_d / m_sum_no_d
        #     dis = ((center_x - d.x) ** 2 + (center_y - d.y) ** 2) ** 0.5
        #     vec_x, vec_y = center_x - d.x, center_y - d.y
        #     vec_len = (vec_x ** 2 + vec_y ** 2) ** 0.5
        #     vec_x /= vec_len
        #     vec_y /= vec_len
        #     f = INTER_G * d.weight * m_sum_no_d / dis ** 2
        #     d.speed_x += f * vec_x / d.weight * FPS_TIME
        #     d.speed_y += f * vec_y / d.weight * FPS_TIME

        inter = []
        for d1 in self.ball_list:
            for d2 in self.ball_list:
                if d1 != d2 and (d1, d2) not in inter and (d2, d1) not in inter:
                    if self.hide_ball0 and (d1 == self.ball_list[0] or d2 == self.ball_list[0]):
                        continue
                    if ELASTIC_SWITCH and pygame.sprite.collide_mask(d1, d2):
                        continue
                    dis = ((d1.x - d2.x) ** 2 + (d1.y - d2.y) ** 2) ** 0.5
                    vec_x, vec_y = d2.x - d1.x, d2.y - d1.y
                    vec_len = (vec_x ** 2 + vec_y ** 2) ** 0.5
                    vec_x /= vec_len
                    vec_y /= vec_len
                    f = INTER_G * d1.mass * d2.mass / dis ** 2
                    d1.speed_x += f * vec_x / d1.mass * FPS_TIME
                    d1.speed_y += f * vec_y / d1.mass * FPS_TIME
                    d2.speed_x += -f * vec_x / d2.mass * FPS_TIME
                    d2.speed_y += -f * vec_y / d2.mass * FPS_TIME
                    inter.append((d1, d2))

    def update_all_ball(self):

        for d in self.ball_list:
            d.move()
            d.hit_edge()

        self.collides = []
        self.collide_split(self.ball_list, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

        # for d1 in self.ball_list:
        #     for d2 in self.ball_list:
        #         if (d1, d2) in self.collides or (d2, d1) in self.collides:
        #             continue
        #         if d1 != d2 and d1.hit_other(d2):
        #             self.collides.append((d1, d2))

        if INTER_GRAVITY_SWITCH:
            self.inter_gravity()

    def get_event(self):
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                self.end_game()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.ball_list[0].power['L'] = True
                elif event.key == pygame.K_RIGHT:
                    self.ball_list[0].power['R'] = True
                elif event.key == pygame.K_UP:
                    self.ball_list[0].power['U'] = True
                elif event.key == pygame.K_DOWN:
                    self.ball_list[0].power['D'] = True
                elif event.key == pygame.K_g:
                    self.hide_ball0 = not self.hide_ball0
                    if self.hide_ball0:
                        self.ball_list[0].image.set_alpha(99)
                    else:
                        self.ball_list[0].image.set_alpha(255)
                elif event.key == pygame.K_SPACE:
                    self.fps_pause = not self.fps_pause

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.ball_list[0].power['L'] = False
                elif event.key == pygame.K_RIGHT:
                    self.ball_list[0].power['R'] = False
                elif event.key == pygame.K_UP:
                    self.ball_list[0].power['U'] = False
                elif event.key == pygame.K_DOWN:
                    self.ball_list[0].power['D'] = False

    @staticmethod
    def end_game():
        exit()


class BaseItem(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)


class Ball(BaseItem):
    def __init__(self, x, y, img_src='pic/circle.png', weight=1.0):
        super(Ball, self).__init__()
        self.weight = weight
        self.image = pygame.image.load(img_src)
        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.radius = self.rect.width / 2 / PIX_PER_METER
        self.x_last = x
        self.y_last = y
        self.speed_x = 0.
        self.speed_y = 0.
        self.speed_x_last = self.speed_x
        self.speed_y_last = self.speed_y
        self.mask = pygame.mask.from_surface(self.image)
        self.power = {
            'U': False,
            'L': False,
            'D': False,
            'R': False
        }

    def move(self):
        self.x_last = self.x
        self.y_last = self.y
        self.speed_x_last = self.speed_x
        self.speed_y_last = self.speed_y

        self.x += self.speed_x * FPS_TIME
        self.y += self.speed_y * FPS_TIME

        vec_speed_len = (self.speed_x ** 2 + self.speed_y ** 2) ** 0.5
        if abs(vec_speed_len) > EPS:
            norm_speed_x, norm_speed_y = self.speed_x / vec_speed_len, self.speed_y / vec_speed_len
            # 摩擦力
            self.speed_x += -MU * G * norm_speed_x * FPS_TIME
            self.speed_y += -MU * G * norm_speed_y * FPS_TIME
            # 空气阻力
            self.speed_x += \
                -K_AIR * vec_speed_len ** 2 * self.radius ** 2 * math.pi * norm_speed_x / self.weight * FPS_TIME
            self.speed_y += \
                -K_AIR * vec_speed_len ** 2 * self.radius ** 2 * math.pi * norm_speed_y / self.weight * FPS_TIME

        # 阻力过度
        if (self.speed_x_last > EPS) != (self.speed_x > EPS):
            self.speed_x = 0.
        if (self.speed_y_last > EPS) != (self.speed_y > EPS):
            self.speed_y = 0.

        if self.power['L']:
            self.speed_x += -KEY_ACC * FPS_TIME
        if self.power['R']:
            self.speed_x += KEY_ACC * FPS_TIME
        if self.power['U']:
            self.speed_y += -KEY_ACC * FPS_TIME
        if self.power['D']:
            self.speed_y += KEY_ACC * FPS_TIME

        if GRAVITY_SWITCH:
            self.speed_y += G * FPS_TIME

        self.rect.left = int(self.x * PIX_PER_METER - self.rect.width / 2)
        self.rect.top = int(self.y * PIX_PER_METER - self.rect.height / 2)

    def hit_other(self, other) -> bool:
        # 弹性碰撞
        if pygame.sprite.collide_mask(self, other):
            vec_x, vec_y = other.x - self.x, other.y - self.y
            vec_speed_x, vec_speed_y = other.speed_x - self.speed_x, other.speed_y - self.speed_y
            if vec_x * vec_speed_x + vec_y * vec_speed_y > 0.:
                # 相对速度趋势为远离则不计算碰撞
                return False
            vec_len = (vec_x ** 2 + vec_y ** 2) ** 0.5
            if abs(vec_len) > EPS:
                vec_x, vec_y = vec_x / vec_len, vec_y / vec_len

            v_cross1 = self.speed_x * vec_x + self.speed_y * vec_y
            vx1, vy1 = v_cross1 * vec_x, v_cross1 * vec_y
            v_ori_x1, v_ori_y1 = self.speed_x - vx1, self.speed_y - vy1
            # (vx1, vy1, v_ori_x1, v_ori_y1)

            v_cross2 = other.speed_x * vec_x + other.speed_y * vec_y
            vx2, vy2 = v_cross2 * vec_x, v_cross2 * vec_y
            v_ori_x2, v_ori_y2 = other.speed_x - vx2, other.speed_y - vy2
            # print(vx2, vy2, v_ori_x2, v_ori_y2)
            # print('----')

            # 回退到上一位置 并更新碰撞位置
            if AVOID_INTER_SUBMERGE:
                self.x, self.y = self.x_last, self.y_last
            other.x += other.speed_x * FPS_TIME
            other.y += other.speed_y * FPS_TIME

            self.rect.left = int(self.x * PIX_PER_METER - self.rect.width / 2)
            self.rect.top = int(self.y * PIX_PER_METER - self.rect.height / 2)
            other.rect.left = int(other.x * PIX_PER_METER - other.rect.width / 2)
            other.rect.top = int(other.y * PIX_PER_METER - other.rect.height / 2)

            self.speed_x = \
                v_ori_x1 + ((self.weight - other.mass) * vx1 + 2 * other.mass * vx2) / \
                (self.weight + other.mass)
            other.speed_x = \
                v_ori_x2 + ((other.mass - self.weight) * vx2 + 2 * self.weight * vx1) / \
                (self.weight + other.mass)
            self.speed_y = \
                v_ori_y1 + ((self.weight - other.mass) * vy1 + 2 * other.mass * vy2) / \
                (self.weight + other.mass)
            other.speed_y = \
                v_ori_y2 + ((other.mass - self.weight) * vy2 + 2 * self.weight * vy1) / \
                (self.weight + other.mass)
            return True
        return False

    def hit_edge(self):
        if self.x * PIX_PER_METER - self.rect.width / 2 < 0:
            if AVOID_EDGE_SUBMERGE:
                self.x = self.rect.width / 2 / PIX_PER_METER
            if self.speed_x < 0.:
                self.speed_x *= -1.

        if self.x * PIX_PER_METER + self.rect.width / 2 > SCREEN_WIDTH:
            if AVOID_EDGE_SUBMERGE:
                self.x = (SCREEN_WIDTH - self.rect.width / 2) / PIX_PER_METER
            if self.speed_x > 0.:
                self.speed_x *= -1.

        if self.y * PIX_PER_METER - self.rect.height / 2 < 0:
            if AVOID_EDGE_SUBMERGE:
                self.y = self.rect.height / 2 / PIX_PER_METER
            if self.speed_y < 0.:
                self.speed_y *= -1

        if self.y * PIX_PER_METER + self.rect.height / 2 > SCREEN_HEIGHT:
            if AVOID_EDGE_SUBMERGE:
                self.y = (SCREEN_HEIGHT - self.rect.height / 2) / PIX_PER_METER
            if self.speed_y > 0.:
                self.speed_y *= -1.  # Latex 规则

    def display(self, window):
        window.blit(self.image, self.rect)


def collide(ball1: Ball, ball2: Ball):
    return ((ball1.x - ball2.x) ** 2 + (ball1.y - ball2.y) ** 2) ** 0.5 < ball1.radius + ball2.radius


def code(x, y):
    x = y ** 2


# class MyBall(Ball):
#     def __init__(self, x, y):
#         super(MyBall, self).__init__(x, y)
#
#
# class DeadBall(Ball):
#     def __init__(self, x, y):
#         super(DeadBall, self).__init__(x, y)


def main():
    game = MainGame()
    game.start_game()


main()
