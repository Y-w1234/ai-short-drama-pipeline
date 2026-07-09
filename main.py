"""
AI 短剧生成工作流 —— 纯 Python 实现
对标岗位：AI应用开发工程师（AI短剧方向）

用法：
    python main.py                                                # 运行内置测试剧本
    python main.py --script sample_script.txt                     # 指定剧本文件
    python main.py --script sample_script.txt --model deepseek    # 指定模型
    python main.py --demo                                         # 脱机演示（不调API）
"""

import json
import sys
import os
import asyncio
from pathlib import Path
from typing import Optional

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-1-5-pro-32k-250115",
        "api_key_env": "DOUBAO_API_KEY",
    },
}


# ============================================================
# LLM 客户端
# ============================================================
class LLMClient:
    def __init__(self, provider: str = "deepseek", api_key: str = None):
        cfg = CONFIG.get(provider, CONFIG["deepseek"])
        self.base_url = cfg["base_url"]
        self.model = cfg["model"]
        self.api_key = api_key or os.environ.get(cfg["api_key_env"], "")
        if not self.api_key:
            print(f"[WARN] {cfg['api_key_env']} 未设置，将使用脱机Demo模式")

    def chat(self, system: str, user: str, temperature: float = 0.3,
             max_tokens: int = 4096) -> str:
        if not self.api_key:
            return self._demo_chat(system, user)

        import requests
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _demo_chat(self, system: str, user: str) -> str:
        """离线演示：根据 system prompt 主题返回模拟 JSON"""
        if "角色提取" in system or "提取所有出场角色" in system:
            return json.dumps({
                "characters": [
                    {"id": "char_001", "name": "张三", "type": "主角", "gender": "男",
                     "age_group": "青年", "personality": ["冲动", "正义", "幽默"],
                     "appearance": ["短发寸头", "深色连帽卫衣", "左眉浅疤"],
                     "first_line": "李总，不好了！服务器宕机了！",
                     "relationships": [{"to": "李总", "relation": "上下级"}, {"to": "小王", "relation": "同事"}]},
                    {"id": "char_002", "name": "李总", "type": "配角", "gender": "男",
                     "age_group": "中年", "personality": ["严肃", "果断", "易怒"],
                     "appearance": ["西装革履", "金丝眼镜", "头发梳得一丝不苟"],
                     "first_line": "什么？！小王呢？叫他立刻去机房！",
                     "relationships": [{"to": "张三", "relation": "上级"}, {"to": "小王", "relation": "上级"}]},
                    {"id": "char_003", "name": "小王", "type": "配角", "gender": "男",
                     "age_group": "青年", "personality": ["冷静", "技术宅", "隐忍"],
                     "appearance": ["戴耳机", "格子衬衫", "黑框眼镜"],
                     "first_line": "我一直在说这事，你们没人听啊。",
                     "relationships": [{"to": "李总", "relation": "下属"}, {"to": "张三", "relation": "同事"}]},
                ],
                "total": 3,
            }, ensure_ascii=False)
        elif "场景" in system or "提取所有场景" in system:
            return json.dumps({
                "scenes": [
                    {"id": "scene_001", "name": "李总办公室", "location_type": "室内",
                     "time_of_day": "下午",
                     "description": "20平米现代办公室，落地窗朝向CBD，办公桌堆满文件，墙上挂着'奋斗'书法牌匾，角落有饮水机和绿植",
                     "lighting": "下午暖光从落地窗斜射入室，形成明暗对比",
                     "atmosphere": "紧张", "color_tone": "暖色调偏灰",
                     "characters_present": ["张三", "李总", "小王"],
                     "key_props": ["办公桌", "电脑显示器", "文件堆", "咖啡杯", "钢笔"]},
                    {"id": "scene_002", "name": "机房", "location_type": "室内",
                     "time_of_day": "傍晚",
                     "description": "狭长机房，两排服务器机柜延伸到深处，蓝绿色指示灯闪烁，只有服务器风扇的白噪音，空调开得很足",
                     "lighting": "服务器蓝色LED是唯一光源，映在小王脸上",
                     "atmosphere": "孤独", "color_tone": "冷色调蓝黑",
                     "characters_present": ["小王"],
                     "key_props": ["服务器机柜", "蓝色LED指示灯", "手机", "显示器"]},
                ],
                "total": 2,
            }, ensure_ascii=False)
        elif "道具" in system or "提取所有道具" in system:
            return json.dumps({
                "props": [
                    {"id": "prop_001", "name": "手机", "category": "电子产品", "priority": "A",
                     "scenes": ["机房"], "used_by": ["小王"],
                     "description": "黑色智能手机，屏幕上显示猎头发来的消息"},
                    {"id": "prop_002", "name": "钢笔", "category": "手持", "priority": "B",
                     "scenes": ["李总办公室"], "used_by": ["李总"],
                     "description": "银色万宝龙钢笔，李总的标志性物品"},
                    {"id": "prop_003", "name": "耳机", "category": "电子产品", "priority": "B",
                     "scenes": ["李总办公室"], "used_by": ["小王"],
                     "description": "黑色头戴式降噪耳机"},
                    {"id": "prop_004", "name": "服务器机柜", "category": "场景装饰", "priority": "B",
                     "scenes": ["机房"], "used_by": [],
                     "description": "标准42U机柜，蓝色指示灯规律闪烁"},
                ],
                "total": 4,
            }, ensure_ascii=False)
        elif "分镜" in system or "分镜师" in system:
            return json.dumps({
                "project": {"title": "服务器宕机了", "genre": "职场/剧情", "estimated_duration": "120秒"},
                "storyboard": [
                    {"shot_id": "shot_001", "scene_id": "scene_001", "shot_type": "中景",
                     "camera_angle": "平视", "camera_setup": "过肩视角，从李总身后拍向门口",
                     "visual_description": "办公室门被猛地推开，张三气喘吁吁站在门口。逆光勾出他的轮廓。李总从办公桌后抬起头，手中的钢笔停在半空。阳光透过落地窗在地面投下长方形的光斑。",
                     "character_actions": {"张三": "推开门冲入，气喘吁吁", "李总": "抬头皱眉"},
                     "dialogue": "张三：李总，不好了！服务器宕机了！",
                     "duration_seconds": 4, "camera_movement": "固定", "transition": "硬切", "mood": "紧张"},
                    {"shot_id": "shot_002", "scene_id": "scene_001", "shot_type": "近景",
                     "camera_angle": "平视", "camera_setup": "正面拍李总",
                     "visual_description": "李总猛地站起来，椅子向后滑出。他双手撑在桌上，面部肌肉紧绷，金丝眼镜后的眼睛瞪得很大。文件被碰落散在地上。",
                     "character_actions": {"李总": "猛地站起，双手撑桌，面部紧绷"},
                     "dialogue": "李总：什么？！小王呢？叫他立刻去机房！",
                     "duration_seconds": 3, "camera_movement": "固定", "transition": "硬切", "mood": "愤怒"},
                    {"shot_id": "shot_003", "scene_id": "scene_001", "shot_type": "中景",
                     "camera_angle": "平视", "camera_setup": "摇镜转向角落",
                     "visual_description": "镜头转向办公室角落。小王坐在工位上，慢慢摘下耳机。他表情平静，仿佛一切都在意料之中。格子衬衫在冷气下微微飘动。",
                     "character_actions": {"小王": "慢慢摘下耳机，面无表情"},
                     "dialogue": "小王：我一直在说这事，你们没人听啊。",
                     "duration_seconds": 4, "camera_movement": "摇", "transition": "硬切", "mood": "讽刺"},
                    {"shot_id": "shot_004", "scene_id": "scene_001", "shot_type": "近景",
                     "camera_angle": "平视", "camera_setup": "正面拍李总",
                     "visual_description": "李总转头瞪着小王，面部因愤怒而微红。他单手整理了一下领带，动作僵硬。",
                     "character_actions": {"李总": "转头瞪小王，单手整理领带"},
                     "dialogue": "李总：那你还坐着干嘛？快去修！",
                     "duration_seconds": 2, "camera_movement": "固定", "transition": "硬切", "mood": "愤怒"},
                    {"shot_id": "shot_005", "scene_id": "scene_001", "shot_type": "特写",
                     "camera_angle": "平视", "camera_setup": "拍小王的手表",
                     "visual_description": "小王低头看了一眼手表。手腕上是普通的电子表。他嘴角微微上扬，几乎看不出。",
                     "character_actions": {"小王": "看表，嘴角微扬"},
                     "dialogue": "小王：已经在跑了...三分钟后恢复。",
                     "duration_seconds": 3, "camera_movement": "固定→微推", "transition": "硬切", "mood": "冷静"},
                    {"shot_id": "shot_006", "scene_id": "scene_001", "shot_type": "中景",
                     "camera_angle": "平视", "camera_setup": "拍张三",
                     "visual_description": "张三长出一口气，整个人瘫坐在椅子上。他用手擦了擦额头上的汗，脸上写满了'逃过一劫'。",
                     "character_actions": {"张三": "瘫坐椅子上，擦汗"},
                     "dialogue": "张三：吓死我了，还以为要背锅了。",
                     "duration_seconds": 3, "camera_movement": "固定", "transition": "淡入淡出", "mood": "轻松"},
                    {"shot_id": "shot_007", "scene_id": "scene_002", "shot_type": "全景",
                     "camera_angle": "平视", "camera_setup": "机房入口视角",
                     "visual_description": "机房内两排服务器机柜延伸到深处，蓝色LED灯规律闪烁。小王独自坐在角落的折叠椅上，面前是监视器屏幕。空调出风口吹动他额前的头发。",
                     "character_actions": {"小王": "独坐角落，面对监视器"},
                     "dialogue": "",
                     "duration_seconds": 4, "camera_movement": "推", "transition": "硬切", "mood": "孤独"},
                    {"shot_id": "shot_008", "scene_id": "scene_002", "shot_type": "近景",
                     "camera_angle": "平视", "camera_setup": "正面拍小王的脸",
                     "visual_description": "小王脸被服务器蓝光映成冷色调。他自言自语，声音很轻。屏幕上的监控数据一行行跳动。",
                     "character_actions": {"小王": "自言自语，盯着屏幕"},
                     "dialogue": "小王：每次都是我来救火，涨薪的时候怎么没人想起我？",
                     "duration_seconds": 4, "camera_movement": "固定", "transition": "硬切", "mood": "压抑"},
                    {"shot_id": "shot_009", "scene_id": "scene_002", "shot_type": "大特写",
                     "camera_angle": "俯视", "camera_setup": "拍手机屏幕",
                     "visual_description": "放在桌面上的手机震动，屏幕亮起。一条来自'猎头-Alan'的微信消息弹出：'王工，上次聊的那个机会，对方CEO很感兴趣，薪资可以给到现在的两倍。方便回个电话？'",
                     "character_actions": {},
                     "dialogue": "",
                     "duration_seconds": 5, "camera_movement": "固定→微推", "transition": "硬切", "mood": "转折"},
                    {"shot_id": "shot_010", "scene_id": "scene_002", "shot_type": "近景",
                     "camera_angle": "平视", "camera_setup": "正面拍小王",
                     "visual_description": "小王盯着手机屏幕，一动不动，只有眼神在闪烁。他犹豫了三秒——这三秒被拉得很长。他的右手拇指悬在屏幕上方，微微颤抖。",
                     "character_actions": {"小王": "盯着屏幕，犹豫，拇指悬空微微颤抖"},
                     "dialogue": "",
                     "duration_seconds": 5, "camera_movement": "固定", "transition": "硬切", "mood": "紧张"},
                    {"shot_id": "shot_011", "scene_id": "scene_002", "shot_type": "大特写",
                     "camera_angle": "俯视", "camera_setup": "拍手机屏幕 + 手指",
                     "visual_description": "小王的拇指落下，在手机屏幕上打出一行字：'我考虑一下。' 然后点击发送。消息气泡变成绿色。屏幕短暂变黑后，服务器恢复正常的绿灯亮了。",
                     "character_actions": {"小王": "打字'我考虑一下'，点击发送"},
                     "dialogue": "",
                     "duration_seconds": 4, "camera_movement": "固定", "transition": "硬切", "mood": "决断"},
                    {"shot_id": "shot_012", "scene_id": "scene_002", "shot_type": "全景",
                     "camera_angle": "仰视", "camera_setup": "从小王身后仰拍",
                     "visual_description": "小王站起身，关上手机屏幕。服务器绿灯亮起的瞬间，他的脸上同时映着蓝光和绿光。他嘴角扬起一个微小的弧度，转身走向机房门口。镜头定格在他的背影上。",
                     "character_actions": {"小王": "站起身，嘴角微扬，走向门口"},
                     "dialogue": "",
                     "duration_seconds": 4, "camera_movement": "固定", "transition": "淡出", "mood": "释然+悬念"},
                ],
            }, ensure_ascii=False)
        elif "画" in system or "绘画" in system:
            return json.dumps({
                "prompts": [
                    {"shot_id": f"shot_{i:03d}",
                     "prompt_cn": f"影视级现实主义，电影质感，{['办公室场景，年轻男子冲入','中年男人愤怒站起','戴耳机青年平静转头'][i%3]}，8K超清，专业布光",
                     "prompt_en": f"cinematic photorealistic, 8k, professional lighting, film grain, {['office interior','angry boss','calm tech guy'][i%3]}",
                     "negative_prompt": "blur, deformed, extra fingers, text artifacts, anime, cartoon",
                     "style_tags": ["cinematic", "photorealistic", "professional lighting"],
                     "aspect_ratio": "16:9"}
                    for i in range(1, 13)
                ],
            }, ensure_ascii=False)
        elif "视频" in system:
            return json.dumps({
                "video_prompts": [
                    {"shot_id": f"shot_{i:03d}",
                     "prompt": f"cinematic video, smooth camera movement, photorealistic, 24fps, {i}-second shot",
                     "motion_description": "自然动作流畅",
                     "camera_motion": "固定→微摇" if i == 1 else "固定",
                     "duration_seconds": 4}
                    for i in range(1, 13)
                ],
            }, ensure_ascii=False)
        elif "审核" in system or "质量" in system:
            return json.dumps({
                "scores": {
                    "narrative_flow": {"score": 5, "reason": "12个分镜叙事流畅，起承转合完整"},
                    "visual_consistency": {"score": 5, "reason": "角色外观在分镜间保持一致"},
                    "pacing": {"score": 4, "reason": "开头略快，中间张弛有度"},
                    "emotional_expression": {"score": 5, "reason": "景别精准服务情绪，特写和全景交替运用到位"},
                    "generatability": {"score": 5, "reason": "Prompt质量高，可直接用于AI生成"},
                },
                "overall_score": 4.8,
                "verdict": "通过",
                "suggestions": ["shot_004可以尝试加入晃动镜头增强紧张感"],
            }, ensure_ascii=False)
        return "{}"


