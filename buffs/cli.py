"""命令行入口：跑叠加与 DoT 快照样例。"""

import argparse
import sys

from .auras import Aura, AuraSet, dot_total


def build_parser():
    parser = argparse.ArgumentParser(prog="buff-stacking", description="叠加规则与 DoT 快照")
    parser.add_argument("--script", default="slow", help="slow / stacks / dot")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    auras = AuraSet()
    if args.script == "slow":
        auras.add(Aura("slow", 30, 5))
        auras.add(Aura("slow", 20, 5))
        print("slow_value=%d stacks=%d" % (auras.value("slow"), auras.stacks("slow")))
    elif args.script == "stacks":
        for _ in range(9):
            auras.add(Aura("bleed", 5, 10, stacks=1))
        print("bleed_stacks=%d" % auras.stacks("bleed"))
    elif args.script == "dot":
        print("dot_total=%d" % dot_total(100, 200, 3))
    else:
        print("错误：不认识的脚本", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
