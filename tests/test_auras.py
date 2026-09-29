import unittest

from buffs.auras import MAX_STACKS, Aura, AuraSet, dot_total


class AddTest(unittest.TestCase):
    def test_first_add(self):
        auras = AuraSet()
        auras.add(Aura("haste", 10, 5))
        self.assertEqual(auras.value("haste"), 10)

    def test_duration_refresh(self):
        auras = AuraSet()
        auras.add(Aura("haste", 10, 5))
        auras.add(Aura("haste", 10, 9))
        self.assertEqual(auras.auras["haste"].duration, 9)

    def test_tick_expires(self):
        auras = AuraSet()
        auras.add(Aura("haste", 10, 1))
        auras.tick()
        self.assertEqual(auras.value("haste"), 0)

    def test_second_add_overwrites_power(self):
        auras = AuraSet()
        auras.add(Aura("shield", 10, 5))
        auras.add(Aura("shield", 20, 5))
        self.assertEqual(auras.value("shield"), 20)


class DoTTest(unittest.TestCase):
    def test_zero_ticks(self):
        self.assertEqual(dot_total(100, 200, 0), 0)

    def test_ticks_count(self):
        self.assertEqual(dot_total(10, 10, 4), 40)

    def test_max_stacks_defined(self):
        self.assertEqual(MAX_STACKS, 5)


class KeepStrongestTest(unittest.TestCase):
    def test_weaker_does_not_replace(self):
        auras = AuraSet()
        auras.add(Aura("slow", 30, 5))
        auras.add(Aura("slow", 20, 5))
        self.assertEqual(auras.value("slow"), 30)
        self.assertEqual(auras.stacks("slow"), 1)

    def test_stronger_replaces(self):
        auras = AuraSet()
        auras.add(Aura("slow", 20, 5))
        auras.add(Aura("slow", 30, 5))
        self.assertEqual(auras.value("slow"), 30)

    def test_equal_does_not_replace(self):
        auras = AuraSet()
        auras.add(Aura("slow", 30, 5))
        auras.add(Aura("slow", 30, 2))
        self.assertEqual(auras.value("slow"), 30)
        self.assertEqual(auras.auras["slow"].duration, 5)

    def test_default_rule_still_refreshes(self):
        auras = AuraSet()
        auras.add(Aura("shield", 10, 5))
        auras.add(Aura("shield", 20, 5))
        self.assertEqual(auras.value("shield"), 20)

    def test_keep_strongest_power_monotone(self):
        auras = AuraSet()
        auras.add(Aura("slow", 30, 5))
        previous = auras.value("slow")
        for power in (40, 25, 50, 10):
            auras.add(Aura("slow", power, 5))
            self.assertGreaterEqual(auras.value("slow"), previous)
            previous = auras.value("slow")


class StackCapTest(unittest.TestCase):
    def test_nine_applications_cap_at_five(self):
        auras = AuraSet()
        for _ in range(9):
            auras.add(Aura("bleed", 5, 10, stacks=1))
        self.assertEqual(auras.stacks("bleed"), MAX_STACKS)

    def test_big_single_application_capped(self):
        auras = AuraSet()
        auras.add(Aura("bleed", 5, 10, stacks=9))
        self.assertEqual(auras.stacks("bleed"), MAX_STACKS)

    def test_overcapped_partial_application(self):
        auras = AuraSet()
        auras.add(Aura("bleed", 5, 10, stacks=4))
        auras.add(Aura("bleed", 5, 10, stacks=4))
        self.assertEqual(auras.stacks("bleed"), MAX_STACKS)

    def test_keep_strongest_never_stacks(self):
        auras = AuraSet()
        auras.add(Aura("slow", 30, 5, stacks=2))
        auras.add(Aura("slow", 25, 5, stacks=5))
        self.assertEqual(auras.stacks("slow"), 2)
        auras.add(Aura("slow", 40, 5, stacks=4))
        self.assertEqual(auras.stacks("slow"), 4)
        self.assertLessEqual(auras.stacks("slow"), MAX_STACKS)

    def test_stacks_cleared_after_expiry(self):
        auras = AuraSet()
        auras.add(Aura("bleed", 5, 1, stacks=5))
        auras.tick()
        self.assertEqual(auras.stacks("bleed"), 0)
        self.assertNotIn("bleed", auras.auras)
        auras.add(Aura("bleed", 5, 2, stacks=2))
        self.assertEqual(auras.stacks("bleed"), 2)


