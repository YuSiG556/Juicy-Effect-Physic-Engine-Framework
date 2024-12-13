import math
import random
import pygame

class Paddle:
    def __init__(self, x, y, width, height, color):
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)
        self.color = color
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.curve_amplitude = 0        # 휘어짐 정도 (현재 진폭)
        self.curve_decay = 0.92         # 감쇠율 (점점 줄어드는 비율)
        self.max_curve_amplitude = 50   # 초기 휘어짐 크기
        self.oscillation_speed = 0.2    # 진동 속도
        self.time = math.pi / 2         # 초기값을 아래 방향(-1)으로 설정

    def bounce(self):
        self.curve_amplitude = self.max_curve_amplitude  # 충돌 시 패들 최대 휘어짐 시작
        self.time = math.pi / 2

    def animate(self):
        if self.curve_amplitude > 0.1:           # 패들 진동 진폭이 남아 있을 때만 동작
            self.time += self.oscillation_speed  # 시간 증가
            # 감쇠 진동 계산
            self.curve_amplitude *= self.curve_decay            # 패들 진폭 감소
            self.curve_amplitude = max(self.curve_amplitude, 0) # 최소값 보장

    def draw(self, screen):
        points = []

        # 상단 곡선 계산
        for i in range(self.width + 1):
            dx = i - self.width // 2
            dy = int(self.curve_amplitude * math.sin(self.time) * (1 - (dx / (self.width / 2))**2))
            points.append((self.x + i, self.y + dy))

        # 하단 곡선 계산
        for i in range(self.width, -1, -1):
            dx = i - self.width // 2
            dy = int(self.curve_amplitude * math.sin(self.time) * (1 - (dx / (self.width / 2))**2))
            points.append((self.x + i, self.y + self.height + dy))

        pygame.draw.polygon(screen, self.color, points)

        # 패들 충돌 박스 업데이트
        self.rect.update(self.x, self.y, self.width, self.height)

class Ball:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.speed = [0, -5]
        self.squish_factor = 1.0            # 찌그러짐 정도 (1.0이 원래 크기)
        self.target_squish = 1.0            # 목표 찌그러짐 (원래 상태로 복귀)
        self.squish_recovery_speed = 0.05   # 복구 속도
        self.angular_velocity = 0           # 각속도 (회전 효과)
                          
    def move(self):
        self.rect.x += self.speed[0]
        self.rect.y += self.speed[1]

    def update_rotation(self, dt):  # 각속도를 반영한 회전 업데이트
        self.rect = self.rect.move(int(self.angular_velocity * dt), 0)

    def bounce_on_collision(self):
        self.squish_factor = 0.5  # 공이 패들에 부딪힐 때 찌그러짐
        self.target_squish = 1.0  # 원래 크기로 복구하도록 설정

    def animate(self):
        if abs(self.squish_factor - self.target_squish) > 0.01:
            self.squish_factor += (
                self.squish_recovery_speed
                * (self.target_squish - self.squish_factor)
            )

    def draw(self, screen):
        """
        공을 화면에 그리되 찌그러짐 상태에 따라 크기를 조정
        """
        width = int(self.rect.width / self.squish_factor)
        height = int(self.rect.height * self.squish_factor)
        ball_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(ball_surface, (255, 255, 255), (0, 0, width, height))
        screen.blit(
            ball_surface,
            (self.rect.centerx - width // 2, self.rect.centery - height // 2),
        )

class Brick:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.destroyed = False
        self.is_animating = False  # 애니메이션 진행 중 여부
        self.scale_factor = 1.0  # 현재 크기 배율
        self.target_scale = 1.0  # 목표 크기 배율
        self.scaling_speed = 0.005  # 크기 변화 속도

    def animate_hit(self):
        """
        벽돌이 충돌되었을 때 애니메이션 효과를 시작.
        """
        self.is_animating = True
        self.target_scale = 1.08  # 확대 배율

    def update_animation(self):
        """
        애니메이션 프레임 업데이트.
        """
        if self.is_animating:
            if self.scale_factor < self.target_scale:
                # 점진적으로 벽돌 확대
                self.scale_factor += self.scaling_speed
                if self.scale_factor >= self.target_scale:
                    self.target_scale = 1.0  # 축소 목표로 설정
            elif self.scale_factor > self.target_scale:
                # 점진적으로 벽돌 축소
                self.scale_factor -= self.scaling_speed
                if self.scale_factor <= 1.0:
                    self.scale_factor = 1.0
                    self.is_animating = False  # 애니메이션 종료

    def draw(self, screen):
        """
        현재 스케일에 맞춰 벽돌 렌더링.
        """
        if not self.destroyed:  # 파괴된 벽돌은 렌더링하지 않음
            scaled_width = int(self.rect.width * self.scale_factor)
            scaled_height = int(self.rect.height * self.scale_factor)
            scaled_x = self.rect.centerx - scaled_width // 2
            scaled_y = self.rect.centery - scaled_height // 2

            scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
            pygame.draw.rect(screen, self.color, scaled_rect)

def create_bricks(rows, cols, brick_width, brick_height, brick_color):
    bricks = []
    for x in range(cols):
        for y in range(rows):
            bricks.append(Brick(x * (brick_width + 10) + 10, y * (brick_height + 10) + 10, brick_width, brick_height, brick_color))
    return bricks