# ============================================================
# 所有 System Prompt
# ============================================================
SYS_CHARACTER = """你是一位专业的影视剧本分析专家。请从以下剧本中提取所有出场角色。

对每个角色输出：
1. id: 编号(char_001格式)  2. name: 角色名  3. type: 主角/反派/配角/龙套
4. gender: 男/女  5. age_group: 少年/青年/中年/老年
6. personality: 3-5个形容词组成的数组  7. appearance: 3个外貌特征组成的数组(用于AI画图)
8. first_line: 第一句台词原文  9. relationships: [{to:对方名, relation:关系}]

输出严格JSON(不要markdown包裹): {"characters":[...], "total":数字}"""

SYS_SCENE = """你是影视美术指导。从剧本提取所有场景。

每个场景输出：
id, name, location_type(室内/室外/半室内), time_of_day, description(80字+空间描述，能画背景图),
lighting, atmosphere, color_tone, characters_present(角色名数组), key_props(道具名数组)

输出严格JSON: {"scenes":[...], "total":数字}"""

SYS_PROPS = """你是影视道具师。从剧本提取所有道具，按重要性分级。

每个道具输出：
id, name, category(手持/场景装饰/服装/电子产品), priority(A级特写/B级普通/C级背景),
scenes(场景名数组), used_by(角色名数组), description(30字视觉描述)

输出严格JSON: {"props":[...], "total":数字}"""

