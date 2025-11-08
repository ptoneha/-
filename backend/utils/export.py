"""数据导出工具"""
import csv
import json
from io import StringIO
from typing import List, Dict, Any


def export_to_csv(data: List[Dict[str, Any]], columns: List[str]) -> str:
    """导出数据为CSV格式"""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def export_to_json(data: List[Dict[str, Any]]) -> str:
    """导出数据为JSON格式"""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)

