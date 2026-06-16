"""A 股实时行情查询工具。"""

import akshare as ak

from tools.registry import register


def get_stock_price(code):
    """查询 A 股实时价格"""
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if row.empty:
            return f"未找到股票代码 {code}"
        r = row.iloc[0]
        return (
            f"{r['名称']}({code})\n"
            f"最新价: {r['最新价']}\n"
            f"涨跌幅: {r['涨跌幅']}%\n"
            f"成交量: {r['成交量']}\n"
            f"成交额: {r['成交额']}"
        )
    except Exception as e:
        return f"查询失败: {e}"


PRICE_DEF = {
    "type": "function",
    "function": {
        "name": "get_stock_price",
        "description": "查询 A 股实时行情，返回最新价、涨跌幅、成交量、成交额",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "股票代码，如 600519（茅台）"}
            },
            "required": ["code"],
        },
    },
}

register("get_stock_price", PRICE_DEF, get_stock_price)
