"""Buff/Debuff 的叠加规则与 DoT 快照。

规则表（README 口径）：

- keep-strongest：同名效果只保留最强的那一次；新效果不更强时整次丢弃，
  更强时整体替换（强度/层数/持续时间都取自新效果）。
- refresh（默认）：新效果覆盖强度与持续时间，层数累加。

层数统一封顶在 MAX_STACKS；DoT 在施法瞬间对属性快照，之后攻击力变化
不影响已挂上的持续伤害。
"""

MAX_STACKS = 5

RULES = {
    "slow": "keep-strongest",
}


class Aura:
    """一个光环或减益。"""

    __slots__ = ("name", "power", "duration", "stacks")

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
        stacks = max(0, min(MAX_STACKS, aura.stacks))
        if aura.name not in self.auras:
            self.auras[aura.name] = Aura(aura.name, aura.power, aura.duration, stacks)
            return
        existing = self.auras[aura.name]
        rule = RULES.get(aura.name, "refresh")
        if rule == "keep-strongest":
            if aura.power > existing.power:
                existing.power = aura.power
                existing.duration = aura.duration
                existing.stacks = stacks
            return
        existing.power = aura.power
        existing.duration = max(existing.duration, aura.duration)
        existing.stacks = max(0, min(MAX_STACKS, existing.stacks + stacks))

    def value(self, name):
        return self.auras[name].power if name in self.auras else 0

    def stacks(self, name):
        return self.auras[name].stacks if name in self.auras else 0

    def tick(self):
        expired = None
        for name, aura in self.auras.items():
            aura.duration -= 1
            if aura.duration <= 0:
                if expired is None:
                    expired = [name]
                else:
                    expired.append(name)
        if expired:
            for name in expired:
                del self.auras[name]


def dot_total(snapshot_power, current_attack, ticks):
    """用施法瞬间的属性快照计算持续伤害总伤。

    current_attack 仅保留在签名里以兼容调用方，实际不参与计算：伤害在
    施法时就已定下，之后攻击力变化不影响这一轮跳伤害。
    """
    return snapshot_power * ticks
