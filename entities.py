# pygame 모듈을 불러옵니다. (게임 화면, 키보드 입력, 그래픽 처리를 위해)
import pygame

# 플레이어 캐릭터를 나타내는 클래스입니다.
# pygame의 Sprite(스프라이트) 클래스를 상속받아 화면에 표시 가능한 객체로 만듭니다.
class Player(pygame.sprite.Sprite):
    # 생성자: 플레이어의 초기 위치(x, y)와 이동 속도(speed)를 설정합니다.
    def __init__(self, x, y, speed=200):
        # 부모 클래스(Sprite)의 생성자를 먼저 호출합니다.
        super().__init__()

        # 플레이어의 이미지(모양)를 만듭니다. 32x32 크기의 사각형 Surface 생성.
        self.image = pygame.Surface((32, 32))

        # 이미지 색상을 파란색(RGB: 0,0,255)으로 채웁니다.
        self.image.fill((0, 0, 255))  # 파란 네모가 주인공

        # 사각형(rect) 속성을 만들어, 화면에서의 위치와 크기를 관리합니다.
        # topleft=(x, y)는 시작 좌표를 지정하는 부분입니다.
        self.rect = self.image.get_rect(topleft=(x, y))

        # 플레이어 이동 속도를 저장합니다. 초당 200픽셀 정도로 설정.
        self.speed = speed

    # update() 메서드: 매 프레임마다 실행되어, 키 입력에 따라 위치를 변경합니다.
    def update(self, dt, keys):
        # 이동할 방향(dx, dy)을 0으로 초기화합니다.
        dx = dy = 0

        # 왼쪽 방향키를 누르면 x축 음수 방향으로 이동합니다.
        if keys[pygame.K_LEFT]:
            dx -= self.speed * dt  # 속도 * 시간 = 이동거리

        # 오른쪽 방향키를 누르면 x축 양수 방향으로 이동합니다.
        if keys[pygame.K_RIGHT]:
            dx += self.speed * dt

        # 위쪽 방향키를 누르면 y축 음수 방향으로 이동합니다. (pygame은 위가 0)
        if keys[pygame.K_UP]:
            dy -= self.speed * dt

        # 아래쪽 방향키를 누르면 y축 양수 방향으로 이동합니다.
        if keys[pygame.K_DOWN]:
            dy += self.speed * dt

        # rect의 x, y 좌표를 갱신하여 실제로 플레이어를 이동시킵니다.
        self.rect.x += dx
        self.rect.y += dy