SYS_STORYBOARD = """你是资深短剧导演/分镜师。根据剧本和已提取的角色/场景/道具信息生成详细分镜表。

原则: 每个情节转折至少1个分镜 | 对白用正反打 | 情绪高点用特写 | 环境建立用全景 | 1分钟约8-15分镜 | 同角色多分镜中外貌必须一致

每个分镜输出:
shot_id, scene_id, shot_type(远景/全景/中景/近景/特写/大特写), camera_angle(平视/俯视/仰视/过肩/主观视角),
camera_setup(机位描述), visual_description(100字+画面描述，能直接用于AI生成),
character_actions({角色名: 动作表情描述,...}), dialogue(对白), duration_seconds(数字),
camera_movement(固定/推/拉/摇/移/跟), transition(硬切/淡入淡出/叠化), mood(情绪)

输出严格JSON: {"project":{"title":"","genre":"","estimated_duration":""}, "storyboard":[...]}"""

SYS_IMAGE = """你是AI绘画Prompt工程师。为每个分镜生成中英文AI绘画Prompt。

Prompt结构: [主体+动作] + [场景环境] + [光线氛围] + [视角构图] + [风格标签(cinematic,photorealistic,8k)]
负向Prompt: blur,deformed,extra fingers,text artifacts

输出严格JSON: {"prompts":[{"shot_id":"","prompt_cn":"","prompt_en":"","negative_prompt":"","style_tags":[],"aspect_ratio":"16:9"}]}"""

