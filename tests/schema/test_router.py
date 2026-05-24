import pytest
from pydantic import ValidationError
# 确保改成你实际的模块导入路径，比如：from src.schemas.router import RouterDecision, Intent
from src.schema.router import RouterDecision, Intent 

def test_router_decision_success():
    """测试正常传入所有参数时的正确解析"""
    data = {
        "intent": "chat",  # 传入字符串，触发 use_enum_values=True 自动解析
        "confidence": 0.85,
        "reasoning": "用户只是在打招呼聊天",
        "extracted_info": {"user_name": "张三"}
    }
    
    decision = RouterDecision(**data)
    
    assert decision.intent == "chat"  # 因为 use_enum_values=True，拿出来的是字符串
    assert decision.confidence == 0.85
    assert decision.reasoning == "用户只是在打招呼聊天"
    assert decision.extracted_info == {"user_name": "张三"}

def test_router_decision_default_value():
    """测试不传 extracted_info 时，是否能正确使用默认值 None"""
    decision = RouterDecision(
        intent=Intent.METTING,
        confidence=0.9,
        reasoning="用户提到了预约会议"
    )
    
    assert decision.intent == "meeting"
    assert decision.extracted_info is None  # 验证默认值生效

def test_router_decision_required_fields():
    """测试缺少必填字段（带有 ... 的字段）时，是否会抛出校验错误"""
    # 缺少 confidence 和 reasoning
    with pytest.raises(ValidationError) as exc_info:
        RouterDecision(intent=Intent.CHAT)
    
    errors = exc_info.value.errors()
    missing_fields = [err["loc"][0] for err in errors]
    
    assert "confidence" in missing_fields
    assert "reasoning" in missing_fields

@pytest.mark.parametrize("invalid_confidence", [-0.1, 1.1])
def test_router_decision_confidence_bounds(invalid_confidence):
    """测试 confidence 的边界值校验（ge=0.0, le=1.0）"""
    with pytest.raises(ValidationError):
        RouterDecision(
            intent=Intent.UNKNOWN,
            confidence=invalid_confidence,  # 超出 0.0 ~ 1.0 的范围
            reasoning="不可靠的置信度"
        )