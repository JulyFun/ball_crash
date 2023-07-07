import pygame
import random
import time
import math

EPS = 1e-12
COLLIDE_TREE_MIN_SIZE = 5

FPS = 59
FPS_TIME = 1. / FPS
COLOR_BG = pygame.Color(23, 23, 23)
PIX_PER_METER = 100
SCREEN_HEIGHT = 976
SCREEN_WIDTH = 1688

MU = 0.3
DOWNWARD_G = 9.8
INTER_G = 6.67 * 1e-11
# K_AIR = 1.2258
K_AIR = 1e10
KEY_ACC = 25
KEY_ACC_FOR_ALL = True
K_ELASTIC = 1e12

RIGID = 5
DEAD_COUNT = 1
BALL_COUNT = RIGID * RIGID - 1

DOWNWARD_GRAVITY_ON = False
INTER_GRAVITY_ON = True

ELASTIC_COLLISION_ON = True

AVOID_INTER_SUBMERGE = False
CANCEL_INTER_GRAVITY_WHEN_COLLIDE = True
AVOID_EDGE_SUBMERGE = True

# 可以控制的球
WEIGHT1 = 1e12
# 不可控制的球
WEIGHT2 = 1e10

IMG_SRC1 = 'pic/saturn-256.png'
IMG_SRC2 = 'pic/saturn-48.png'
RIGID_DIS = 2.0


RIGID_ELASTIC_NUM = 0


def get_dis(x1, y1, x2, y2):
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def get_vec(x1, y1, x2, y2):
    vec_x, vec_y = x2 - x1, y2 - y1
    vec_len = get_dis(x1, y1, x2, y2)
    if vec_len > EPS:
        vec_x /= vec_len
        vec_y /= vec_len
    return vec_x, vec_y


