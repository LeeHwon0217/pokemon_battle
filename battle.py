# battle.py
import pygame
import os
from scenes import BaseScene

FONT = None  # 전역 폰트 (초기화는 __init__에서)

class BattleScene(BaseScene):
    def __init__(self, game, player_pokemon, enemy_pokemon, origin_scene=None):
        super().__init__(game)
        global FONT
        if FONT is None:
            FONT = pygame.font.SysFont("malgungothic", 24)

        self.player_pokemon = player_pokemon
        self.enemy_pokemon = enemy_pokemon
        # 전투를 시작한 원래 씬을 보관(맵으로 되돌아갈 때 같은 인스턴스로 복귀하기 위해)
        self.origin_scene = origin_scene

        # 전투 화면에 표시할 포켓몬 이미지를 로드합니다. 파일 경로는
        # project_root/<name>.(png|jpg) 또는 assets/pokemon/<name>.(png|jpg)
        def find_image(name):
            exts = ("png", "jpg", "jpeg")
            candidates = []
            # 우선 루트 폴더
            for e in exts:
                candidates.append(os.path.join(f"{name}.{e}"))
            # assets/pokemon 폴더
            for e in exts:
                candidates.append(os.path.join("assets", "pokemon", f"{name}.{e}"))
            for p in candidates:
                if os.path.exists(p):
                    return p
            return None

        # 로드 시도
        try:
            ppath = find_image(self.player_pokemon.name)
            if ppath:
                self.player_image = pygame.image.load(ppath).convert_alpha()
                self.player_image = pygame.transform.smoothscale(self.player_image, (120, 120))
            else:
                self.player_image = None
        except Exception:
            self.player_image = None

        try:
            epath = find_image(self.enemy_pokemon.name)
            if epath:
                self.enemy_image = pygame.image.load(epath).convert_alpha()
                self.enemy_image = pygame.transform.smoothscale(self.enemy_image, (120, 120))
            else:
                self.enemy_image = None
        except Exception:
            self.enemy_image = None

        self.state = "MENU"  # MENU -> SKILL_SELECT -> ANIMATION/LOG 등
        self.log = "야생 {} 이(가) 나타났다!".format(enemy_pokemon.name)
        self.selected_skill = 0

        self.turn = "PLAYER"  # PLAYER / ENEMY
        # 화면에 표시할 HP는 실제 HP와 분리하여 애니메이션(감소)을 표현합니다.
        # float로 보간해서 매 프레임 부드럽게 변경됩니다.
        self.player_display_hp = float(self.player_pokemon.current_hp)
        self.enemy_display_hp = float(self.enemy_pokemon.current_hp)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # 전투가 끝나면 아무 키나 누르면 필드로 돌아가거나 게임오버로 이동
                if self.state == "FINISHED":
                    # 플레이어가 기절 상태라면 게임오버 씬으로
                    if self.player_pokemon.is_fainted():
                        from scenes import GameOverScene
                        self.game.change_scene(GameOverScene(self.game))
                    else:
                        # origin_scene 이 있으면 같은 인스턴스로 복귀
                        if getattr(self, 'origin_scene', None) is not None:
                            self.game.change_scene(self.origin_scene)
                        else:
                            from scenes import MapScene
                            self.game.change_scene(MapScene(self.game))
                    return

                if self.state == "MENU":
                    if event.key == pygame.K_1:
                        self.state = "SKILL_SELECT"
                    elif event.key == pygame.K_2:
                        # 도망
                        self.log = "성공적으로 도망쳤다!"
                        # 필드로 돌아가기: origin_scene이 있으면 같은 인스턴스로 복귀 (HP 리셋 방지)
                        # 도망 횟수 누적 및 연속 도망 체크
                        try:
                            self.game.flee_count = getattr(self.game, 'flee_count', 0) + 1
                        except Exception:
                            pass

                        # 두 번 연속 도망이면 게임 오버 처리
                        if getattr(self.game, 'flee_count', 0) >= 2:
                            try:
                                self.game.last_gameover_reason = "포켓몬이 실망했다..."
                            except Exception:
                                pass
                            from scenes import GameOverScene
                            self.game.change_scene(GameOverScene(self.game))
                            return

                        if getattr(self, 'origin_scene', None) is not None:
                            try:
                                # 짧은 쿨다운을 걸어 즉시 재전투 발생을 방지
                                self.origin_scene.battle_cooldown = 1.0
                            except Exception:
                                pass
                            self.game.change_scene(self.origin_scene)
                        else:
                            from scenes import MapScene
                            self.game.change_scene(MapScene(self.game))
                elif self.state == "SKILL_SELECT":
                    # 예: 1번 스킬만 있다고 가정
                    if event.key == pygame.K_1:
                        self.player_attack()

    def player_attack(self):
        damage, ok = self.player_pokemon.attack_target(0, self.enemy_pokemon)
        if not ok:
            self.log = "PP가 부족하다!"
            return

        self.log = f"{self.player_pokemon.name} 의 {self.player_pokemon.skills[0].name}! {damage} 데미지!"
        if self.enemy_pokemon.is_fainted():
            self.log += f"\n야생 {self.enemy_pokemon.name} 은(는) 쓰러졌다!"
            # EXP 지급: 간단한 공식으로 경험치 지급 (예: 상대 레벨 * 10)
            exp_gain = max(1, int(self.enemy_pokemon.level * 10))
            # 게임 전체 누적 EXP에 추가
            try:
                self.game.total_exp = getattr(self.game, 'total_exp', 0) + exp_gain
            except Exception:
                pass
            try:
                msgs = self.player_pokemon.gain_exp(exp_gain)
                for m in msgs:
                    self.log += "\n" + m
            except Exception:
                # 안전하게 무시 (포켓몬 객체에 exp 메서드가 없을 수 있음)
                pass
            # 연속 도망 카운트 초기화 (승리하면 '연속'이 깨집니다)
            try:
                self.game.flee_count = 0
            except Exception:
                pass
            # 전투 종료 상태로 전환 (아무 키나 누르면 필드로 복귀)
            self.state = "FINISHED"
            # 전투가 끝난 시 origin_scene이 있으면 그 맵에 쿨다운을 설정하여
            # 즉시 재전투가 발생하지 않도록 보호합니다.
            if getattr(self, 'origin_scene', None) is not None:
                try:
                    self.origin_scene.battle_cooldown = 1.0
                except Exception:
                    pass
            self.log += "\n아무 키나 눌러 필드로 돌아갑니다."
        else:
            self.turn = "ENEMY"
            self.enemy_attack()

    def enemy_attack(self):
        damage, ok = self.enemy_pokemon.attack_target(0, self.player_pokemon)
        if not ok:
            self.log = f"야생 {self.enemy_pokemon.name} 은(는) 아무 일도 일어나지 않았다."
        else:
            self.log += f"\n야생 {self.enemy_pokemon.name} 의 공격! {damage} 데미지!"
        # 플레이어 기절 체크
        if self.player_pokemon.is_fainted():
            self.log += f"\n{self.player_pokemon.name} 은(는) 기절했다..."
            self.state = "FINISHED"
            self.log += "\n아무 키나 눌러 필드로 돌아갑니다."
        self.turn = "PLAYER"

    def update(self, dt):
        # 둘 중 하나라도 쓰러지면 아무 키나 누르면 필드로 복귀하도록 바꿀 수도 있습니다.
        if self.player_pokemon.is_fainted() or self.enemy_pokemon.is_fainted():
            # 간단하게 엔터 누르면 돌아간다든지, 추가 로직 가능
            pass
        # HP 애니메이션: 실제 HP 쪽으로 부드럽게 접근
        lerp_speed = 6.0  # 클수록 더 빨리 줄어듬 (단위: 1/초에 가까워지는 비율)
        # 플레이어
        target_p = float(self.player_pokemon.current_hp)
        if abs(self.player_display_hp - target_p) > 0.01:
            self.player_display_hp += (target_p - self.player_display_hp) * min(1.0, lerp_speed * dt)
        else:
            self.player_display_hp = target_p
        # 상대
        target_e = float(self.enemy_pokemon.current_hp)
        if abs(self.enemy_display_hp - target_e) > 0.01:
            self.enemy_display_hp += (target_e - self.enemy_display_hp) * min(1.0, lerp_speed * dt)
        else:
            self.enemy_display_hp = target_e

    def draw(self, screen):
        screen.fill((255, 255, 255))

        # 간단한 박스 UI
        pygame.draw.rect(screen, (200, 200, 200), (50, 50, 300, 100))   # 내 포켓몬
        pygame.draw.rect(screen, (200, 200, 200), (450, 50, 300, 100))  # 야생 포켓몬
        pygame.draw.rect(screen, (230, 230, 230), (50, 400, 700, 150))  # 메뉴/메시지

        # 이름 + 레벨 텍스트
        p_name = f"{self.player_pokemon.name} Lv{self.player_pokemon.level}"
        e_name = f"{self.enemy_pokemon.name} Lv{self.enemy_pokemon.level}"
        p_text = FONT.render(p_name, True, (0, 0, 0))
        e_text = FONT.render(e_name, True, (0, 0, 0))
        screen.blit(p_text, (60, 60))
        screen.blit(e_text, (460, 60))

        # 포켓몬 이미지 표시 (적은 상단 우측, 아군은 하단 좌측 느낌)
        # enemy: 오른쪽 박스 위쪽 쪽에 배치
        if getattr(self, 'enemy_image', None) is not None:
            try:
                screen.blit(self.enemy_image, (460 + 80, 60))
            except Exception:
                pass
        # player: 왼쪽 박스 아래쪽 쪽에 배치
        if getattr(self, 'player_image', None) is not None:
            try:
                screen.blit(self.player_image, (60 + 20, 90))
            except Exception:
                pass

        # HP 바 그리기 함수(내부)
        def draw_hp_bar(screen, x, y, w, h, display_hp, max_hp):
            # 백그라운드
            pygame.draw.rect(screen, (100, 100, 100), (x - 1, y - 1, w + 2, h + 2))
            pygame.draw.rect(screen, (210, 210, 210), (x, y, w, h))
            # 비율 계산
            fraction = 0.0 if max_hp <= 0 else max(0.0, min(1.0, display_hp / float(max_hp)))
            fill_w = int(w * fraction)
            # 색상: 초록 -> 노랑 -> 빨강
            if fraction > 0.5:
                color = (88, 200, 115)  # 녹색
            elif fraction > 0.2:
                color = (240, 200, 80)  # 노랑
            else:
                color = (220, 60, 60)   # 빨강
            if fill_w > 0:
                pygame.draw.rect(screen, color, (x, y, fill_w, h))

        # 내 포켓몬 HP 바
        draw_hp_bar(screen, 60, 90, 220, 18, self.player_display_hp, self.player_pokemon.max_hp)
        # 상대 포켓몬 HP 바
        draw_hp_bar(screen, 460, 90, 220, 18, self.enemy_display_hp, self.enemy_pokemon.max_hp)

        # HP 수치 텍스트 (우측에 표시)
        p_hp_text = FONT.render(f"{int(self.player_display_hp)}/{self.player_pokemon.max_hp}", True, (0, 0, 0))
        e_hp_text = FONT.render(f"{int(self.enemy_display_hp)}/{self.enemy_pokemon.max_hp}", True, (0, 0, 0))
        screen.blit(p_hp_text, (60, 115))
        screen.blit(e_hp_text, (460, 115))

        # 메뉴/로그
        y = 410
        for i, line in enumerate(self.log.split("\n")):
            log_text = FONT.render(line, True, (0, 0, 0))
            screen.blit(log_text, (60, y + i * 30))

        if not (self.player_pokemon.is_fainted() or self.enemy_pokemon.is_fainted()):
            menu_text1 = FONT.render("1) 공격", True, (0, 0, 0))
            menu_text2 = FONT.render("2) 도망", True, (0, 0, 0))
            screen.blit(menu_text1, (60, 470))
            screen.blit(menu_text2, (200, 470))
