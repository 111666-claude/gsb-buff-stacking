"""Buff/Debuff 的叠加规则与 DoT 快照。

口径（以 README 为准）：

- ``slow`` 按 keep-strongest 叠加：只保留最强的一次施放，较弱的施放整体
  丢弃（不覆盖强度、不延长持续时间、不累加层数）；更强的一次整体替换。
- 其它效果默认 refresh：以新施放的强度为准，持续时间取较长者，层数累加。
- 层数统一封顶在 ``MAX_STACKS``，超出部分丢弃。
- DoT 伤害在施法瞬间快照，之后攻击力变化不影响这一轮跳伤害。
"""

MAX_STACKS = 5

REFRESH = "refresh"
KEEP_STRONGEST = "keep-strongest"

RULES = {"slow": KEEP_STRONGEST}


class Aura:
    """一个光环或减益。"""

    def __init__(self, name, power, duration, stacks=1):
        self.name = name
        self.power = power
        self.duration = duration
        self.stacks = stacks


class AuraSet:
    """目标身上的光环集合。"""

    def __init__(self):
        self.auras = {}

    def add(self, aura):
        existing = self.auras.get(aura.name)
        if existing is None:
            aura.stacks = min(MAX_STACKS, aura.stacks)
            self.auras[aura.name] = aura
            return
        rule = RULES.get(aura.name, REFRESH)
        if rule == KEEP_STRONGEST:
            if aura.power <= existing.power:
                return
            existing.power = aura.power
            existing.duration = aura.duration
            existing.stacks = min(MAX_STACKS, aura.stacks)
            return
        existing.power = aura.power
        existing.duration = max(existing.duration, aura.duration)
        existing.stacks = min(MAX_STACKS, existing.stacks + aura.stacks)

    def value(self, name):
        aura = self.auras.get(name)
        return aura.power if aura is not None else 0

    def stacks(self, name):
        aura = self.auras.get(name)
        return aura.stacks if aura is not None else 0

    def tick(self):
        for aura in list(self.auras.values()):
            aura.duration -= 1
            if aura.duration <= 0:
                del self.auras[aura.name]


def dot_total(snapshot_power, current_attack, ticks):
    """DoT 总伤害，按施法瞬间快照的攻击力结算。"""
    return snapshot_power * ticks