class DoTSnapshotTest(unittest.TestCase):
    def test_ignores_current_attack(self):
        self.assertEqual(dot_total(100, 200, 3), 300)

    def test_snapshot_drives_total(self):
        self.assertEqual(dot_total(100, 999, 4), 400)
        self.assertEqual(dot_total(0, 200, 3), 0)


class ReferenceAura:
    """独立参考实现：严格按规则表 + 封顶 + 快照推演。"""

    RULES = {"slow": "keep-strongest"}

    def __init__(self):
        self.state = {}

    def apply(self, name, power, duration, stacks):
        stacks = max(0, min(MAX_STACKS, stacks))
        if name not in self.state:
            self.state[name] = [power, duration, stacks]
            return
        current_power, current_duration, current_stacks = self.state[name]
        if self.RULES.get(name, "refresh") == "keep-strongest":
            if power > current_power:
                self.state[name] = [power, duration, stacks]
            return
        self.state[name] = [
            power,
            max(current_duration, duration),
            max(0, min(MAX_STACKS, current_stacks + stacks)),
        ]

    def tick(self):
        expired = [name for name, aura in self.state.items() if aura[1] - 1 <= 0]
        for name in expired:
            del self.state[name]
        for aura in self.state.values():
            aura[1] -= 1

    def power_of(self, name):
        return self.state[name][0] if name in self.state else 0

    def stacks_of(self, name):
        return self.state[name][2] if name in self.state else 0


class DifferentialTest(unittest.TestCase):
    NAMES = ("slow", "bleed", "haste", "shield", "poison")

    def _stream(self, rng):
        events = []
        for _ in range(rng.randrange(20, 60)):
            if events and rng.random() < 0.3:
                events.append(("tick", None))
            else:
                events.append((
                    "cast",
                    (
                        rng.choice(self.NAMES),
                        rng.randrange(0, 40),
                        rng.randrange(1, 6),
                        rng.randrange(1, 8),
                    ),
                ))
        return events

    def _run_reference(self, events):
        ref = ReferenceAura()
        observed = []
        for kind, payload in events:
            if kind == "cast":
                ref.apply(*payload)
            else:
                ref.tick()
            snapshot = {
                name: (ref.power_of(name), ref.stacks_of(name))
                for name in self.NAMES
            }
            observed.append(snapshot)
        return observed

    def _run_actual(self, events):
        auras = AuraSet()
        observed = []
        for kind, payload in events:
            if kind == "cast":
                name, power, duration, stacks = payload
                auras.add(Aura(name, power, duration, stacks))
            else:
                auras.tick()
            snapshot = {
                name: (auras.value(name), auras.stacks(name))
                for name in self.NAMES
            }
            for _, stack_count in snapshot.values():
                self.assertGreaterEqual(stack_count, 0)
                self.assertLessEqual(stack_count, MAX_STACKS)
            observed.append(snapshot)
        return observed

    def test_random_streams_match_reference(self):
        import random

        rng = random.Random(20260930)
        for _ in range(200):
            events = self._stream(rng)
            expected = self._run_reference(events)
            self.assertEqual(self._run_actual(events), expected)

    def test_replaying_same_events_is_deterministic(self):
        import random

        rng = random.Random(42)
        for _ in range(10):
            events = self._stream(rng)
            first = self._run_actual(events)
            second = self._run_actual(events)
            self.assertEqual(first, second)

    def test_dot_snapshot_matches_reference(self):
        import random

        rng = random.Random(7)
        for _ in range(200):
            snapshot_power = rng.randrange(0, 100)
            current_attack = rng.randrange(0, 100)
            ticks = rng.randrange(0, 10)
            self.assertEqual(
                dot_total(snapshot_power, current_attack, ticks),
                snapshot_power * ticks,
            )
