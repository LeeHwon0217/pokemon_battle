# 난수를 발생시켜서 공격 데미지를 약간씩 다르게 만들기 위해 random 모듈을 불러옵니다.
import random

# -----------------------------
# ⚔️ 기술(Skill) 클래스 정의
# -----------------------------
class Skill:
    # 기술의 이름(name), 위력(power), 사용 횟수(pp)을 초기화합니다.
    def __init__(self, name, power, pp):
        self.name = name            # 기술 이름 (예: '몸통박치기')
        self.power = power          # 기술의 공격력
        self.max_pp = pp            # 기술의 최대 사용 가능 횟수
        self.current_pp = pp        # 현재 남은 사용 횟수 (시작 시 최대치와 동일)

    # 기술을 사용할 때 호출됩니다.
    def use(self):
        # 남은 PP가 1 이상일 때만 기술 사용 가능
        if self.current_pp > 0:
            self.current_pp -= 1    # 기술을 한 번 사용하면 PP를 1 줄입니다.
            return True             # 사용 성공
        return False                # PP가 부족하면 사용 실패


# -----------------------------
# 🐉 포켓몬(Pokemon) 클래스 정의
# -----------------------------
class Pokemon:
    # 이름(name), 레벨(level), 체력(HP), 공격력/방어력/스피드, 그리고 기술 목록(skills)을 초기화합니다.
    def __init__(self, name, level, max_hp, attack, defense, speed, skills=None):
        self.name = name            # 포켓몬 이름
        self.level = level          # 레벨 (현재는 단순 표시용)
        self.max_hp = max_hp        # 최대 체력
        self.current_hp = max_hp    # 현재 체력 (처음엔 최대체력으로 시작)
        # 경험치(현재)와 다음 레벨까지 필요한 경험치 계산은 레벨^3 기반으로 간단히 설정
        self.exp = 0
        self.attack = attack        # 공격력
        self.defense = defense      # 방어력
        self.speed = speed          # 속도 (턴 순서 등에 사용 가능)
        # 기술 목록: 전달되지 않았다면 기본 기술을 자동으로 세팅합니다.
        self.skills = skills or self.default_skills()

    # 기본 기술을 지정하는 메서드 (기술이 따로 없을 때 자동으로 불림)
    def default_skills(self):
        # 예시로 'Tackle(몸통박치기)' 기술 하나를 등록합니다.
        return [Skill("Tackle", power=10, pp=35)]

    # 포켓몬이 기절(HP가 0 이하)했는지 확인합니다.
    def is_fainted(self):
        return self.current_hp <= 0

    # 데미지를 계산하는 메서드
    def calc_damage(self, skill, target):
        # 간단한 공식: 내 공격력 + 기술 위력 - 상대 방어력 + 랜덤 보정(-2~+2)
        base = skill.power + self.attack - target.defense
        # 최소 데미지를 1로 보장하고, 랜덤 요소를 더해 자연스럽게 만듭니다.
        damage = max(1, base + random.randint(-2, 2))
        return damage

    # target(상대 포켓몬)에게 공격을 수행하는 메서드
    def attack_target(self, skill_index, target):
        # 사용할 기술을 선택 (인덱스로 접근)
        skill = self.skills[skill_index]

        # 기술 사용 시도 — PP가 부족하면 False 반환
        if not skill.use():
            return 0, False  # 데미지 0, 사용 실패

        # 실제 데미지 계산
        damage = self.calc_damage(skill, target)

        # 상대 포켓몬의 체력에서 데미지만큼 차감
        target.current_hp = max(0, target.current_hp - damage)

        # (가한 데미지, 성공 여부) 반환
        return damage, True

    # -----------------------------
    # 경험치 및 레벨업 관련 메서드
    # -----------------------------
    def exp_to_next(self):
        # 간단한 공식: 필요 EXP = level^3
        return max(1, self.level ** 3)

    def gain_exp(self, amount):
        """지정한 amount만큼 EXP를 획득하고, 필요 시 레벨업을 수행한다.

        반환값: 메시지 리스트(예: ['Pikachu gained 20 EXP!', 'Pikachu grew to Lv5!'])
        """
        messages = []
        if amount <= 0:
            return messages

        self.exp += int(amount)
        messages.append(f"{self.name} 는(은) {int(amount)} EXP 를 얻었다!")

        # 레벨업 루프: 얻은 EXP로 여러 레벨을 한 번에 오를 수 있음
        while self.exp >= self.exp_to_next():
            self.exp -= self.exp_to_next()
            self.level_up()
            messages.append(f"{self.name} 은(는) Lv{self.level} 로 레벨업했다!")

        return messages

    def level_up(self):
        # 레벨을 1 올리고, 기본 스탯을 소폭 상승시킨다.
        self.level += 1
        # 예시 수치: max_hp +5, attack+2, defense+2, speed+1
        self.max_hp += 5
        self.attack += 2
        self.defense += 2
        self.speed += 1
        # 체력 증가분만큼 현재 체력도 회복시키기(플레이어가 더 유리하게 느껴짐)
        self.current_hp = min(self.max_hp, self.current_hp + 5)
