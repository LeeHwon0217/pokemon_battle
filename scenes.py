# pygame 모듈을 불러옵니다. (그래픽, 이벤트 처리 등 게임의 핵심 기능 담당)
import pygame

# 추상 클래스(기본 틀)를 만들기 위해 abc 모듈을 사용합니다.
from abc import ABC, abstractmethod

# from battle import BattleScene  # 나중에 구현 예정. 현재는 주석 처리하여 순환 참조 방지

# 무작위 전투 발생 확률을 만들기 위해 random 모듈을 불러옵니다.
import random
import os

# Player 클래스를 가져옵니다. (플레이어의 움직임과 모양 담당)
from entities import Player

# 포켓몬의 능력치와 전투 데이터를 담당하는 Pokemon 클래스를 불러옵니다.
from base_pokemon import Pokemon


# -------------------------------------------
# 🎮 BaseScene 클래스
# -------------------------------------------
# 모든 장면(Scene)의 공통 부모 클래스입니다.
# MapScene, BattleScene 등은 이 클래스를 상속받습니다.
class BaseScene(ABC):
    # 생성자: 모든 Scene은 game 객체(메인 루프)를 공유합니다.
    def __init__(self, game):
        self.game = game  # Game 인스턴스를 저장해, 장면 간 이동(change_scene)에 사용됩니다.

    # 하위 클래스에서 반드시 구현해야 할 이벤트 처리 메서드
    @abstractmethod
    def handle_events(self, events):
        pass

    # 하위 클래스에서 반드시 구현해야 할 업데이트 메서드
    @abstractmethod
    def update(self, dt):
        pass

    # 하위 클래스에서 반드시 구현해야 할 화면 그리기 메서드
    @abstractmethod
    def draw(self, screen):
        pass