SYS_VIDEO = """你是AI视频生成专家。为每个分镜生成视频Prompt。

包含: 画面内容+角色动作(谁动/怎么动/速度)+摄像机运动+时长

输出严格JSON: {"video_prompts":[{"shot_id":"","prompt":"","motion_description":"","camera_motion":"","duration_seconds":数字}]}"""

SYS_QC = """你是影视质量审核专家。审核分镜方案，5维度每项0-5分:
1.narrative_flow 叙事连贯性  2.visual_consistency 视觉一致性  3.pacing 节奏把控
4.emotional_expression 情感表达  5.generatability Prompt可生成性

输出JSON: {"scores":{维度名:{score:数字,reason:""},...}, "overall_score":数字, "verdict":"通过/修改/重做", "suggestions":[]}"""


# ============================================================
# 各节点处理函数
# ============================================================
def preprocess(script_text: str) -> dict:
    """节点1: 剧本预处理"""
    text = script_text.strip()
    text = "\n".join(line for line in text.split("\n") if not (line.startswith("#") or line.startswith("//")))
    lines = [l for l in text.split("\n") if l.strip()]
    chars = len(text.replace(" ", "").replace("\n", ""))
    return {
        "cleaned_text": text,
        "line_count": len(lines),
        "char_count": chars,
        "estimated_minutes": round(chars / 200, 1),
    }


