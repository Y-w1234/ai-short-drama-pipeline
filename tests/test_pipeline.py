"""
管线测试套件（Phase 1-3 修复验证）

覆盖:
- VULN-02: API Key 安全（删除 --api-key）
- VULN-03: 错误脱敏 + 重试
- VULN-05: JSON Schema 校验 + parse_error 阻断
- Phase 2: 并行架构 + Few-Shot Prompt 升级
- Phase 3: Token 用量统计 (C6)
- Demo 模式端到端

运行: python -m pytest tests/test_pipeline.py -v
"""
import sys
import json
import inspect
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import (
    LLMClient, ShortDramaPipeline,
    SYS_CHARACTER, SYS_SCENE, SYS_PROPS,
    SYS_STORYBOARD, SYS_IMAGE, SYS_VIDEO, SYS_QC,
    validate_character_output, extract_json_from_llm,
    parse_scene, parse_props,
)
import main as _main


@pytest.fixture
def client():
    return LLMClient(provider="deepseek")


# ============================================================
# VULN-02: API Key 安全
# ============================================================
class TestApiKeySecurity:
    """测试 API Key 仅通过环境变量获取，不支持命令行传参"""

    def test_no_api_key_in_llmclient_init(self):
        """LLMClient.__init__ 不应有 api_key 参数"""
        params = list(
            LLMClient.__init__.__code__.co_varnames[
                :LLMClient.__init__.__code__.co_argcount])
        assert "api_key" not in params

    def test_no_api_key_in_pipeline_init(self):
        """ShortDramaPipeline.__init__ 不应有 api_key 参数"""
        params = list(
            ShortDramaPipeline.__init__.__code__.co_varnames[
                :ShortDramaPipeline.__init__.__code__.co_argcount])
        assert "api_key" not in params

    def test_load_dotenv_callable(self):
        """_load_dotenv 应可调用"""
        assert callable(_main._load_dotenv)


# ============================================================
# VULN-03: 错误脱敏 + 重试
# ============================================================
class TestErrorHandling:
    """测试错误消息脱敏和指数退避重试"""

    def test_error_messages_class_level(self):
        """错误消息应为类级常量"""
        assert hasattr(LLMClient, "_ERROR_MESSAGES")

    def test_no_base_url_in_error_messages(self):
        """错误消息不应暴露内部 URL"""
        msgs = LLMClient._ERROR_MESSAGES
        assert all("ark.cn" not in v for v in msgs.values())
        assert all("api.deepseek.com" not in v for v in msgs.values())

    def test_chat_has_max_retries_param(self, client):
        """chat() 应有 max_retries 参数"""
        assert "max_retries" in LLMClient.chat.__code__.co_varnames

    def test_chat_has_retry_loop(self, client):
        """chat() 应包含重试循环逻辑"""
        source = inspect.getsource(LLMClient.chat)
        assert "attempt" in source


# ============================================================
# VULN-05: JSON Schema 校验
# ============================================================
class TestJsonValidation:
    """测试 LLM 输出 Schema 校验"""

    def test_valid_character_passes(self):
        """有效的角色数据应通过校验"""
        data = {
            "characters": [
                {"id": "char_001", "name": "张三", "type": "主角",
                 "gender": "男", "age_group": "青年",
                 "personality": ["冲动"], "appearance": ["短发"]}
            ],
            "total": 1
        }
        result = validate_character_output(data)
        assert result["total"] == 1

    def test_parse_error_blocked(self):
        """parse_error 标志应触发 RuntimeError"""
        with pytest.raises(RuntimeError):
            validate_character_output(
                {"raw_output": "garbage", "parse_error": True})

    def test_id_normalized_char1_to_char_001(self):
        """char1 应归一化为 char_001"""
        data = {
            "characters": [
                {"id": "char1", "name": "张三", "type": "主角",
                 "gender": "男", "age_group": "青年",
                 "personality": [], "appearance": []}
            ],
            "total": 1
        }
        result = validate_character_output(data)
        assert result["characters"][0]["id"] == "char_001"

    def test_id_normalized_char_dash_to_char_002(self):
        """char-02 应归一化为 char_002"""
        data = {
            "characters": [
                {"id": "char-02", "name": "李四", "type": "配角",
                 "gender": "男", "age_group": "中年",
                 "personality": [], "appearance": []}
            ],
            "total": 1
        }
        result = validate_character_output(data)
        assert result["characters"][0]["id"] == "char_002"

    def test_missing_name_detected(self):
        """缺少 name 字段应被检测"""
        data = {
            "characters": [
                {"id": "char_001", "name": "", "type": "主角",
                 "gender": "男", "age_group": ""}
            ],
            "total": 1
        }
        with pytest.raises(RuntimeError):
            validate_character_output(data)

    def test_parse_scene_checks_parse_error(self):
        """parse_scene 应检查 parse_error"""
        source = inspect.getsource(parse_scene)
        assert "parse_error" in source

    def test_parse_props_checks_parse_error(self):
        """parse_props 应检查 parse_error"""
        source = inspect.getsource(parse_props)
        assert "parse_error" in source


# ============================================================
# Phase 2: 并行架构
# ============================================================
class TestParallelArchitecture:
    """测试 Phase 1-3 和 Phase 5-6 的并行化"""

    def test_thread_pool_executor_in_source(self):
        """pipeline.run() 应使用 ThreadPoolExecutor"""
        source = inspect.getsource(ShortDramaPipeline.run)
        assert "ThreadPoolExecutor" in source

    def test_two_threadpool_instances(self):
        """应有两个 ThreadPoolExecutor 使用点（Phase 1-3 和 Phase 5-6）"""
        source = inspect.getsource(ShortDramaPipeline.run)
        assert source.count("ThreadPoolExecutor") >= 2

    def test_storyboard_json_cached(self):
        """Phase 5-6 应缓存 storyboard_json"""
        source = inspect.getsource(ShortDramaPipeline.run)
        assert "storyboard_json" in source

    def test_parallel_error_handling_exists(self):
        """并行执行应有错误处理"""
        source = inspect.getsource(ShortDramaPipeline.run)
        assert "RuntimeError" in source
        assert "并行" in source


