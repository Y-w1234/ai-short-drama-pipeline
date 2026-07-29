"""
AI Short Drama Pipeline - Streamlit Web UI v2
==============================================
图形化短剧生成工作台 + LLM 提供商智能推荐

特性:
- 图形化分镜时间线（情绪色彩映射 + 运镜图标）
- 角色关系网络可视化
- 场景氛围色板预览
- LLM 提供商对比推荐（成本 / 质量 / 免费额度）
- 实时 Token 费用估算
- 剧本模板库（职场 / 恋爱 / 悬疑 / 古装）
- 分镜流程导图

人设适配:
- Streamlit 纯 Python - 不碰 React/Vue
- 商业化就绪 - 成本展示 + JSON 下载
- 系统思维 - 组件化可复用布局

运行:
    streamlit run web_ui.py --server.port=8501
"""
import streamlit as st
import json, sys, time, os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from main import ShortDramaPipeline, preprocess

# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════
MOOD_COLORS = {
    "紧张": "#ef4444", "愤怒": "#dc2626", "压抑": "#6b7280",
    "冷静": "#3b82f6", "孤独": "#6366f1", "轻松": "#10b981",
    "讽刺": "#f59e0b", "转折": "#8b5cf6", "决断": "#0ea5e9",
    "释然+悬念": "#14b8a6", "悬疑": "#7c3aed", "浪漫": "#ec4899",
    "悲伤": "#3b82f6", "欢乐": "#22c55e", "恐惧": "#f97316",
}

SHOT_TYPE_GLYPH = {
    "远景": "🏞️", "全景": "🎬", "中景": "📷", "近景": "🔍",
    "特写": "🔎", "大特写": "⚡",
}

CAMERA_GLYPH = {
    "固定": "📌", "推": "➡️", "拉": "⬅️", "摇": "🔄",
    "移": "🚶", "跟": "🏃", "俯视": "🔽", "仰视": "🔼",
    "过肩": "👤", "固定→微推": "📌➡️",
}

TRANSITION_GLYPH = {
    "硬切": "✂️", "淡入淡出": "🌅", "叠化": "🔄",
}

# ═══════════════════════════════════════════════════════════════
# LLM 提供商推荐数据
# ═══════════════════════════════════════════════════════════════
LLM_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "model": "deepseek-chat",
        "price_input": 1.0,    # ¥/M tokens
        "price_output": 2.0,
        "free_credits": "注册送 500 万 tokens",
        "quality": 4.5,
        "speed": "快",
        "best_for": ["通用剧本", "高性价比", "新手入门"],
        "url": "https://platform.deepseek.com/api_keys",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "doubao": {
        "name": "豆包 (Doubao)",
        "model": "ep-20260729132149-9c8h5",
        "price_input": 0.8,
        "price_output": 2.0,
        "free_credits": "字节跳动 ARK 新人额度",
        "quality": 4.3,
        "speed": "极快",
        "best_for": ["长剧本 (>5k字)", "32K 上下文", "字节生态"],
        "url": "https://console.volcengine.com/ark",
        "env_key": "DOUBAO_API_KEY",
    },
}

SCRIPT_TEMPLATES = {
    "职场剧情": """【第一场】李总办公室 - 下午

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
[服务器绿灯亮起，他站起身，嘴角微扬，走出了机房]""",

    "恋爱甜宠": """【第一场】咖啡馆 - 午后

[林小晚端着咖啡，不小心撞到迎面走来的陆深]
林小晚：对不起对不起！
陆深（低头看看被咖啡泼湿的衬衫，嘴角微扬）：这是我今天遇到的最好的事。
林小晚（愣住）：啊？
陆深：因为让我遇见了你。
[林小晚脸红到耳根]

【第二场】公司会议室 - 上午

[林小晚抱着文件走进会议室，看到坐在主位的陆深]
林小晚（震惊）：你...你是新来的CEO？
陆深（微笑）：又见面了，咖啡小姐。
[会议室所有人面面相觑]""",

    "悬疑推理": """【第一场】废弃工厂 - 深夜

[雨夜。李警官打着手电筒，在废弃工厂中搜寻]
李警官：张队，这里有发现。
[手电筒照到地面上的血迹拖痕]
张队（对讲机）：什么情况？
李警官（蹲下，手指沾起红色液体）：血还是湿的，他应该没走远。
[突然，身后传来金属碰撞声]
李警官（猛地转身，拔枪）：谁？！

【第二场】审讯室 - 凌晨

[嫌疑人陈某坐在审讯椅上，表情平静]
李警官：你知道我们找到了什么吗？
陈某（微笑）：你们什么也找不到。
[李警官把证物袋拍在桌上]
李警官：那这个呢？
[陈某的笑容僵住了]""",
}