class MainGame:
    _display = pygame.display
    window = None
    ball_list = []
    elastic_list = []
    clock = pygame.time.Clock()
    collides = []
    hide_ball0 = False
    fps_pause = False

    def start_game(self):
        self._display.init()
        self.window = self._display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
        self.create_my_ball()
        self.create_dead_ball()
        # self.elastic_list.append(Elastic(self.ball_list[0],
        #                                  self.ball_list[1],
        #                                  balance_len=1.))

        def legal(x, y):
            return 0 <= x < RIGID and 0 <= y < RIGID

        # 生成弹性链
        for i in range(RIGID * RIGID):
            x = i // RIGID
            y = i % RIGID
            for x1 in range(x - RIGID_ELASTIC_NUM, x + RIGID_ELASTIC_NUM + 1):
                for y1 in range(y - RIGID_ELASTIC_NUM, y + RIGID_ELASTIC_NUM + 1):
                    if (not legal(x1, y1)) or (x1 == x and y1 == y):
                        continue
                    num = x1 * RIGID + y1
                    if i < num:
                        self.elastic_list.append(Elastic(self.ball_list[i],
                                                         self.ball_list[num],
                                                         get_dis(x, y, x1, y1) * RIGID_DIS))

        self._display.set_caption("球球模拟器")

        last_time = 0
        max_power = 0.
        while True:
            self.clock.tick(FPS)

            time_begin = time.time()

            self.window.fill(COLOR_BG)

            self.get_event()
            if not self.fps_pause:
                self.update_all_balls(FPS_TIME)

            for d in self.ball_list:
                d.display(self.window)  # !!!
            for e in self.elastic_list:
                e.display(self.window)
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
        # my = Ball(random.random() * (SCREEN_WIDTH / PIX_PER_METER),
        #           random.random() * ((SCREEN_HEIGHT / 2 + 10) / PIX_PER_METER),
        #           # 2,
        #           img_src=IMG_SRC1, mass=WEIGHT1)

        my = Ball(RIGID_DIS, RIGID_DIS,
                  img_src=IMG_SRC1, mass=WEIGHT1)
        self.ball_list.append(my)  # 可操作的球员总是在 0 号

    def create_dead_ball(self):
        # for i in range(BALL_COUNT):
        #     self.ball_list.append(Ball(random.random() * (SCREEN_WIDTH / PIX_PER_METER),
        #                                random.random() * ((SCREEN_HEIGHT / 2 + 10) / PIX_PER_METER),
        #                                # 2,
        #                                img_src=IMG_SRC2, mass=WEIGHT2))
        for i in range(BALL_COUNT):
            x = (i + 1) // RIGID
            y = (i + 1) % RIGID
            self.ball_list.append(Ball(RIGID_DIS + x * RIGID_DIS, RIGID_DIS + y * RIGID_DIS,
                                  img_src=IMG_SRC2, mass=WEIGHT2))

    def collide_split(self, node_list: list, x1, y1, x2, y2):
        if len(node_list) == 0:
            return

        points = [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]
        pygame.draw.lines(self.window, (0, 127, 0), True, points, 1)
        pygame.draw.line(self.window, (255, 255, 255),
                         (25, 50), (25 + PIX_PER_METER, 50), 1)

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

    def inter_gravity2(self):
        g_sum_x, g_sum_y = 0., 0.
        m_sum = 0.
        for d in self.ball_list:
            g_sum_x += d.x * d.mass
            g_sum_y += d.y * d.mass
            m_sum += d.mass
        for d in self.ball_list:
            g_sum_x_no_d = g_sum_x - d.x * d.mass
            g_sum_y_no_d = g_sum_y - d.y * d.mass
            m_sum_no_d = m_sum - d.mass
            center_x, center_y = g_sum_x_no_d / m_sum_no_d, g_sum_y_no_d / m_sum_no_d
            dis = ((center_x - d.x) ** 2 + (center_y - d.y) ** 2) ** 0.5
            vec_x, vec_y = center_x - d.x, center_y - d.y
            vec_len = (vec_x ** 2 + vec_y ** 2) ** 0.5
            vec_x /= vec_len
            vec_y /= vec_len
            f = INTER_G * d.mass * m_sum_no_d / dis ** 2
            d.speed_x += f * vec_x / d.mass * FPS_TIME
            d.speed_y += f * vec_y / d.mass * FPS_TIME

    def inter_gravity(self):
        inter = []
        for d1 in self.ball_list:
            for d2 in self.ball_list:
                if d1 != d2 and (d1, d2) not in inter and (d2, d1) not in inter:
                    if self.hide_ball0 and (d1 == self.ball_list[0] or d2 == self.ball_list[0]):
                        continue
                    if CANCEL_INTER_GRAVITY_WHEN_COLLIDE and pygame.sprite.collide_mask(d1, d2):
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

    def update_all_balls(self, t):

        for d in self.ball_list:
            d.move()
            d.hit_edge()
        for e in self.elastic_list:
            e.affect(t)

        self.collides = []
        self.collide_split(self.ball_list, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

        # for d1 in self.ball_list:
        #     for d2 in self.ball_list:
        #         if (d1, d2) in self.collides or (d2, d1) in self.collides:
        #             continue
        #         if d1 != d2 and d1.hit_other(d2):
        #             self.collides.append((d1, d2))

        if INTER_GRAVITY_ON:
            self.inter_gravity()

    def get_event(self):
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                self.end_game()
            di_di = {
                pygame.K_LEFT: 'L',
                pygame.K_RIGHT: 'R',
                pygame.K_UP: 'U',
                pygame.K_DOWN: 'D',
            }

            if event.type == pygame.KEYDOWN:
                if event.key in di_di:
                    if KEY_ACC_FOR_ALL:
                        for ball in self.ball_list:
                            ball.power[di_di[event.key]] = True
                    else:
                        self.ball_list[0].power[di_di[event.key]] = True
                elif event.key == pygame.K_g:
                    self.hide_ball0 = not self.hide_ball0
                    if self.hide_ball0:
                        self.ball_list[0].image.set_alpha(99)
                    else:
                        self.ball_list[0].image.set_alpha(255)
                elif event.key == pygame.K_SPACE:
                    self.fps_pause = not self.fps_pause

            elif event.type == pygame.KEYUP:
                if event.key in di_di:
                    if KEY_ACC_FOR_ALL:
                        for ball in self.ball_list:
                            ball.power[di_di[event.key]] = False
                    else:
                        self.ball_list[0].power[di_di[event.key]] = False

    @staticmethod
    def end_game():
        exit()


class BaseItem(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)


class Ball(BaseItem):
    def __init__(self, x, y, img_src='pic/circle.png', mass=1.0, elastic_list=[]):
        super(Ball, self).__init__()
        self.mass = mass
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
            norm_speed_x, norm_speed_y = self.speed_x / \
                vec_speed_len, self.speed_y / vec_speed_len
            # 摩擦力
            self.speed_x += -MU * DOWNWARD_G * norm_speed_x * FPS_TIME
            self.speed_y += -MU * DOWNWARD_G * norm_speed_y * FPS_TIME
            # 空气阻力
            self.speed_x += \
                -K_AIR * vec_speed_len ** 2 * self.radius ** 2 * \
                math.pi * norm_speed_x / self.mass * FPS_TIME
            self.speed_y += \
                -K_AIR * vec_speed_len ** 2 * self.radius ** 2 * \
                math.pi * norm_speed_y / self.mass * FPS_TIME

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

        if DOWNWARD_GRAVITY_ON:
            self.speed_y += DOWNWARD_G * FPS_TIME

        self.rect.left = int(self.x * PIX_PER_METER - self.rect.width / 2)
        self.rect.top = int(self.y * PIX_PER_METER - self.rect.height / 2)

    def receive_f(self, f, vec_x, vec_y, t):
        a = f / self.mass
        self.speed_x += a * vec_x * t
        self.speed_y += a * vec_y * t

    def hit_other(self, other) -> bool:
        # 弹性碰撞
        if pygame.sprite.collide_mask(self, other):
            vec_x, vec_y = other.x - self.x, other.y - self.y
            vec_speed_x, vec_speed_y = other.speed_x - \
                self.speed_x, other.speed_y - self.speed_y
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
            other.rect.left = int(
                other.x * PIX_PER_METER - other.rect.width / 2)
            other.rect.top = int(
                other.y * PIX_PER_METER - other.rect.height / 2)

            self.speed_x = \
                v_ori_x1 + ((self.mass - other.mass) * vx1 + 2 * other.mass * vx2) / \
                (self.mass + other.mass)
            other.speed_x = \
                v_ori_x2 + ((other.mass - self.mass) * vx2 + 2 * self.mass * vx1) / \
                (self.mass + other.mass)
            self.speed_y = \
                v_ori_y1 + ((self.mass - other.mass) * vy1 + 2 * other.mass * vy2) / \
                (self.mass + other.mass)
            other.speed_y = \
                v_ori_y2 + ((other.mass - self.mass) * vy2 + 2 * self.mass * vy1) / \
                (self.mass + other.mass)
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


class Elastic:
    def __init__(self, d1: Ball, d2: Ball, balance_len):
        self.d1 = d1
        self.d2 = d2
        self.balance_len = balance_len

    def affect(self, t):
        # 从 1 指向 2
        vec_x, vec_y = get_vec(self.d1.x, self.d1.y, self.d2.x, self.d2.y)
        dis = get_dis(self.d1.x, self.d1.y, self.d2.x, self.d2.y)
        f = K_ELASTIC * (dis - self.balance_len)
        self.d1.receive_f(f, vec_x, vec_y, t)
        self.d2.receive_f(f, -vec_x, -vec_y, t)

    def display(self, window: pygame.Surface):
        pygame.draw.line(window, (255, 255, 255),
                         (self.d1.x * PIX_PER_METER, self.d1.y * PIX_PER_METER),
                         (self.d2.x * PIX_PER_METER, self.d2.y * PIX_PER_METER),
                         2)


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