def extract_json_from_llm(raw: str) -> dict:
    """从 LLM 原始输出中提取 JSON（容错处理）"""
    text = raw.strip()
    # 去除 markdown 代码块包裹
    for fence in ["```json", "```"]:
        if fence in text:
            parts = text.split(fence)
            text = parts[1] if len(parts) >= 2 else text
            if "```" in text:
                text = text.split("```")[0]
            break
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试匹配第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return {"raw_output": raw, "parse_error": True}


def parse_character(raw: str) -> dict:
    data = extract_json_from_llm(raw)
    return {"characters": data.get("characters", []), "total": data.get("total", 0)}


def parse_scene(raw: str) -> dict:
    data = extract_json_from_llm(raw)
    return {"scenes": data.get("scenes", []), "total": data.get("total", 0)}


def parse_props(raw: str) -> dict:
    data = extract_json_from_llm(raw)
    return {"props": data.get("props", []), "total": data.get("total", 0)}


def parse_storyboard(raw: str) -> dict:
    return extract_json_from_llm(raw)


def parse_image_prompts(raw: str) -> dict:
    return extract_json_from_llm(raw)


def parse_video_prompts(raw: str) -> dict:
    return extract_json_from_llm(raw)


def parse_qc_report(raw: str) -> dict:
    return extract_json_from_llm(raw)


