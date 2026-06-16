"""年报结构化报告工具 — 多指标并行搜索 → 整理文本 → 交 LLM 分析。"""

from knowledge.search import unified_search
from tools.registry import register


def financial_report(stock_name):
    """搜索指定公司的关键财务指标，返回整理后的年报数据。

    搜索营收、净利润、增长率等核心指标，合并去重后返回结构化文本。
    LLM 拿到整理好的数据后自行做分析和格式化。
    """
    try:
        metrics = [
            "营业收入 2024年",
            "归属于上市公司股东的净利润",
            "营业收入 同比增长",
            "基本每股收益",
        ]

        all_chunks = []
        seen = set()
        for metric in metrics:
            results = unified_search(
                f"{stock_name} {metric}", top_k=3, collections=["annual_reports"]
            )
            for r in results:
                # 去重：同一段文本不重复
                key = r["content"][:80]
                if key not in seen and r["content"].strip():
                    seen.add(key)
                    all_chunks.append(r)

        if not all_chunks:
            return f"年报库中未找到 {stock_name} 的财务数据"

        # 按相关度排序
        all_chunks.sort(key=lambda x: x["distance"])

        lines = [f"{stock_name} 年报财务数据\n"]
        for i, r in enumerate(all_chunks, 1):
            lines.append(f"## 数据块 {i}（距离 {r['distance']}）")
            lines.append(r["content"])
            lines.append("---")

        return "\n".join(lines)

    except Exception as e:
        return f"查询失败: {e}"


REPORT_DEF = {
    "type": "function",
    "function": {
        "name": "financial_report",
        "description": "查询上市公司年报，搜索营业收入、净利润、增长率等核心财务指标，返回整理后的年报原文供分析",
        "parameters": {
            "type": "object",
            "properties": {
                "stock_name": {
                    "type": "string",
                    "description": "公司名称，如 贵州茅台、比亚迪",
                },
            },
            "required": ["stock_name"],
        },
    },
}

register("financial_report", REPORT_DEF, financial_report)
