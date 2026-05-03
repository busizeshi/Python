import re
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

# ==========================================
# 1. 基础配置
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LogicalRouting")


# ==========================================
# 2. Pydantic 模型：定义路由决策结果
# ==========================================
class RouteDecision(BaseModel):
    """路由决策结果"""
    target_route: str = Field(description="最终决定的目标路由/检索器名称")
    confidence: float = Field(description="置信度 (0.0 - 1.0)。逻辑路由命中通常为 1.0")
    matched_rules: List[str] = Field(description="命中了哪些规则，用于日志和排查")
    reason: str = Field(description="决策原因解释")


# ==========================================
# 3. 抽象规则类 (工程化设计的核心)
# ==========================================
class BaseRule(ABC):
    """
    路由规则基类。
    生产环境中，规则可能是存在数据库或配置中心里的，动态加载的。
    """

    def __init__(self, rule_name: str, target_route: str, priority: int):
        self.rule_name = rule_name
        self.target_route = target_route
        self.priority = priority  # 优先级，数字越大优先级越高

    @abstractmethod
    def evaluate(self, query: str) -> bool:
        """评估查询是否命中该规则"""
        pass


# ==========================================
# 4. 具体规则实现 (支持扩展)
# ==========================================
class KeywordRule(BaseRule):
    """基于关键词的匹配规则"""

    def __init__(self, rule_name: str, target_route: str, priority: int, keywords: List[str]):
        super().__init__(rule_name, target_route, priority)
        self.keywords = keywords

    def evaluate(self, query: str) -> bool:
        # 只要包含任意一个关键词即命中
        return any(kw in query for kw in self.keywords)


class RegexRule(BaseRule):
    """基于正则表达式的匹配规则"""

    def __init__(self, rule_name: str, target_route: str, priority: int, pattern: str):
        super().__init__(rule_name, target_route, priority)
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def evaluate(self, query: str) -> bool:
        return bool(self.pattern.search(query))


class LengthRule(BaseRule):
    """基于文本长度的规则 (例如太长的话直接走向量库，太短的话走精确匹配)"""

    def __init__(self, rule_name: str, target_route: str, priority: int, max_length: int = None,
                 min_length: int = None):
        super().__init__(rule_name, target_route, priority)
        self.max_length = max_length
        self.min_length = min_length

    def evaluate(self, query: str) -> bool:
        length = len(query.strip())
        if self.max_length and length > self.max_length:
            return False
        if self.min_length and length < self.min_length:
            return False
        return True


# ==========================================
# 5. 核心组件：逻辑路由器 (Logical Router)
# ==========================================
class LogicalRouter:
    def __init__(self):
        self.rules: List[BaseRule] = []
        self.fallback_route = "default_hybrid_retriever"  # 兜底路由

    def add_rule(self, rule: BaseRule):
        self.rules.append(rule)
        # 每次加完规则按优先级降序排序，保证高优先级的先被评估
        self.rules.sort(key=lambda x: x.priority, reverse=True)

    def route(self, query: str) -> RouteDecision:
        logger.info(f"开始逻辑路由评估: [{query}]")

        matched_rules = []
        # 按优先级逐个评估
        for rule in self.rules:
            if rule.evaluate(query):
                logger.info(f"命中规则: {rule.rule_name} -> 目标: {rule.target_route}")
                return RouteDecision(
                    target_route=rule.target_route,
                    confidence=1.0,  # 规则命中的置信度通常是拉满的
                    matched_rules=[rule.rule_name],
                    reason=f"强规则命中，优先级: {rule.priority}"
                )

        # 如果所有规则都没命中，走 fallback
        logger.warning(f"未命中任何规则，使用 Fallback 路由: {self.fallback_route}")
        return RouteDecision(
            target_route=self.fallback_route,
            confidence=0.0,  # 0.0 表示没中规则，提示下游可以考虑启动"语义路由"
            matched_rules=[],
            reason="未命中任何逻辑规则，使用默认兜底策略"
        )


# ==========================================
# 6. 运行与测试
# ==========================================
if __name__ == "__main__":
    router = LogicalRouter()

    # --- 注册业务规则 ---

    # 规则 1：错误码直接走精确词汇检索 (最高优先级 100)
    # 正则解释：匹配 0x 开头加数字字母，或者大写字母加数字组成的错误码
    router.add_rule(RegexRule(
        rule_name="ErrorCode_Regex",
        target_route="exact_match_es_retriever",
        priority=100,
        pattern=r"(0x[0-9a-fA-F]+|[A-Z]{2,4}-\d{3,5})"
    ))

    # 规则 2：看到图片/图表等词，走多模态检索 (优先级 90)
    router.add_rule(KeywordRule(
        rule_name="Multimodal_Keywords",
        target_route="multimodal_retriever",
        priority=90,
        keywords=["图片", "截图", "照片", "X光", "架构图"]
    ))

    # 规则 3：表格数据对比要求，走 SQL 或结构化数据检索 (优先级 80)
    router.add_rule(KeywordRule(
        rule_name="Structured_Comparison",
        target_route="sql_graph_retriever",
        priority=80,
        keywords=["财报", "销售额", "环比", "同比", "参数对比"]
    ))

    # --- 测试案例 ---
    test_queries = [
        "我的系统崩溃了，提示 0x80070422 怎么办？",  # 预期: exact_match_es_retriever (错误码匹配)
        "帮我找一下带有这张截图里错误提示的历史工单",  # 预期: multimodal_retriever (包含“截图”)
        "帮我对比下这三款车型的长宽高参数对比",  # 预期: sql_graph_retriever (包含“参数对比”)
        "如何解决 Python 里的内存泄漏问题？"  # 预期: default_hybrid_retriever (无规则命中，走兜底)
    ]

    for i, query in enumerate(test_queries, 1):
        print("\n" + "=" * 50)
        print(f"--- 测试案例 {i} ---")
        print(f"原问题   : {query}")

        decision = router.route(query)

        print(f"目标路由 : 🎯 {decision.target_route}")
        print(f"置信度   : {decision.confidence}")
        print(f"命中规则 : {decision.matched_rules}")
        print(f"原因     : 📝 {decision.reason}")
        print("=" * 50)