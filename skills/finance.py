"""财报分析技能 — 当用户查询财务数据时自动激活。"""

from skills.registry import register_skill

FINANCE_CONTENT = """你是财报分析专家。当用户查询财务数据时，遵循以下规范：

1. **数据来源优先**：优先从 search_knowledge 或 search_financial 获取年报数据
2. **结构化展示**：用表格展示关键指标（营收、净利润、毛利率、同比增长率）
3. **单位统一**：年报数据通常是"千元"或"元"，换算为"亿元"展示
4. **对比分析**：如有同比数据，自动计算增长率
5. **归因分析**：解释数据变化的原因（行业趋势、公司战略、季节性因素）
6. **风险提示**：最后加一句免责声明，数据仅供参考"""

register_skill(
    name="financial_analysis",
    trigger="营收|利润|财报|年报|净利润|毛利率|资产负债|现金流",
    description="财报分析",
    content=FINANCE_CONTENT,
)
