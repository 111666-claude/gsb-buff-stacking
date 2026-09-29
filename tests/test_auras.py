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
import random


class KeepStrongestTest(unittest.TestCase):
    def test_weaker_cast_is_discarded(self):
        auras = AuraSet()
        auras.add(Aura("slow", 30, 5))
        auras.add(Aura("slow", 20, 5))
        self.assertEqual(auras.value("slow"), 30)
        self.assertEqual(auras.stacks("slow"), 1)

    def test_weaker_cast_does_not_extend_duration(self):
        auras = AuraSet()
        auras.add(Aura("slow", 30, 2))
        auras.add(Aura("slow", 20, 9))
        self.assertEqual(auras.auras["slow"].duration, 2)

    def test_stronger_cast_replaces(self):
        auras = AuraSet()
        auras.add(Aura("slow", 20, 5))
        auras.add(Aura("slow", 30, 5))
        self.assertEqual(auras.value("slow"), 30)

    def test_equal_power_is_not_stronger(self):
        auras = AuraSet()
        auras.add(Aura("slow", 30, 2))
        auras.add(Aura("slow", 30, 9))
        self.assertEqual(auras.auras["slow"].duration, 2)

    def test_strength_never_decreases(self):
        auras = AuraSet()
        auras.add(Aura("slow", 40, 8))
        for power in (35, 10, 40, 39, 25):
            auras.add(Aura("slow", power, 8))
            self.assertEqual(auras.value("slow"), 40)


class StackCapTest(unittest.TestCase):
    def test_caps_at_max_stacks(self):
        auras = AuraSet()
        for _ in range(9):
            auras.add(Aura("bleed", 5, 10, stacks=1))
        self.assertEqual(auras.stacks("bleed"), MAX_STACKS)

    def test_single_overstacked_application_is_capped(self):
        auras = AuraSet()
        auras.add(Aura("bleed", 5, 10, stacks=9))
        self.assertEqual(auras.stacks("bleed"), MAX_STACKS)

    def test_extra_stacks_are_dropped(self):
        auras = AuraSet()
        auras.add(Aura("bleed", 5, 10, stacks=4))
        auras.add(Aura("bleed", 5, 10, stacks=4))
        self.assertEqual(auras.stacks("bleed"), MAX_STACKS)
        auras.add(Aura("bleed", 5, 10, stacks=2))
        self.assertEqual(auras.stacks("bleed"), MAX_STACKS)

    def test_keep_strongest_does_not_accumulate_stacks(self):
        auras = AuraSet()
        auras.add(Aura("slow", 30, 8, stacks=2))
        auras.add(Aura("slow", 20, 8, stacks=2))
        self.assertEqual(auras.stacks("slow"), 2)


class DoTSnapshotTest(unittest.TestCase):
    def test_uses_snapshot_power(self):
        self.assertEqual(dot_total(100, 200, 3), 300)

    def test_attack_change_after_cast_ignored(self):
        self.assertEqual(dot_total(50, 999, 4), 200)

    def test_snapshot_zero_power(self):
        self.assertEqual(dot_total(0, 200, 5), 0)


class ReferenceModel:
    """按 README 口径写的独立参考实现。"""

    def __init__(self):
        self.state = {}

    def add(self, name, power, duration, stacks):
        capped = min(MAX_STACKS, stacks)
        if name not in self.state:
            self.state[name] = [power, duration, capped]
            return
        current = self.state[name]
        if name == "slow":
            if power > current[0]:
                current[0] = power
                current[1] = duration
                current[2] = capped
        else:
            current[0] = power
            current[1] = max(current[1], duration)
            current[2] = min(MAX_STACKS, current[2] + capped)

    def tick(self):
        expired = []
        for name, current in self.state.items():
            current[1] -= 1
            if current[1] <= 0:
                expired.append(name)
        for name in expired:
            del self.state[name]

    def value(self, name):
        return self.state[name][0] if name in self.state else 0

    def stacks(self, name):
        return self.state[name][2] if name in self.state else 0


class CrossValidationTest(unittest.TestCase):
    def test_random_event_streams_match_reference(self):
        rng = random.Random(20260930)
        names = ["slow", "bleed", "haste", "shield"]
        for _ in range(200):
            actual = AuraSet()
            reference = ReferenceModel()

            def assert_matches():
                for name in names:
                    self.assertEqual(actual.value(name), reference.value(name), name)
                    self.assertEqual(actual.stacks(name), reference.stacks(name), name)
                    self.assertGreaterEqual(actual.stacks(name), 0)
                    self.assertLessEqual(actual.stacks(name), MAX_STACKS)
                self.assertEqual(set(actual.auras), set(reference.state))

            for _ in range(rng.randint(1, 30)):
                if rng.random() < 0.7:
                    name = rng.choice(names)
                    power = rng.randint(1, 50)
                    duration = rng.randint(1, 6)
                    stacks = rng.randint(1, 4)
                    actual.add(Aura(name, power, duration, stacks=stacks))
                    reference.add(name, power, duration, stacks)
                else:
                    actual.tick()
                    reference.tick()
                assert_matches()

    def test_repeated_events_are_deterministic(self):
        def run():
            auras = AuraSet()
            auras.add(Aura("slow", 30, 3))
            auras.add(Aura("slow", 20, 3))
            for _ in range(9):
                auras.add(Aura("bleed", 5, 4, stacks=1))
            auras.tick()
            return auras.value("slow"), auras.stacks("slow"), auras.stacks("bleed")

        self.assertEqual(run(), run())
