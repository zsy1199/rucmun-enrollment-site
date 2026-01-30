#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web应用：提供数据统计网页
"""
from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS
from data_processor import process_data, COMMITTEES, get_total_count, COMMITTEE_CAPACITIES, get_capacity_ratio, COMMITTEE_DISPLAY_NAMES
import os

app = Flask(__name__)
CORS(app)

# 设置模板和静态文件目录
app.template_folder = 'templates'
app.static_folder = 'static'

@app.route('/')
def index():
    """主页面：显示所有会场的概览"""
    return render_template('index.html', committees=COMMITTEES, display_names=COMMITTEE_DISPLAY_NAMES)

def _resolve_committee_name(name):
    """URL/显示名为「联合国安全理事会」等时，解析为内部名 UNSC，便于查 Excel 与 intro 文件。"""
    from urllib.parse import unquote
    name = unquote(name)
    reverse = {v: k for k, v in COMMITTEE_DISPLAY_NAMES.items()}
    return reverse.get(name, name)


@app.route('/committee/<committee_name>')
def committee_page(committee_name):
    """各个会场的详细页面"""
    from urllib.parse import unquote
    committee_name = unquote(committee_name)
    return render_template('committee.html', committee_name=committee_name, committees=COMMITTEES, display_names=COMMITTEE_DISPLAY_NAMES)

@app.route('/api/stats')
def get_stats():
    """API：获取所有会场的统计数据（key 使用显示名，与静态页一致）"""
    try:
        stats, update_time = process_data()
        enhanced_data = {}
        for committee in COMMITTEES:
            key = COMMITTEE_DISPLAY_NAMES.get(committee, committee)
            enhanced_data[key] = {
                **stats[committee],
                'capacity': COMMITTEE_CAPACITIES[committee],
                'ratio': get_capacity_ratio(stats, committee)
            }
        return jsonify({
            'success': True,
            'data': enhanced_data,
            'update_time': update_time
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/committee/<committee_name>')
def get_committee_stats(committee_name):
    """API：获取特定会场的统计数据"""
    try:
        internal_name = _resolve_committee_name(committee_name)
        stats, update_time = process_data()
        
        if internal_name not in stats:
            return jsonify({
                'success': False,
                'error': '会场不存在'
            }), 404
        
        committee_data = stats[internal_name]
        total = get_total_count(stats, internal_name)
        capacity = COMMITTEE_CAPACITIES.get(internal_name, 0)
        ratio = get_capacity_ratio(stats, internal_name)
        
        display_name = COMMITTEE_DISPLAY_NAMES.get(internal_name, committee_name)
        return jsonify({
            'success': True,
            'data': {
                'committee': display_name,
                'first_choice': committee_data['第一志愿'],
                'second_choice': committee_data['第二志愿'],
                'third_choice': committee_data['第三志愿'],
                'total': total,
                'capacity': capacity,
                'ratio': ratio
            },
            'update_time': update_time
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/intro/<committee_name>')
def get_committee_intro(committee_name):
    """API：获取特定会场的介绍文本（从项目根目录的txt读取）"""
    try:
        internal_name = _resolve_committee_name(committee_name)

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

        filename = intro_files.get(internal_name)
        if not filename:
            return jsonify({"success": False, "error": "会场不存在"}), 404

        file_path = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "未找到会场介绍文件"}), 404

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 统一缩进规则：
        # - 主席团负责人 / Dais Head 段落：后续每行前补齐一个Tab
        # - 会场介绍 / Introduction 段落：后续每行前补齐一个Tab（更符合网页展示）
        def normalize_indentation(text: str) -> str:
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
                if any(ch in key for ch in ("，", "。", "！", "？", ";", "；", "、", "\"", "“", "”")):
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

        import re
        content = normalize_indentation(content)

        if not content or not content.strip():
            return jsonify({"success": False, "error": "会场介绍文件为空"}), 404

        display_name = COMMITTEE_DISPLAY_NAMES.get(internal_name, committee_name)
        return jsonify({"success": True, "committee": display_name, "content": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

