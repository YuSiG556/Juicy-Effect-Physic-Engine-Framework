import math
import random
import pygame

class Particle:
    def __init__(self, position, velocity, size, lifetime, color):
        self.position = pygame.Vector2(position)    # 파티클의 초기 위치
        self.velocity = pygame.Vector2(velocity)    # 파티클의 초기 속도
        self.size = size                            # 파티클의 크기
        self.lifetime = lifetime                    # 파티클의 수명
        self.color = pygame.Color(*color)           # 파티클의 색상
        self.initial_lifetime = lifetime            # 초기 수명 (투명도 계산에 사용)

    
    @classmethod
    def generate_particles(cls, position, num_particles, \
        speed_range, angle_range, color=(255, 255, 255)):
        """
        입자 생성 및 입자의 위치, 속도, 분포, 크기, 색깔 등을 결정하는 메서드
        """
        particles = []
        for _ in range(num_particles):
            angle = random.uniform(angle_range[0], angle_range[1])
            noise = random.gauss(0, 2)  # 각도 노이즈(평균, 표준편차)   
            speed = random.uniform(speed_range[0], speed_range[1])
            velocity = pygame.Vector2(math.cos(angle + noise), math.sin(angle + noise)) * speed
            
            offset_x = random.gauss(0, 20)   # Gaussian 분포로 위치 분산
            offset_y = random.gauss(0, 20)
            
            random_color = (
                random.randint(200, 255),
                random.randint(100, 200),
                random.randint(50, 100)
            )
            particle_color = pygame.Color(*random_color)
            particle_color.a = random.randint(100, 255)  # 초기 투명도
            
            particles.append(
                cls(
                    position=(position[0] + offset_x, position[1] + offset_y),
                    velocity=velocity,
                    size=random.randint(3, 6),
                    lifetime=random.randint(20, 50),
                    color=particle_color
                )
            )
        return particles    

    def update(self, dt):
        """
        파티클의 위치와 속도를 업데이트하며 물리적 동작 적용.
        """
        # 중력 효과
        gravity = pygame.Vector2(0, 300)  # 중력 값
        self.velocity += gravity * dt

        # 마찰 효과
        friction = 0.95  # 속도 감소를 위한 마찰 계수
        self.velocity *= friction

        # 위치 업데이트
        self.position += self.velocity * dt

        # 크기 점진적 감소
        self.size = max(1, self.size - 0.1)

        # 투명도 점진적 감소
        alpha = max(0, int(255 * (self.lifetime / self.initial_lifetime)))
        self.color.a = alpha

        # 수명 감소
        self.lifetime -= 1

    def draw(self, screen):
        """
        파티클을 화면에 그립니다.
        """
        if self.lifetime > 0:  # 살아 있는 파티클만 그리기
            surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, self.color, (self.size, self.size), self.size)
            screen.blit(surface, (self.position.x - self.size, self.position.y - self.size))

def apply_torque(velocity, contact_point, center_of_mass, width, height):
    """
    충돌 시 발생하는 토크를 계산하여 각속도를 반환.
    """
    # 공의 크기를 기반으로 질량과 관성 모멘트 설정
    mass = (width + height) / 2                     # 공의 크기에 비례한 질량 가정
    radius = width / 2                              # 공의 반지름
    moment_of_inertia = 0.5 * mass * radius ** 2    # 관성 모멘트 계산

    torque = (contact_point - center_of_mass).cross(velocity)
    angular_velocity = torque / moment_of_inertia   # 각속도 = 토크 / 관성 모멘트
    return angular_velocity

def reflect_vector(velocity, normal, restitution=1.0):
    """
    벡터 기반 반사 계산. apply_torque로 구한 각속도로 방향 조정하여 단순 반사가 아닌 난반사 구현.
    """
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    reflected = [
        velocity[0] - 2 * dot_product * normal[0],
        velocity[1] - 2 * dot_product * normal[1],
    ]
    reflected[0] *= restitution
    reflected[1] *= restitution
    
    # 각속도로 방향 조정 추가
    angular_adjustment = math.atan2(reflected[1], reflected[0])  # 기존 반사각 계산
    angular_velocity = math.sqrt(velocity[0]**2 + velocity[1]**2) * 0.01  # 가정된 각속도 영향
    angular_adjustment += angular_velocity  # 각속도에 따른 조정
    
    reflected = [
        math.cos(angular_adjustment) * math.sqrt(reflected[0]**2 + reflected[1]**2),
        math.sin(angular_adjustment) * math.sqrt(reflected[0]**2 + reflected[1]**2),
    ]
    
    return reflected

def calculate_reflection_angle(ball, paddle):
    """
    패들과 공의 충돌 반사 각도 계산. apply_torque로 구한 각속도로 방향 조정하여 단순 반사가 아닌 난반사 구현.
    패들과 공의 충돌 위치에 따라 다른 반사 각도 리턴
    """
    relative_intersect_x = (ball.rect.centerx - paddle.x) / paddle.width
    reflection_angle = math.radians(150 * (relative_intersect_x - 0.5))  # 기존 반사 각도 계산

    # 각속도로 각도 조정
    angular_velocity = ball.angular_velocity  # 공의 각속도 활용
    delta_angle = angular_velocity * 0.1  # 각속도의 영향을 가중치와 함께 조정
    reflection_angle += delta_angle

    return reflection_angle