# ============================================================
# 主流水线
# ============================================================
class ShortDramaPipeline:
    def __init__(self, provider: str = "deepseek", api_key: str = None):
        self.llm = LLMClient(provider, api_key)
        self.verbose = True

    def log(self, phase: int, msg: str):
        if self.verbose:
            print(f"  [Phase {phase}] {msg}")

    def run(self, script_text: str) -> dict:
        """同步执行完整流水线"""
        print("=" * 60)
        print("  AI 短剧生成流水线")
        print("=" * 60)

        # Phase 0: 预处理
        cleaned = preprocess(script_text)
        self.log(0, f"预处理完成: {cleaned['char_count']} 字符, {cleaned['line_count']} 行, "
                     f"预估 {cleaned['estimated_minutes']} 分钟")

        # Phase 1: 角色提取
        self.log(1, "正在提取角色...")
        char_raw = self.llm.chat(SYS_CHARACTER,
            f"请分析以下剧本，提取所有角色：\n\n{cleaned['cleaned_text']}",
            temperature=0.2)
        characters = parse_character(char_raw)
        self.log(1, f"角色提取完成: {characters['total']} 个角色")

        # Phase 2: 场景提取
        self.log(2, "正在提取场景...")
        scene_raw = self.llm.chat(SYS_SCENE,
            f"请分析以下剧本，提取所有场景：\n\n{cleaned['cleaned_text']}",
            temperature=0.2)
        scenes = parse_scene(scene_raw)
        self.log(2, f"场景提取完成: {scenes['total']} 个场景")

        # Phase 3: 道具提取
        self.log(3, "正在提取道具...")
        props_raw = self.llm.chat(SYS_PROPS,
            f"请分析以下剧本，提取所有道具：\n\n{cleaned['cleaned_text']}",
            temperature=0.2)
        props = parse_props(props_raw)
        self.log(3, f"道具提取完成: {props['total']} 个道具")

        # Phase 4: 分镜规划 ⭐
        self.log(4, "正在规划分镜...")
        merged = json.dumps({
            "角色列表": characters,
            "场景列表": scenes,
            "道具列表": props,
        }, ensure_ascii=False, indent=2)

        board_raw = self.llm.chat(SYS_STORYBOARD,
            f"剧本：\n{cleaned['cleaned_text']}\n\n已提取的结构信息：\n{merged}\n\n请生成分镜表。",
            temperature=0.4, max_tokens=8192)
        storyboard = parse_storyboard(board_raw)
        shot_count = len(storyboard.get("storyboard", []))
        duration = storyboard.get("project", {}).get("estimated_duration", "?")
        self.log(4, f"分镜规划完成: {shot_count} 个分镜, 预估时长 {duration}")

        # Phase 5: 图片 Prompt
        self.log(5, "正在生成图片Prompt...")
        img_raw = self.llm.chat(SYS_IMAGE,
            f"请为以下分镜生成图片Prompt：\n{json.dumps(storyboard, ensure_ascii=False, indent=2)}",
            temperature=0.4)
        image_prompts = parse_image_prompts(img_raw)
        self.log(5, f"图片Prompt生成完成: {len(image_prompts.get('prompts', []))} 条")

        # Phase 6: 视频 Prompt
        self.log(6, "正在生成视频Prompt...")
        vid_raw = self.llm.chat(SYS_VIDEO,
            f"请为以下分镜生成视频Prompt：\n{json.dumps(storyboard, ensure_ascii=False, indent=2)}",
            temperature=0.4)
        video_prompts = parse_video_prompts(vid_raw)
        self.log(6, f"视频Prompt生成完成: {len(video_prompts.get('video_prompts', []))} 条")

        # Phase 7: 质量审核
        self.log(7, "正在进行质量审核...")
        qc_raw = self.llm.chat(SYS_QC,
            f"分镜方案：\n{json.dumps(storyboard, ensure_ascii=False, indent=2)}\n\n"
            f"图片Prompt：\n{json.dumps(image_prompts, ensure_ascii=False, indent=2)}\n\n"
            f"视频Prompt：\n{json.dumps(video_prompts, ensure_ascii=False, indent=2)}",
            temperature=0.2)
        quality = parse_qc_report(qc_raw)
        overall = quality.get("overall_score", "?")
        verdict = quality.get("verdict", "?")
        self.log(7, f"质量审核完成: {overall}/5 ({verdict})")

        # 组装结果
        result = {
            "metadata": {
                "pipeline": "AI Short Drama Pipeline v1.0",
                "model": self.llm.model,
                "char_count": cleaned["char_count"],
                "estimated_minutes": cleaned["estimated_minutes"],
            },
            "characters": characters,
            "scenes": scenes,
            "props": props,
            "storyboard": storyboard,
            "image_prompts": image_prompts,
            "video_prompts": video_prompts,
            "quality_report": quality,
        }
        return result


