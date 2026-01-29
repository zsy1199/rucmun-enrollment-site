#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理模块：从Excel文件中提取并统计志愿报名数据
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Tuple

# 会场列表
COMMITTEES = [
    "联合国大会第四委员会",
    "联合国系统联动体系",
    "第二十九届联合国气候变化大会及其临时工作委员会",
    "国际足联球员负荷专责工作组非正式会议",
    "历史谈判委员会",
    "历史联动委员会",
    "UNSC",
    "UNHSP",
    "主新闻中心"
]

# 会场容量（按顺序对应）
COMMITTEE_CAPACITIES = {
    "联合国大会第四委员会": 45,
    "联合国系统联动体系": 80,
    "第二十九届联合国气候变化大会及其临时工作委员会": 27,
    "国际足联球员负荷专责工作组非正式会议": 35,
    "历史谈判委员会": 28,
    "历史联动委员会": 80,
    "UNSC": 25,
    "UNHSP": 40,
    "主新闻中心": 30
}

def read_excel_files(excel_dir: str = ".") -> pd.DataFrame:
    """
    读取指定目录下所有Excel文件并合并数据
    
    Args:
        excel_dir: Excel文件所在目录
        
    Returns:
        合并后的DataFrame
    """
    all_data = []
    excel_files = [f for f in os.listdir(excel_dir) if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]
    
    for excel_file in excel_files:
        try:
            # 跳过模板文件
            if excel_file == '模板.xlsx':
                continue
                
            file_path = os.path.join(excel_dir, excel_file)
            # 读取Excel，第一行是标题，第二行是列名
            df = pd.read_excel(file_path, header=1)
            
            # 确保必要的列存在
            required_columns = ['第一志愿委员会', '第二志愿委员会', '第三志愿委员会']
            if all(col in df.columns for col in required_columns):
                all_data.append(df)
        except Exception as e:
            print(f"读取文件 {excel_file} 时出错: {e}")
            continue
    
    if not all_data:
        return pd.DataFrame()
    
    # 合并所有数据
    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df

def count_volunteers(df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    """
    统计每个会场的第一、第二、第三志愿报名人数
    
    Args:
        df: 包含志愿信息的DataFrame
        
    Returns:
        字典格式：{会场名: {'第一志愿': 人数, '第二志愿': 人数, '第三志愿': 人数}}
    """
    stats = {committee: {'第一志愿': 0, '第二志愿': 0, '第三志愿': 0} for committee in COMMITTEES}
    
    if df.empty:
        return stats
    
    # 统计第一志愿
    first_choice = df['第一志愿委员会'].value_counts()
    for committee in COMMITTEES:
        if committee in first_choice.index:
            stats[committee]['第一志愿'] = int(first_choice[committee])
    
    # 统计第二志愿
    second_choice = df['第二志愿委员会'].value_counts()
    for committee in COMMITTEES:
        if committee in second_choice.index:
            stats[committee]['第二志愿'] = int(second_choice[committee])
    
    # 统计第三志愿
    third_choice = df['第三志愿委员会'].value_counts()
    for committee in COMMITTEES:
        if committee in third_choice.index:
            stats[committee]['第三志愿'] = int(third_choice[committee])
    
    return stats

def get_total_count(stats: Dict[str, Dict[str, int]], committee: str) -> int:
    """
    获取某个会场的总报名人数（第一+第二+第三志愿）
    
    Args:
        stats: 统计数据
        committee: 会场名称
        
    Returns:
        总报名人数
    """
    if committee not in stats:
        return 0
    return stats[committee]['第一志愿'] + stats[committee]['第二志愿'] + stats[committee]['第三志愿']

def get_capacity_ratio(stats: Dict[str, Dict[str, int]], committee: str) -> float:
    """
    计算第一志愿数与会场容量的比例
    
    Args:
        stats: 统计数据
        committee: 会场名称
        
    Returns:
        比例值（0-1之间，可能超过1）
    """
    if committee not in stats or committee not in COMMITTEE_CAPACITIES:
        return 0.0
    capacity = COMMITTEE_CAPACITIES[committee]
    first_choice = stats[committee]['第一志愿']
    if capacity == 0:
        return 0.0
    return first_choice / capacity

def process_data(excel_dir: str = ".") -> Tuple[Dict[str, Dict[str, int]], str]:
    """
    处理所有Excel文件并返回统计数据
    
    Args:
        excel_dir: Excel文件所在目录
        
    Returns:
        (统计数据字典, 更新时间字符串)
    """
    df = read_excel_files(excel_dir)
    stats = count_volunteers(df)
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return stats, update_time

if __name__ == "__main__":
    # 测试代码
    stats, update_time = process_data()
    print("统计数据：")
    for committee, data in stats.items():
        total = sum(data.values())
        print(f"{committee}: 第一志愿={data['第一志愿']}, 第二志愿={data['第二志愿']}, 第三志愿={data['第三志愿']}, 总计={total}")
    print(f"\n更新时间: {update_time}")

