import pygame
from object_generate import Paddle, Ball, Brick, create_bricks
from physic_engine import Particle, handle_collisions

# 초기화
pygame.init()

# 화면 크기와 색상 설정
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (50, 50, 50)
WHITE = (255, 255, 255)
BLUE = (0, 150, 255)
RED = (255, 50, 50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Particle and Haptic Brick Game")
clock = pygame.time.Clock()

# 객체 생성
paddle = Paddle(WIDTH // 2 - 60, HEIGHT - 30, 120, 15, RED)
ball = Ball(WIDTH // 2, HEIGHT // 2)
bricks = create_bricks(5, 7, 90, 30, BLUE)  # 5행 7열의 벽돌 생성
particles = []  # 파티클 리스트
running = True


# 메인 루프
while running:
    screen.fill(BACKGROUND_COLOR)
    dt = clock.get_time() / 1000.0  # ms 단위를 초 단위로 변환
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 키보드 입력 처리
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle.x > 0:
        paddle.x -= 8
    if keys[pygame.K_RIGHT] and paddle.x + paddle.width < WIDTH:
        paddle.x += 8

    # 공과 패들/벽돌/경계와의 충돌 처리 및 충돌시 입자 생성
    handle_collisions(ball, paddle, bricks, particles)

    # 패들 애니메이션 업데이트
    paddle.animate()
    paddle.draw(screen)

    # 공 애니메이션 업데이트
    ball.move()
    ball.update_rotation(dt)
    ball.animate()
    ball.draw(screen)

    # 벽돌 애니메이션 업데이트
    for brick in bricks:
        brick.update_animation()
        brick.draw(screen)

    # 입자 애니메이션 업데이트
    for particle in particles[:]:
        particle.update(dt)
        particle.draw(screen)
        if particle.lifetime <= 0:
            particles.remove(particle)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