def handle_collisions(ball, paddle, bricks, particles):
    """
    공과 경계/패들/벽돌의 충돌 처리
    """    
    # 1. 경계 충돌(reflect_vector 적용)
    if ball.rect.left <= 0:  # 1. 왼쪽 벽과의 충돌
        ball.speed = reflect_vector(ball.speed, [1, 0]) # 법선 벡터 [1, 0] (오른쪽으로 반사)
        ball.rect.left = 1
        ball.bounce_on_collision()  # 충돌 시 공의 찌그러짐 구현
        
        for brick in bricks:
            brick.animate_hit()  # 충돌 시 벽의 확대 및 축소 구현
        
        particles.extend(
            Particle.generate_particles(    # 충돌 시 입자 구현
                position=(ball.rect.left, ball.rect.centery),   # 충돌 위치
                num_particles=30,
                speed_range=(50, 100),
                angle_range=(math.pi / 4, 3 * math.pi / 4),     # 오른쪽으로 확산
                color=(150, 150, 255)
            )
        )

    elif ball.rect.right >= 800:  # 2. 오른쪽 벽과의 충돌
        ball.speed = reflect_vector(ball.speed, [-1, 0])    # 법선 벡터 [-1, 0] (왼쪽으로 반사)
        ball.rect.right = 799
        ball.bounce_on_collision()
        
        for brick in bricks:
            brick.animate_hit()

        particles.extend(
            Particle.generate_particles(
                position=(ball.rect.right, ball.rect.centery),   
                num_particles=30,
                speed_range=(50, 100),
                angle_range=(5 * math.pi / 4, 7 * math.pi / 4), # 왼쪽으로 확산
                color=(150, 150, 255)
            )
        )
        
    if ball.rect.top <= 0:  # 3. 상단 벽과의 충돌
        ball.speed = reflect_vector(ball.speed, [0, 1])  # 법선 벡터 [0, 1] (아래로 반사)
        ball.rect.top = 1
        ball.bounce_on_collision()

        for brick in bricks:
            brick.animate_hit()

        particles.extend(
            Particle.generate_particles(
                position=(ball.rect.centerx, ball.rect.top),    # 충돌 위치
                num_particles=30,
                speed_range=(50, 100),
                angle_range=(3 * math.pi / 4, 5 * math.pi / 4), # 아래쪽으로 확산
                color=(150, 255, 150)
            )
        )

    # 2. 패들 충돌(calculate_reflection_angle, apply_torque 적용)
    if ball.rect.colliderect(paddle.rect):
        ball.bounce_on_collision()
        reflection_angle = calculate_reflection_angle(ball, paddle)
        speed = max(4, math.sqrt(ball.speed[0] ** 2 + ball.speed[1] ** 2))
        ball.speed[0] = speed * math.sin(reflection_angle)
        ball.speed[1] = -abs(speed * math.cos(reflection_angle))

        # 공 각속도 조정()
        contact_point = pygame.Vector2(ball.rect.centerx, ball.rect.centery)
        center_of_mass = pygame.Vector2(paddle.rect.centerx, paddle.rect.centery)
        width, height = ball.rect.width, ball.rect.height
        ball.angular_velocity += apply_torque(ball.speed, contact_point, center_of_mass, width, height)

        # 패들 애니메이션 및 파티클 생성
        paddle.bounce()     # 패들의 휘어짐 구현

        for brick in bricks:
            brick.animate_hit()

        particles.extend(
            Particle.generate_particles(
                position=(ball.rect.centerx, paddle.rect.top),
                num_particles=30,
                speed_range=(50, 150),
                angle_range=(-math.pi / 4, math.pi / 4),
                color=(255, 150, 50)
            )
        )

    # 3.벽돌 충돌 처리
    for brick in bricks:
        if not brick.destroyed and ball.rect.colliderect(brick.rect):
            brick.destroyed = True  # 벽돌 파괴
            ball.bounce_on_collision()
            brick.animate_hit()
            
            # 최소 겹침 방향 계산
            overlap_top = abs(ball.rect.bottom - brick.rect.top)
            overlap_bottom = abs(ball.rect.top - brick.rect.bottom)
            overlap_left = abs(ball.rect.right - brick.rect.left)
            overlap_right = abs(ball.rect.left - brick.rect.right)

            # 충돌 방향에 따라 반사
            if min(overlap_top, overlap_bottom, overlap_left, overlap_right) == overlap_top:
                ball.speed = reflect_vector(ball.speed, [0, -1])
                ball.rect.bottom = brick.rect.top - 1
                particle_position = (ball.rect.centerx, brick.rect.top) 
            elif min(overlap_top, overlap_bottom, overlap_left, overlap_right) == overlap_bottom:
                ball.speed = reflect_vector(ball.speed, [0, 1])
                ball.rect.top = brick.rect.bottom + 1
                particle_position = (ball.rect.centerx, brick.rect.bottom)  
            elif min(overlap_top, overlap_bottom, overlap_left, overlap_right) == overlap_left:
                ball.speed = reflect_vector(ball.speed, [-1, 0])
                ball.rect.right = brick.rect.left - 1
                particle_position = (brick.rect.left, ball.rect.centery)  
            elif min(overlap_top, overlap_bottom, overlap_left, overlap_right) == overlap_right:
                ball.speed = reflect_vector(ball.speed, [1, 0])
                ball.rect.left = brick.rect.right + 1
                particle_position = (brick.rect.right, ball.rect.centery)  

            for brick in bricks:
                brick.animate_hit()

            # 파티클 생성
            particles.extend(
                Particle.generate_particles(
                    position=particle_position,
                    num_particles=30,
                    speed_range=(50, 200),
                    angle_range=(0, 2 * math.pi),
                    color=(random.randint(200, 255), random.randint(50, 150), random.randint(50, 150))
                )
            )