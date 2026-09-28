# buff-stacking

Buff/Debuff 的叠加规则与 DoT 快照，只用 Python 标准库。

```
python3 -m buffs.cli --script slow
python3 -m buffs.cli --script stacks
python3 -m buffs.cli --script dot
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **同名效果按规则表叠加**：`slow` 的规则是 keep-strongest（保留最强的那一次）。
  `--script slow`（先 30% 再 20%）按口径是 `slow_value=30`，现在 refresh 覆盖，给 `slow_value=20`。
- **层数封顶**：同名层数上限 `MAX_STACKS=5`。`--script stacks`（连挂 9 次）按口径是
  `bleed_stacks=5`，现在给 9。
- **DoT 用施法瞬间的快照**：伤害在施法时定下，之后攻击力变化不影响这一轮跳伤害。
  `--script dot`（施法时 100、之后 200、跳 3 次）按口径是 `dot_total=300`，现在每跳重算给 600。
- 不变量：叠加后强度单调不减（除规则明确 refresh）；层数 ∈ [0, MAX_STACKS]；
  同一批事件重复执行结果相同；到期光环必须从集合里删除。
- 规模：10 万目标 × 每人 10 个光环，单帧 tick 1 秒内完成，内存 O(光环数)。

## 现在的行为

- `RULES` 把 `slow` 标成 refresh：新的弱效果直接覆盖更强的旧效果。
- `existing.stacks + aura.stacks` 没有和 `MAX_STACKS` 取最小值。
- `dot_total` 忽略 `snapshot_power` 参数，用 `current_attack` 累加。

## 计划新增的能力

```
--script slow|stacks|dot
```

## 输出

```
slow_value=30 stacks=1
bleed_stacks=5
dot_total=300
```

## 目录

```
buffs/auras.py   叠加规则与 DoT
buffs/cli.py     命令行入口
tests/           unittest 用例
```