# ============================================================
# CLI
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI短剧生成流水线")
    parser.add_argument("--script", type=str, help="剧本文件路径")
    parser.add_argument("--model", type=str, default="deepseek",
                        choices=["deepseek", "doubao"], help="LLM提供商")
    parser.add_argument("--api-key", type=str, help="API Key")
    parser.add_argument("--output", type=str, default="output/short_drama_result.json",
                        help="输出JSON路径")
    args = parser.parse_args()

    # 读取剧本
    if args.script:
        script_text = Path(args.script).read_text(encoding="utf-8")
    else:
        # 内置测试剧本
        script_text = """【第一场】李总办公室 - 下午

[张三冲进办公室，气喘吁吁]
张三：李总，不好了！服务器宕机了！
李总（猛地站起来）：什么？！小王呢？叫他立刻去机房！
[角落里的小王摘下耳机]
小王：我一直在说这事，你们没人听啊。
李总（转头瞪着小王）：那你还坐着干嘛？快去修！
小王：已经在跑了...（看表）三分钟后恢复。
张三（松了一口气，瘫坐在椅子上）：吓死我了，还以为要背锅了。
李总（坐下，整理领带）：下次提前预警。散会。

【第二场】机房 - 傍晚

[小王独自坐在服务器前，屏幕的蓝光映在他脸上]
小王（自言自语）：每次都是我来救火，涨薪的时候怎么没人想起我？
[手机震动，是猎头发来的消息]
小王（盯着屏幕犹豫了三秒）：...先回复看看。
[手指在屏幕上打出一行字：我考虑一下。发送。]
[服务器绿灯亮起，他站起身，嘴角微扬，走出了机房]"""
        print("[使用内置测试剧本]")

    # 运行
    pipeline = ShortDramaPipeline(provider=args.model, api_key=args.api_key)
    result = pipeline.run(script_text)

    # 保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 摘要
    print()
    print("=" * 60)
    storyboard = result.get("storyboard", {})
    project = storyboard.get("project", {})
    print(f"  [Title] {project.get('title', 'N/A')}")
    print(f"  [Duration] {project.get('estimated_duration', 'N/A')}")
    print(f"  [Shots] {len(storyboard.get('storyboard', []))}")
    print(f"  [Characters] {result['characters']['total']}")
    print(f"  [Scenes] {result['scenes']['total']}")
    print(f"  [Props] {result['props']['total']}")
    qc = result.get("quality_report", {})
    print(f"  [Quality] {qc.get('overall_score', 'N/A')}/5 ({qc.get('verdict', 'N/A')})")
    print(f"  [Output] {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
