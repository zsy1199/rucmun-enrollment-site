#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态构建脚本：
- 读取根目录下的 Excel 报名表，统计各会场志愿与容量信息
- 读取各个会场的 txt 介绍文件
- 将结果输出为 static/data/stats.json 和 static/data/intros.json

用于在 Cloudflare Pages 等纯静态环境下部署本项目。
"""

import json
import os
from pathlib import Path

from data_processor import (
    COMMITTEES,
    COMMITTEE_CAPACITIES,
    COMMITTEE_DISPLAY_NAMES,
    process_data,
    get_capacity_ratio,
)


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATA_DIR = STATIC_DIR / "data"


def ensure_dirs() -> None:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def build_stats() -> None:
    """
    生成统计数据 JSON：static/data/stats.json
    结构：
    {
      "update_time": "...",
      "committees": {
        "<会场名>": {
          "first_choice": int,
          "second_choice": int,
          "third_choice": int,
          "capacity": int,
          "ratio": float
        },
        ...
      }
    }
    """
    print("==> 生成统计数据 stats.json ...")

    # 如果仓库中没有实际报名表（只有模板），且已经存在手工维护的 stats.json，
    # 则直接保留现有数据，不用空数据覆盖，方便在 Cloudflare 上展示静态配置的报名情况。
    stats_path = DATA_DIR / "stats.json"
    excel_files = [
        f
        for f in os.listdir(ROOT)
        if f.endswith((".xlsx", ".xls"))
        and not f.startswith("~")
        and f != "模板.xlsx"
    ]
    if not excel_files and stats_path.exists():
        print("  未检测到实际报名表，沿用现有的 static/data/stats.json")
        return

    stats, update_time = process_data(str(ROOT))

    output = {
        "update_time": update_time,
        "committees": {},
    }

    for committee in COMMITTEES:
        base = stats.get(committee, {"第一志愿": 0, "第二志愿": 0, "第三志愿": 0})
        ratio = get_capacity_ratio(stats, committee)
        # 静态页用显示名作为 key（UNSC/UNHSP -> 联合国安全理事会/联合国人类住区规划署）
        key = COMMITTEE_DISPLAY_NAMES.get(committee, committee)
        output["committees"][key] = {
            "first_choice": int(base.get("第一志愿", 0) or 0),
            "second_choice": int(base.get("第二志愿", 0) or 0),
            "third_choice": int(base.get("第三志愿", 0) or 0),
            "capacity": int(COMMITTEE_CAPACITIES.get(committee, 0)),
            "ratio": float(ratio),
        }

    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"已生成 {stats_path.relative_to(ROOT)}")


def build_intros() -> None:
    """
    生成会场介绍 JSON：static/data/intros.json
    结构：
    {
      "<会场名>": "<介绍全文（带换行与制表符）>",
      ...
    }
    """
    print("==> 生成会场介绍 intros.json ...")

    # 内部名 -> 文件名（与 app.py 一致）；写入 intros 时用显示名作为 key
    intro_files = {
        "联合国大会第四委员会": "联合国大会第四委员会.txt",
        "联合国系统联动体系": "联合国系统联动.txt",
        "第二十九届联合国气候变化大会及其临时工作委员会": "第二十九届联合国气候变化大会临时工作委员会.txt",
        "国际足联球员负荷专责工作组非正式会议": "国际足联球员负荷专责工作组非正式会议.txt",
        "历史谈判委员会": "历史谈判委员会.txt",
        "历史联动委员会": "历史联动委员会.txt",
        "UNSC": "UNSC.txt",
        "UNHSP": "UNHSP.txt",
        "主新闻中心": "主新闻中心.txt",
    }

    def normalize_indentation(text: str) -> str:
        # 与 app.py 中逻辑保持一致，但不依赖 Flask
        import re

        lines = text.replace("\r\n", "\n").split("\n")

        leader_markers = ("主席团负责人:", "Dais Head:")
        intro_markers = ("会场介绍:", "Introduction:")

        def starts_with_any(line: str, markers: tuple[str, ...]) -> bool:
            s = line.strip()
            return any(s.startswith(m) for m in markers)

        def is_new_header(line: str) -> bool:
            """
            判断是否是“字段:值”这种顶层header。
            关键点：避免把正文里的“问题: …”误判为header，所以要求冒号出现在较靠前位置。
            """
            s = line.strip()
            if not s:
                return False
            if line.startswith("\t") or line.startswith(" "):
                return False

            # 只接受前 15 个字符内出现的第一个冒号，作为“字段:”
            pos = s.find(":")
            pos_cn = s.find("：")
            if pos == -1 or (pos_cn != -1 and pos_cn < pos):
                pos = pos_cn
            if pos == -1 or pos > 15:
                return False

            key = s[:pos]
            # key 不应包含明显的正文标点
            if any(ch in key for ch in ("，", "。", "！", "？", ";", "；", "、", '"', "“", "”")):
                return False

            return True

        out: list[str] = []
        mode: str | None = None  # None | leaders | intro

        for line in lines:
            if starts_with_any(line, leader_markers):
                mode = "leaders"
                out.append(line.strip())  # 标准化marker行
                continue

            if starts_with_any(line, intro_markers):
                mode = "intro"
                out.append(line.strip())
                continue

            if mode in ("leaders", "intro"):
                # 遇到新的顶层header则结束当前段落
                if is_new_header(line):
                    mode = None
                    out.append(line)
                    continue

                if line.strip() and not line.startswith("\t"):
                    out.append("\t" + line)
                else:
                    out.append(line)
                continue

            out.append(line)

        return "\n".join(out)

    intros: dict[str, str] = {}

    for committee, filename in intro_files.items():
        path = ROOT / filename
        if not path.exists():
            print(f"  [WARN] 会场 {committee} 的介绍文件不存在：{filename}")
            continue
        with path.open("r", encoding="utf-8") as f:
            raw = f.read()
        key = COMMITTEE_DISPLAY_NAMES.get(committee, committee)
        intros[key] = normalize_indentation(raw)

    intros_path = DATA_DIR / "intros.json"
    with intros_path.open("w", encoding="utf-8") as f:
        json.dump(intros, f, ensure_ascii=False, indent=2)

    print(f"已生成 {intros_path.relative_to(ROOT)}")


def main() -> None:
    ensure_dirs()
    build_stats()
    build_intros()
    print("静态数据构建完成。")


if __name__ == "__main__":
    main()


