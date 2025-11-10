# game.py
import pygame
from scenes import MapScene

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Mini Pokemon")
        self.clock = pygame.time.Clock()
        self.running = True
        # 누적 획득 경험치 추적
        self.total_exp = 0
        # 도망 횟수 추적 (2회 이상이면 게임오버)
        self.flee_count = 0
        # 게임오버 사유(문자열)를 저장
        self.last_gameover_reason = None

        # 처음에는 필드 씬부터 시작
        self.current_scene = MapScene(self)

    def change_scene(self, new_scene):
        self.current_scene = new_scene

    def restart(self):
        """게임을 다시 시작합니다: 누적 EXP 초기화 및 새 MapScene 로 이동."""
        self.total_exp = 0
        self.flee_count = 0
        self.last_gameover_reason = None
        # 새로운 맵 씬을 만들어 초기 상태로 돌아갑니다.
        from scenes import MapScene
        self.current_scene = MapScene(self)

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000  # 초 단위 delta time

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            self.current_scene.handle_events(events)
            self.current_scene.update(dt)
            self.current_scene.draw(self.screen)

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