# -------------------------------------------
# 🌳 MapScene 클래스
# -------------------------------------------
# 플레이어가 맵(필드)을 돌아다니며 전투로 진입할 수 있는 장면입니다.
class MapScene(BaseScene):
    # 생성자
    def __init__(self, game):
        # 부모 클래스(BaseScene)의 초기화 실행
        super().__init__(game)

        # Player 객체 생성 (시작 위치 x=100, y=100)
        self.player = Player(100, 100)

        # 스프라이트 그룹을 만들어, 화면에 그릴 객체를 묶습니다.
        self.all_sprites = pygame.sprite.Group(self.player)

    # 초록색 풀숲 영역을 사각형(Rect)으로 정의합니다.
        # (x=0, y=400, 너비=800, 높이=200)
        self.grass_rect = pygame.Rect(0, 400, 800, 200)

        # 플레이어가 보유한 첫 번째 포켓몬을 생성합니다.
        # (기본 스타터 포켓몬 — 필요 시 변경)
        self.player_pokemon = Pokemon("초염몽", level=5, max_hp=35, attack=12, defense=8, speed=10)

        # 배경 이미지 경로 설정(사용자가 이미지를 넣을 수 있도록 경로를 만들어 둡니다)
        # 기본적으로 프로젝트 루트의 `background.png`를 우선으로 사용하고,
        # 없다면 assets/backgrounds/background.png 를 시도합니다.
        candidate_root = os.path.join("background.png")
        candidate_assets = os.path.join("assets", "backgrounds", "background.png")
        if os.path.exists(candidate_root):
            self.background_image_path = candidate_root
        else:
            self.background_image_path = candidate_assets
        self.background_image = None
        try:
            if os.path.exists(self.background_image_path):
                # convert_alpha 허용은 PNG 투명도 지원을 돕습니다.
                self.background_image = pygame.image.load(self.background_image_path).convert_alpha()
        except Exception:
            # 로드 실패 시 무시하고 기본 컬러로 그립니다.
            self.background_image = None

        # 야생 포켓몬 후보 목록 (이름, 레벨, max_hp, attack, defense, speed)
        self.wild_candidates = [
            ("이상해풀", 3, 30, 10, 8, 7),
            ("꼬부기", 3, 28, 9, 9, 8),
            ("잉어킹", 4, 30, 14, 6, 8),
        ]

        # 체력 회복 아이템 관리: 각 아이템은 rect와 heal_amount를 가진 딕셔너리
        self.items = []
        self.item_surface = None
        # 기본 아이템 이미지 경로(사용자가 이미지를 넣을 수 있도록 경로를 준비)
        item_path = os.path.join("assets", "items", "heal.png")
        try:
            if os.path.exists(item_path):
                self.item_surface = pygame.image.load(item_path).convert_alpha()
                self.item_surface = pygame.transform.scale(self.item_surface, (24, 24))
        except Exception:
            self.item_surface = None

        if self.item_surface is None:
            # 대체: 초록색 원을 그린 Surface
            s = pygame.Surface((24, 24), pygame.SRCALPHA)
            # 변경: 아이템 색을 흰색으로 표시
            pygame.draw.circle(s, (255, 255, 255), (12, 12), 10)
            self.item_surface = s

        # 아이템 생성 타이머 (초)
        self.item_spawn_timer = 0.0
        self.item_spawn_interval = 8.0  # 초마다 하나씩 생성 시도
        # 전투 재발생 방지를 위한 쿨다운(초)
        self.battle_cooldown = 0.0
        # UI 폰트 (지도에서 보여줄 작은 HUD용)
        try:
            self.ui_font = pygame.font.SysFont("malgungothic", 18)
        except Exception:
            self.ui_font = pygame.font.SysFont(None, 18)

    # 이벤트 처리 (현재는 특별한 입력 처리 없음)
    def handle_events(self, events):
        pass  # 나중에 메뉴나 전투 시작 키 입력 등을 넣을 수 있음

    # 매 프레임마다 실행되는 업데이트 함수
    def update(self, dt):
        # 키보드 입력 상태를 가져옵니다.
        keys = pygame.key.get_pressed()

        # 쿨다운 감소
        if getattr(self, 'battle_cooldown', 0.0) > 0.0:
            self.battle_cooldown = max(0.0, self.battle_cooldown - dt)

        # Player 객체의 update() 메서드를 호출하여 이동을 적용합니다.
        self.player.update(dt, keys)

        # 만약 플레이어가 풀숲 영역(grass_rect)에 들어가면 전투 발생 확률 체크
        if self.player.rect.colliderect(self.grass_rect):
            # battle_cooldown이 0보다 클 때는 전투 발생을 막음
            if getattr(self, 'battle_cooldown', 0.0) <= 0.0:
                # 0~1 사이의 난수 중 0.05(5%) 확률로 전투 시작
                if random.random() < 0.05:
                    # 전투 씬을 불러오기 위해 이 시점에서 import (순환 참조 방지용)
                    from battle import BattleScene

                    # 야생 포켓몬을 후보군에서 무작위로 선택
                    name, lvl, hp, atk, df, sp = random.choice(self.wild_candidates)
                    wild = Pokemon(name, level=lvl, max_hp=hp, attack=atk, defense=df, speed=sp)

                    # 게임 장면을 전투 장면(BattleScene)으로 변경합니다.
                    # 인자: 현재 game 객체, 플레이어의 포켓몬, 야생 포켓몬
                    # origin_scene=self 를 넘겨 같은 MapScene 인스턴스로 돌아갈 수 있게 합니다.
                    self.game.change_scene(BattleScene(self.game, self.player_pokemon, wild, origin_scene=self))

        # 아이템 스폰 처리
        self.item_spawn_timer += dt
        if self.item_spawn_timer >= self.item_spawn_interval:
            self.item_spawn_timer = 0.0
            # 땅 영역(예: y=300~580) 안쪽에 랜덤하게 생성
            x = random.randint(0, max(0, 800 - 24))
            y = random.randint(300, max(300, 600 - 24))
            item_rect = pygame.Rect(x, y, 24, 24)
            self.items.append({"rect": item_rect, "heal": 15})

        # 플레이어와 아이템 충돌 체크
        for it in list(self.items):
            if self.player.rect.colliderect(it["rect"]):
                # 아이템 획득: 플레이어 포켓몬 체력 회복
                if hasattr(self, 'player_pokemon') and self.player_pokemon is not None:
                    heal = it.get("heal", 10)
                    prev = self.player_pokemon.current_hp
                    self.player_pokemon.current_hp = min(self.player_pokemon.max_hp, self.player_pokemon.current_hp + heal)
                    # 간단한 피드백
                    print(f"{self.player_pokemon.name} 의 체력이 {prev} -> {self.player_pokemon.current_hp} 으로 회복되었습니다.")
                try:
                    self.items.remove(it)
                except ValueError:
                    pass

    # 화면을 그리는 함수
    def draw(self, screen):
        # 배경 이미지가 있으면 스케일해서 먼저 그립니다. 없으면 기본 색상 사용
        if self.background_image is not None:
            try:
                bg = pygame.transform.scale(self.background_image, screen.get_size())
                screen.blit(bg, (0, 0))
            except Exception:
                screen.fill((150, 200, 255))
        else:
            # 하늘색 배경으로 화면 전체를 채웁니다.
            screen.fill((150, 200, 255))


        # 플레이어를 포함한 모든 스프라이트를 화면에 그립니다.
        self.all_sprites.draw(screen)

        # 아이템 그리기
        for it in self.items:
            screen.blit(self.item_surface, it["rect"].topleft)

        # ---------------------------
        # 우측 상단: 내 포켓몬 HP 표시
        # ---------------------------
        if getattr(self, 'player_pokemon', None) is not None:
            hud_w, hud_h = 180, 56
            sw = screen.get_width()
            x = sw - hud_w - 10
            y = 10
            # 배경 박스
            pygame.draw.rect(screen, (240, 240, 240), (x, y, hud_w, hud_h))
            pygame.draw.rect(screen, (160, 160, 160), (x, y, hud_w, hud_h), 2)

            # 이름과 레벨
            name_txt = f"{self.player_pokemon.name} Lv{self.player_pokemon.level}"
            name_surf = self.ui_font.render(name_txt, True, (10, 10, 10))
            screen.blit(name_surf, (x + 8, y + 6))

            # HP 바
            hp_x = x + 8
            hp_y = y + 28
            hp_w = hud_w - 16
            hp_h = 14
            pygame.draw.rect(screen, (100, 100, 100), (hp_x - 1, hp_y - 1, hp_w + 2, hp_h + 2))
            pygame.draw.rect(screen, (220, 220, 220), (hp_x, hp_y, hp_w, hp_h))
            cur = max(0, getattr(self.player_pokemon, 'current_hp', 0))
            m = max(1, getattr(self.player_pokemon, 'max_hp', 1))
            frac = min(1.0, cur / float(m))
            fill_w = int(hp_w * frac)
            if frac > 0.5:
                color = (88, 200, 115)
            elif frac > 0.2:
                color = (240, 200, 80)
            else:
                color = (220, 60, 60)
            if fill_w > 0:
                pygame.draw.rect(screen, color, (hp_x, hp_y, fill_w, hp_h))

            # HP 수치
            hp_text = self.ui_font.render(f"{int(cur)}/{int(m)}", True, (10, 10, 10))
            screen.blit(hp_text, (x + hud_w - 8 - hp_text.get_width(), y + 30))


class GameOverScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        # 폰트
        try:
            self.font = pygame.font.SysFont("malgungothic", 32)
        except Exception:
            self.font = pygame.font.SysFont(None, 32)
        # 버튼 영역
        self.button_rect = pygame.Rect(300, 360, 200, 60)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # 아무 키나 누르면 재시작
                self.game.restart()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.button_rect.collidepoint(event.pos):
                    self.game.restart()

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((40, 40, 40))
        title = self.font.render("Game Over", True, (240, 240, 240))
        screen.blit(title, (320, 200))
        reason = getattr(self.game, 'last_gameover_reason', '')
        reason_text = self.font.render(reason, True, (240, 240, 240))
        screen.blit(reason_text, (240, 230))
        total = getattr(self.game, 'total_exp', 0)
        info = self.font.render(f"획득한 총 EXP: {total}", True, (240, 240, 240))
        screen.blit(info, (260, 270))

        # 버튼
        pygame.draw.rect(screen, (200, 100, 100), self.button_rect)
        btn_text = self.font.render("다시 시작", True, (255, 255, 255))
        screen.blit(btn_text, (self.button_rect.x + 36, self.button_rect.y + 12))
