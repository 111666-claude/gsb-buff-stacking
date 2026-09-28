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