# ============================================================
# Phase 2: Prompt Few-Shot 示例
# ============================================================
class TestPromptFewShot:
    """测试 7 个 System Prompt 的 few-shot 示例"""

    PROMPTS = [
        ("SYS_CHARACTER", SYS_CHARACTER),
        ("SYS_SCENE", SYS_SCENE),
        ("SYS_PROPS", SYS_PROPS),
        ("SYS_STORYBOARD", SYS_STORYBOARD),
        ("SYS_IMAGE", SYS_IMAGE),
        ("SYS_VIDEO", SYS_VIDEO),
        ("SYS_QC", SYS_QC),
    ]

    @pytest.mark.parametrize("name,prompt", PROMPTS)
    def test_prompt_has_few_shot_example(self, name, prompt):
        """每个 Prompt 应有 few-shot 示例标记"""
        assert "【示例】" in prompt, f"{name} missing few-shot example"


# ============================================================
# Phase 3: Token 用量统计 (C6)
# ============================================================
class TestTokenUsage:
    """测试 API Token 用量累计追踪"""

    def test_token_usage_attr_exists(self, client):
        assert hasattr(client, "token_usage")

    def test_token_usage_has_all_fields(self, client):
        """应包含 4 个必填字段"""
        for key in ["prompt_tokens", "completion_tokens", "total_tokens", "api_calls"]:
            assert key in client.token_usage

    def test_get_token_usage_callable(self, client):
        assert callable(client.get_token_usage)

    def test_get_token_usage_returns_dict(self, client):
        usage = client.get_token_usage()
        assert isinstance(usage, dict)

    def test_get_token_usage_returns_copy(self, client):
        """get_token_usage 应返回副本，不是引用"""
        usage = client.get_token_usage()
        assert usage is not client.token_usage


# ============================================================
# Phase 2: Simplify 审查修复
# ============================================================
class TestSimplifyFixes:
    """测试 /simplify 4-agent 审查后的修复"""

    def test_suspicious_patterns_class_level(self):
        assert hasattr(LLMClient, "_SUSPICIOUS_PATTERNS")

    def test_quality_has_named_vars(self):
        """质量阻断条件应有命名变量"""
        source = inspect.getsource(ShortDramaPipeline.run)
        assert "score_ok" in source
        assert "must_redo" in source

    def test_resolve_safe_path_shared(self):
        """应有共享路径解析器"""
        assert callable(_main._resolve_safe_path)


# ============================================================
# End-to-End: Demo 模式
# ============================================================
class TestDemoMode:
    """测试离线 Demo 模式的完整性"""

    def test_demo_characters_work(self, client):
        raw = client._demo_chat("你是角色提取专家，提取所有出场角色", "test")
        data = json.loads(raw)
        assert data["total"] == 3

    def test_demo_storyboard_works(self, client):
        raw = client._demo_chat("你是一个资深短剧导演/分镜师", "test")
        data = json.loads(raw)
        assert len(data.get("storyboard", [])) == 12

    def test_demo_qc_works(self, client):
        raw = client._demo_chat("你是影视质量审核专家", "test")
        data = json.loads(raw)
        assert data.get("overall_score", 0) > 0

    def test_unknown_topic_returns_empty_json(self, client):
        raw = client._demo_chat("完全未知的系统提示", "test")
        data = json.loads(raw)
        assert data == {}

    def test_all_system_prompts_defined(self):
        """7 个 System Prompt 都应已定义"""
        for name in ["SYS_CHARACTER", "SYS_SCENE", "SYS_PROPS",
                      "SYS_STORYBOARD", "SYS_IMAGE", "SYS_VIDEO", "SYS_QC"]:
            assert name in dir()


# ============================================================
# Pipeline 集成: 全流水线端到端
# ============================================================
class TestPipelineE2E:
    """全流水线端到端集成测试"""

    def test_full_demo_run(self):
        """完整 Demo 模式运行应成功"""
        pipeline = ShortDramaPipeline(provider="deepseek")
        script = """【第一场】办公室 - 下午
        张三：李总，不好了！服务器宕机了！
        李总：什么？！快去修！"""
        result = pipeline.run(script)
        assert result is not None
        assert "metadata" in result
        assert "characters" in result
        assert "scenes" in result
        assert "props" in result
        assert "storyboard" in result
        assert "image_prompts" in result
        assert "video_prompts" in result
        assert "quality_report" in result
        assert "safety_scan" in result
        assert result["safety_scan"]["passed"] is True

    def test_output_has_token_usage(self):
        """输出应包含 token_usage 字段"""
        pipeline = ShortDramaPipeline(provider="deepseek")
        script = "张三：你好。李四：你好。"
        result = pipeline.run(script)
        assert "token_usage" in result["metadata"]
        assert isinstance(result["metadata"]["token_usage"], dict)

    def test_output_has_safety_scan(self):
        """输出应包含 safety_scan 字段"""
        pipeline = ShortDramaPipeline(provider="deepseek")
        script = "张三：你好。李四：你好。"
        result = pipeline.run(script)
        assert "safety_scan" in result
        assert "passed" in result["safety_scan"]