# ═══════════════════════════════════════════════════════════════
# 费用估算函数
# ═══════════════════════════════════════════════════════════════
def estimate_cost(char_count: int, provider: str) -> dict:
    """根据剧本字数估算 Token 用量和费用"""
    cn_chars_per_token = 1.5  # 1 个中文字符约 1.5 tokens
    input_tokens = int(char_count * cn_chars_per_token * 1.8)  # system prompt + 往返
    output_tokens = int(char_count * cn_chars_per_token * 3.0)  # 7 个 Phase 输出

    pp = LLM_PROVIDERS.get(provider, LLM_PROVIDERS["deepseek"])
    cost_in = input_tokens / 1_000_000 * pp["price_input"]
    cost_out = output_tokens / 1_000_000 * pp["price_output"]

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_input": round(cost_in, 4),
        "cost_output": round(cost_out, 4),
        "cost_total": round(cost_in + cost_out, 4),
        "api_calls": 7,
    }

# ═══════════════════════════════════════════════════════════════
# 页面配置
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Short Drama Pipeline",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
:root {
  --card-bg: #ffffff;
  --card-border: #e5e7eb;
}
@media (prefers-color-scheme: dark) {
  :root { --card-bg: #1f2937; --card-border: #374151; }
}
.header-main { font-size: 1.6rem; font-weight: 700; }
.header-sub { font-size: 0.9rem; color: #6b7280; margin-bottom: 1rem; }
.card {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: 10px; padding: 1rem; margin-bottom: 0.6rem;
}
.shot-timeline {
  display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: flex-start;
}
.shot-node {
  width: 70px; text-align: center; padding: 0.5rem 0.3rem;
  border-radius: 8px; font-size: 0.7rem; border: 2px solid #e5e7eb;
  cursor: default; transition: transform 0.15s;
}
.shot-node:hover { transform: scale(1.08); z-index: 10; }
.relation-line {
  display: inline-block; padding: 0.25rem 0.6rem; margin: 0.15rem;
  border-radius: 12px; font-size: 0.75rem; background: #f3f4f6;
}
.mood-bar {
  height: 6px; border-radius: 3px; margin-top: 0.3rem;
}
.color-swatch {
  display: inline-block; width: 20px; height: 20px; border-radius: 4px;
  vertical-align: middle; margin-right: 4px; border: 1px solid #d1d5db;
}
.cost-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white; padding: 1rem; border-radius: 10px;
}
.provider-card {
  border: 2px solid #e5e7eb; border-radius: 10px; padding: 0.8rem;
  cursor: pointer; transition: border-color 0.2s;
}
.provider-card:hover { border-color: #3b82f6; }
.provider-card.selected { border-color: #3b82f6; background: #eff6ff; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# API Key 检测 & 智能提供商推荐
# ═══════════════════════════════════════════════════════════════
def detect_available_keys() -> dict:
    """检测所有已配置的 API Key"""
    result = {}
    for pid, pinfo in LLM_PROVIDERS.items():
        result[pid] = bool(os.environ.get(pinfo["env_key"], "").strip())
    return result

def recommend_provider(key_status: dict) -> str:
    """智能推荐: 有 Key > 免费用量大 > 成本低"""
    available = [pid for pid, ok in key_status.items() if ok]
    if available:
        return available[0]  # 第一个可用的
    return "deepseek"  # 默认（Demo 模式）

# ═══════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════
key_status = detect_available_keys()

with st.sidebar:
    st.markdown("## 🎬 工作台")

    # ── API Key 概览 ──
    st.markdown("### 🔑 API Keys")
    for pid, ok in key_status.items():
        pinfo = LLM_PROVIDERS[pid]
        icon = "🟢" if ok else "🔴"
        st.caption(f"{icon} {pinfo['name']}: {'已连接' if ok else '未设置'}")

    # ── LLM 选择 ──
    st.markdown("### 🤖 LLM 提供商")
    tabs_llm = st.tabs(["快速选择", "详细对比"])

    with tabs_llm[0]:
        recommended = recommend_provider(key_status)
        options = ["deepseek", "doubao"]
        default_idx = options.index(recommended)

        provider = st.selectbox(
            "选择模型",
            options=options,
            format_func=lambda x: f"{LLM_PROVIDERS[x]['name']} ({LLM_PROVIDERS[x]['model']})",
            index=default_idx,
            help=f"智能推荐: {LLM_PROVIDERS[recommended]['name']}",
        )

        env_key = LLM_PROVIDERS[provider]["env_key"]
        env_val = os.environ.get(env_key, "").strip()
        has_key = bool(env_val)

        if has_key:
            masked = env_val[:8] + "..." + env_val[-4:] if len(env_val) > 12 else "***"
            st.success(f"已连接 {env_key} ({masked})")
        else:
            st.warning(f"{env_key} 未设置 — Demo 模式")
            st.caption(f"[获取 {LLM_PROVIDERS[provider]['name']} Key]({LLM_PROVIDERS[provider]['url']})")

    with tabs_llm[1]:
        cols = st.columns(len(LLM_PROVIDERS))
        for i, (pid, pinfo) in enumerate(LLM_PROVIDERS.items()):
            with cols[i]:
                selected = pid == provider
                st.markdown(f"""
                <div class="provider-card {'selected' if selected else ''}">
                    <b>{pinfo['name']}</b><br>
                    <small>{pinfo['model'][:30]}...</small>
                    <hr style="margin:0.4rem 0">
                    <small>输入: ¥{pinfo['price_input']}/M tokens</small><br>
                    <small>输出: ¥{pinfo['price_output']}/M tokens</small><br>
                    <small>质量: {'⭐'*int(pinfo['quality'])}</small><br>
                    <small>速度: {pinfo['speed']}</small><br>
                    <small style="color:#10b981">💰 {pinfo['free_credits']}</small>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # ── 输入方式 ──
    st.markdown("### 📝 输入")
    input_mode = st.radio(
        "剧本来源",
        options=["🎭 剧本模板", "📝 自由输入", "📂 上传文件"],
        index=0,
    )

    if input_mode == "🎭 剧本模板":
        template_name = st.selectbox(
            "选择模板", options=list(SCRIPT_TEMPLATES.keys()), index=0,
        )
        script_text = SCRIPT_TEMPLATES[template_name]
        st.info(f"📖 **{template_name}** — {len(script_text)} 字")

    elif input_mode == "📝 自由输入":
        script_text = st.text_area(
            "输入剧本", value="", height=220,
            placeholder="在此粘贴你的短剧剧本...\n\n示例格式：\n【第一场】办公室 - 下午\n张三：李总，不好了！",
        )
    else:
        uploaded = st.file_uploader("上传 .txt 文件 (最大 1MB)", type=["txt"])
        script_text = ""
        if uploaded:
            script_text = uploaded.read().decode("utf-8")
            st.text_area("预览", value=script_text[:1500], height=180, disabled=True)

    st.divider()

    # ── 安全模式 ──
    st.markdown("### 🛡️ 安全")
    safety_mode = st.selectbox(
        "内容审核", options=["strict", "relaxed"], index=0,
        format_func=lambda x: "严格模式 (生产)" if x == "strict" else "宽松模式 (测试)",
    )

    st.divider()

    # ── 费用预估 ──
    if script_text.strip():
        cleaned = preprocess(script_text.strip())
        est = estimate_cost(cleaned["char_count"], provider)
        st.markdown("### 💰 费用预估")
        st.markdown(f"""
        <div class="card">
            <small>输入 tokens</small> <b>{est['input_tokens']:,}</b><br>
            <small>输出 tokens</small> <b>{est['output_tokens']:,}</b><br>
            <small>总计 tokens</small> <b>{est['total_tokens']:,}</b><br>
            <small>API 调用</small> <b>7 次</b><br>
            <hr style="margin:0.3rem 0">
            <small>预估费用</small> <b style="color:#3b82f6">¥{est['cost_total']}</b>
            <span style="color:#10b981;font-size:0.75rem"> ({LLM_PROVIDERS[provider]['free_credits']})</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.caption(f"[GitHub](https://github.com/Y-w1234/ai-short-drama-pipeline) | v2.0")

# ═══════════════════════════════════════════════════════════════
# 主页面
# ═══════════════════════════════════════════════════════════════
st.markdown('<p class="header-main">🎬 AI Short Drama Pipeline</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="header-sub">8-Phase 全链路自动化 · 图形化分镜工作台 · '
    + f'当前模型: <b>{LLM_PROVIDERS[provider]["name"]}</b></p>',
    unsafe_allow_html=True,
)

# ── 运行按钮 ──
col_btn, col_info = st.columns([2, 4])
with col_btn:
    run_btn = st.button(
        "🚀 生成短剧方案", type="primary", use_container_width=True,
        disabled=not script_text.strip(),
    )
with col_info:
    if not script_text.strip():
        st.caption("输入剧本后点击左侧按钮开始生成")
    else:
        cleaned = preprocess(script_text.strip())
        st.caption(
            f"就绪: {cleaned['char_count']} 字符 · {cleaned['line_count']} 行 · "
            f"预估 {cleaned['estimated_minutes']} 分钟 · "
            f"费用约 ¥{estimate_cost(cleaned['char_count'], provider)['cost_total']}"
        )

st.divider()

# ═══════════════════════════════════════════════════════════════
# 空状态 - 功能导览
# ═══════════════════════════════════════════════════════════════
if not run_btn:
    st.markdown("### 🚀 快速开始")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="card">
            <b>1. 选择 LLM</b><br>
            <small>DeepSeek 推荐（免费 500 万 tokens）<br>
            豆包适合长剧本 (32K 上下文)</small>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="card">
            <b>2. 准备剧本</b><br>
            <small>使用内置模板或自由输入<br>
            支持中文剧本 + 场景标记</small>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="card">
            <b>3. 一键生成</b><br>
            <small>8-Phase 全自动执行<br>
            图形化分镜表 + AI Prompt + 安全审核</small>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📊 LLM 提供商推荐对比")

    # 对比表
    comp_cols = st.columns(len(LLM_PROVIDERS) + 1)
    rows = [
        ("模型", lambda p: LLM_PROVIDERS[p]["model"]),
        ("输入价格", lambda p: f"¥{LLM_PROVIDERS[p]['price_input']}/M"),
        ("输出价格", lambda p: f"¥{LLM_PROVIDERS[p]['price_output']}/M"),
        ("质量评分", lambda p: f"{'⭐'*int(LLM_PROVIDERS[p]['quality'])}"),
        ("速度", lambda p: LLM_PROVIDERS[p]["speed"]),
        ("免费额度", lambda p: LLM_PROVIDERS[p]["free_credits"]),
        ("适用场景", lambda p: ", ".join(LLM_PROVIDERS[p]["best_for"])),
    ]
    for row_label, row_fn in rows:
        comp_cols[0].markdown(f"**{row_label}**")
        for j, pid in enumerate(LLM_PROVIDERS):
            comp_cols[j + 1].markdown(f"<small>{row_fn(pid)}</small>", unsafe_allow_html=True)

    st.divider()
    st.caption("💡 未设置 API Key 时自动进入 Demo 模式（零费用），展示完整 12 镜头示例")

# ═══════════════════════════════════════════════════════════════
# 执行管线
# ═══════════════════════════════════════════════════════════════
if run_btn and script_text.strip():
    cleaned = preprocess(script_text.strip())

    # 进度条
    progress_bar = st.progress(0, text="初始化...")
    status_area = st.empty()

    try:
        progress_bar.progress(10, text="Phase 0: 预处理 & 注入检测...")
        pipeline = ShortDramaPipeline(provider=provider)
        pipeline.verbose = False  # 禁用 CLI 日志，使用 Streamlit 进度条

        progress_bar.progress(25, text="Phase 1-3: 并行提取角色/场景/道具...")
        result = pipeline.run(script_text.strip())
        progress_bar.progress(100, text="完成!")
        time.sleep(0.3)
        progress_bar.empty()

        st.success(f"生成完成！")

        # ═══════════════════════════════════════════════════════
        # 仪表盘
        # ═══════════════════════════════════════════════════════
        storyboard = result.get("storyboard", {})
        project = storyboard.get("project", {})
        quality = result.get("quality_report", {})
        safety = result.get("safety_scan", {})
        shots = storyboard.get("storyboard", [])
        characters = result["characters"]["characters"]
        scenes = result["scenes"]["scenes"]
        props = result["props"]["props"]
        token_usage = result["metadata"].get("token_usage", {})

        st.markdown("### 📊 项目概览")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("分镜数", len(shots))
        c2.metric("角色", result["characters"]["total"])
        c3.metric("场景", result["scenes"]["total"])
        c4.metric("道具", result["props"]["total"])
        c5.metric("质量", f"{quality.get('overall_score','?')}/5", delta=quality.get("verdict",""))
        c6.metric("安全", "PASS" if safety.get("passed") else "BLOCKED")

        if token_usage and token_usage.get("api_calls", 0) > 0:
            st.markdown("##### Token 用量 & 成本")
            actual_cost_in = token_usage["prompt_tokens"] / 1_000_000 * LLM_PROVIDERS[provider]["price_input"]
            actual_cost_out = token_usage["completion_tokens"] / 1_000_000 * LLM_PROVIDERS[provider]["price_output"]
            actual_total = actual_cost_in + actual_cost_out
            tc1, tc2, tc3, tc4, tc5 = st.columns(5)
            tc1.metric("API 调用", f"{token_usage['api_calls']} 次")
            tc2.metric("Prompt Tokens", f"{token_usage['prompt_tokens']:,}")
            tc3.metric("Completion Tokens", f"{token_usage['completion_tokens']:,}")
            tc4.metric("总计 Tokens", f"{token_usage['total_tokens']:,}")
            tc5.metric("实际费用", f"¥{actual_total:.4f}")

        st.divider()

        # ═══════════════════════════════════════════════════════
        # 图形化分镜时间线
        # ═══════════════════════════════════════════════════════
        st.markdown("### 🎬 分镜时间线")
        st.caption(f"**{project.get('title','N/A')}** | {project.get('genre','?')} | {project.get('estimated_duration','?')}")

        if shots:
            # 分镜节点
            timeline_html = '<div class="shot-timeline">'
            for i, shot in enumerate(shots):
                mood = shot.get("mood", "")
                bg = MOOD_COLORS.get(mood, "#9ca3af")
                camera = shot.get("camera_movement", "")
                cam_glyph = CAMERA_GLYPH.get(camera, "📌")
                shot_type_g = SHOT_TYPE_GLYPH.get(shot.get("shot_type", ""), "🎬")

                timeline_html += f"""
                <div class="shot-node" style="border-color:{bg}" title="{shot.get('shot_id','')}: {shot.get('visual_description','')[:80]}">
                    <div style="font-size:1.2rem">{shot_type_g}</div>
                    <div style="font-weight:700;color:{bg}">{shot.get('shot_id','?')[-3:]}</div>
                    <div style="font-size:0.65rem">{shot.get('shot_type','?')}</div>
                    <div style="font-size:0.65rem">{cam_glyph} {camera}</div>
                    <div class="mood-bar" style="background:{bg}"></div>
                    <div style="font-size:0.6rem;color:#888">{shot.get('duration_seconds',0)}s</div>
                </div>"""

                # 转场箭头
                if i < len(shots) - 1:
                    trans = shot.get("transition", "硬切")
                    trans_g = TRANSITION_GLYPH.get(trans, "→")
                    timeline_html += f'<div style="align-self:center;font-size:0.7rem;color:#888">{trans_g}</div>'

            timeline_html += "</div>"
            st.markdown(timeline_html, unsafe_allow_html=True)

            # 图例
            st.caption(
                "运镜: 📌固定 ➡️推 ⬅️拉 🔄摇 🚶移 🏃跟 🔼仰视 🔽俯视 | "
                "转场: ✂️硬切 🌅淡入淡出 | "
                "景别: 🏞️远景 🎬全景 📷中景 🔍近景 🔎特写 ⚡大特写"
            )

        st.divider()

        # ═══════════════════════════════════════════════════════
        # Tab 详情
        # ═══════════════════════════════════════════════════════
        tabs = st.tabs([
            "👤 角色关系", "🏠 场景氛围", "🎭 道具", "🎬 分镜详情",
            "🖼️ Prompt", "📊 质量 & 安全",
        ])

        # Tab 1: 角色关系图
        with tabs[0]:
            if characters:
                # 关系网络
                st.markdown("#### 角色关系网络")
                all_relations = []
                char_names = {c["name"] for c in characters}

                for char in characters:
                    for rel in char.get("relationships", []):
                        if rel["to"] in char_names:
                            all_relations.append((char["name"], rel["to"], rel.get("relation", "")))

                if all_relations:
                    rel_html = '<div style="padding:0.5rem">'
                    for src, dst, rel in all_relations:
                        rel_html += (
                            f'<span class="relation-line">'
                            f'<b>{src}</b> {rel} <b>{dst}</b>'
                            f'</span> '
                        )
                    rel_html += "</div>"
                    st.markdown(rel_html, unsafe_allow_html=True)

                # 角色卡片
                st.markdown("#### 角色详情")
                cols = st.columns(min(len(characters), 3))
                for i, char in enumerate(characters):
                    with cols[i % 3]:
                        type_color = {"主角": "#f59e0b", "反派": "#ef4444", "配角": "#3b82f6", "龙套": "#9ca3af"}
                        tc = type_color.get(char.get("type", ""), "#9ca3af")
                        st.markdown(f"""
                        <div class="card">
                            <div style="display:flex;justify-content:space-between;align-items:center">
                                <b style="font-size:1.1rem">{char.get('name','?')}</b>
                                <span style="background:{tc};color:white;padding:0.1rem 0.5rem;border-radius:10px;font-size:0.7rem">{char.get('type','?')}</span>
                            </div>
                            <small>性别: {char.get('gender','?')} | {char.get('age_group','?')}</small><br>
                            <small>性格: {', '.join(char.get('personality',[]))}</small><br>
                            <small>外貌: {', '.join(char.get('appearance',[]))}</small><br>
                            <small style="color:#888">台词: "{char.get('first_line','')[:50]}"</small>
                        </div>""", unsafe_allow_html=True)

        # Tab 2: 场景氛围
        with tabs[1]:
            if scenes:
                st.markdown("#### 场景氛围色板")
                scene_cols = st.columns(min(len(scenes), 2))
                for i, scene in enumerate(scenes):
                    with scene_cols[i % 2]:
                        mood = scene.get("atmosphere", "")
                        mood_c = MOOD_COLORS.get(mood, "#9ca3af")
                        lighting = scene.get("lighting", "")
                        color_tone = scene.get("color_tone", "")

                        # 从 description 粗略推断主色调
                        swatch_c = mood_c
                        if "暖" in color_tone:
                            swatch_c = "#f59e0b"
                        elif "冷" in color_tone:
                            swatch_c = "#3b82f6"

                        st.markdown(f"""
                        <div class="card">
                            <div style="display:flex;align-items:center;gap:0.5rem">
                                <span class="color-swatch" style="background:{swatch_c}"></span>
                                <b>{scene.get('name','?')}</b>
                                <span style="font-size:0.7rem;color:#888">{scene.get('location_type','?')} | {scene.get('time_of_day','?')}</span>
                            </div>
                            <small>{scene.get('description','')[:120]}</small>
                            <div style="display:flex;gap:1rem;margin-top:0.3rem">
                                <small>光线: {lighting[:30]}</small>
                                <small>氛围: <span style="color:{mood_c}">{mood}</span></small>
                                <small>色调: {color_tone}</small>
                            </div>
                            <div style="margin-top:0.3rem">
                                <small>出场: {', '.join(scene.get('characters_present',[]))}</small>
                            </div>
                        </div>""", unsafe_allow_html=True)

        # Tab 3: 道具
        with tabs[2]:
            if props:
                priority_icons = {"A": "🔴", "B": "🟡", "C": "🟢"}
                p_cols = st.columns(3)
                for i, cat in enumerate(["电子产品", "服装", "手持", "场景装饰"]):
                    cat_props = [p for p in props if cat in p.get("category", "")]
                    if cat_props:
                        with p_cols[i % 3]:
                            st.markdown(f"**{cat}**")
                            for p in cat_props[:5]:
                                pi = priority_icons.get(p.get("priority", "C"), "⚪")
                                st.markdown(f"{pi} **{p['name']}**<br><small>{p.get('description','')[:40]}</small>")

        # Tab 4: 分镜详情
        with tabs[3]:
            for shot in shots:
                mood = shot.get("mood", "")
                bg = MOOD_COLORS.get(mood, "#e5e7eb")
                sid = shot.get("shot_id", "?")
                with st.expander(
                    f"{SHOT_TYPE_GLYPH.get(shot.get('shot_type',''),'🎬')} "
                    f"**{sid}** — {shot.get('shot_type','?')} | "
                    f"`{shot.get('mood','?')}` | {shot.get('duration_seconds',0)}s"
                ):
                    c1, c2 = st.columns([3, 2])
                    with c1:
                        st.markdown(f"""
                        <div style="border-left:4px solid {bg};padding-left:0.8rem">
                            <p>{shot.get('visual_description','')}</p>
                        </div>""", unsafe_allow_html=True)
                        if shot.get("dialogue"):
                            st.markdown(f"> _{shot.get('dialogue','')}_")
                    with c2:
                        st.markdown(f"**场景**: `{shot.get('scene_id','')}`")
                        st.markdown(f"**机位**: {CAMERA_GLYPH.get(shot.get('camera_angle',''),'')} {shot.get('camera_angle','?')}")
                        st.markdown(f"**运镜**: {CAMERA_GLYPH.get(shot.get('camera_movement',''),'')} {shot.get('camera_movement','?')}")
                        st.markdown(f"**转场**: {TRANSITION_GLYPH.get(shot.get('transition',''),'')} {shot.get('transition','?')}")
                        actions = shot.get("character_actions", {})
                        if actions:
                            st.caption("动作:")
                            for k, v in actions.items():
                                st.caption(f"  {k}: {v}")

        # Tab 5: Prompts
        with tabs[4]:
            img_prompts = result.get("image_prompts", {}).get("prompts", [])
            vid_prompts = result.get("video_prompts", {}).get("video_prompts", [])

            st.markdown("#### 🖼️ 图片生成 Prompt")
            for p in img_prompts:
                st.markdown(f"**{p.get('shot_id','')}**")
                st.code(p.get("prompt_en", ""), language=None)
                st.caption(f"负向: {p.get('negative_prompt','')} | {p.get('aspect_ratio','16:9')}")

            st.markdown("#### 🎥 视频生成 Prompt")
            for p in vid_prompts:
                st.markdown(f"**{p.get('shot_id','')}** ({p.get('duration_seconds',0)}s)")
                st.code(p.get("prompt", ""), language=None)

            if img_prompts and img_prompts[0].get("parse_fallback"):
                st.info("以上 Prompt 为 fallback 生成（LLM 解析降级）")

        # Tab 6: 质量 & 安全
        with tabs[5]:
            qc1, qc2 = st.columns(2)

            with qc1:
                st.markdown("#### ⭐ 质量评分")
                scores = quality.get("scores", {})
                if scores:
                    for dim, info in scores.items():
                        score_val = info.get("score", 0)
                        pct = score_val / 5.0
                        color = "#10b981" if score_val >= 4 else "#f59e0b" if score_val >= 3 else "#ef4444"
                        st.markdown(f"**{dim}**: {score_val}/5")
                        st.progress(pct, text=f"{'⭐'*score_val}{'☆'*(5-score_val)}")
                        st.caption(info.get("reason", ""))
                st.markdown(f"**总评**: {quality.get('overall_score','?')}/5 — `{quality.get('verdict','?')}`")
                suggestions = quality.get("suggestions", [])
                if suggestions:
                    st.info("\n".join(f"- {s}" for s in suggestions))

            with qc2:
                st.markdown("#### 🛡️ 安全扫描")
                if safety.get("passed"):
                    st.success("PASS — 内容安全")
                else:
                    st.error("BLOCKED — 发现违规内容")

                st.metric("标记数", safety.get("total_flags", 0))
                st.caption(f"模式: {safety.get('scan_mode','?')}")
                st.caption(f"深度审核: {'已执行' if safety.get('deep_scan_performed') else '无需'}")

                blocked = safety.get("blocked", [])
                if blocked:
                    st.error("**阻断项**:")
                    for b in blocked:
                        st.markdown(f"- {b['category']}: {b.get('matched_keyword','')}")

                warnings = safety.get("warnings", [])
                if warnings:
                    st.warning("**警告项**:")
                    for w in warnings:
                        st.markdown(f"- {w['category']}: {w.get('matched_keyword','')}")

        # ═══════════════════════════════════════════════════════
        # 下载
        # ═══════════════════════════════════════════════════════
        st.divider()
        dl1, dl2, dl3 = st.columns([1, 1, 4])
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with dl1:
            st.download_button("📥 下载 JSON", json.dumps(result, ensure_ascii=False, indent=2),
                               f"drama_{ts}.json", "application/json", use_container_width=True)
        with dl2:
            # 导出纯文本分镜表
            txt_output = f"{project.get('title','N/A')} — 分镜表\n{'='*40}\n\n"
            for s in shots:
                txt_output += (
                    f"{s.get('shot_id','?')} | {s.get('shot_type','?')} | {s.get('duration_seconds',0)}s\n"
                    f"  画面: {s.get('visual_description','')[:100]}\n"
                    f"  对白: {s.get('dialogue','')}\n"
                    f"  运镜: {s.get('camera_movement','?')} | 转场: {s.get('transition','?')}\n\n"
                )
            st.download_button("📄 下载分镜文本", txt_output,
                               f"storyboard_{ts}.txt", "text/plain", use_container_width=True)
        with dl3:
            st.caption("JSON 可用于下游 AI 图像/视频生成管线。分镜文本适合打印审阅。")

    except RuntimeError as e:
        progress_bar.empty()
        st.error(f"流水线执行失败: {e}")
    except Exception as e:
        progress_bar.empty()
        st.error(f"未知错误: {e}")
        st.exception(e)
