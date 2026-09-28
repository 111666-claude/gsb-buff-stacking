"""Buff/Debuff 的叠加规则与 DoT 快照。

缺陷：slow 的叠加规则写成 refresh（口径是取最强）、层数不封顶、
DoT 每一跳都拿当前攻击力重算（口径要施法瞬间的快照）。
"""

MAX_STACKS = 5
RULES = {"slow": "refresh"}  # 缺陷：口径是 keep-strongest


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
        if aura.name not in self.auras:
            self.auras[aura.name] = aura
            return
        existing = self.auras[aura.name]
        rule = RULES.get(aura.name, "refresh")
        if rule == "refresh":
            existing.power = aura.power  # 缺陷：refresh 覆盖了更强的旧效果
        else:
            existing.power = max(existing.power, aura.power)
        existing.duration = max(existing.duration, aura.duration)
        existing.stacks = existing.stacks + aura.stacks  # 缺陷：没有按 MAX_STACKS 封顶

    def value(self, name):
        return self.auras[name].power if name in self.auras else 0

    def stacks(self, name):
        return self.auras[name].stacks if name in self.auras else 0

    def tick(self):
        for aura in list(self.auras.values()):
            aura.duration -= 1
            if aura.duration <= 0:
                del self.auras[aura.name]


def dot_total(snapshot_power, current_attack, ticks):
    """缺陷：口径要求用施法瞬间的属性快照，现在每跳都拿当前攻击力算。"""
    return current_attack * ticks
