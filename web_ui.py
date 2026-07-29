"""
AI Short Drama Pipeline — Streamlit Web UI
===========================================
纯 Python 前端，导入 main.py 的 ShortDramaPipeline，不修改后端代码。

人设适配:
- 用 Streamlit（Python 生态），不碰 React/Vue
- 商业化就绪：JSON 下载、Token 成本展示、安全扫描结果可视化
- 系统思维：组件化布局，可复用

运行:
    streamlit run web_ui.py
    streamlit run web_ui.py --server.port=7860 --server.address=0.0.0.0
"""
import streamlit as st
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# 导入后端（不修改 main.py）
sys.path.insert(0, str(Path(__file__).parent))
from main import ShortDramaPipeline, ContentSafetyScanner, LLMClient, preprocess

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="AI Short Drama Pipeline",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS 样式（暗色/亮色自适应）
# ============================================================
st.markdown("""
<style>
    .main-header { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }
    .metric-card { padding: 1rem; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center; }
    .metric-value { font-size: 1.5rem; font-weight: 700; }
    .metric-label { font-size: 0.8rem; color: #888; }
    .pass-badge { color: #10b981; font-weight: 700; }
    .fail-badge { color: #ef4444; font-weight: 700; }
    .warn-badge { color: #f59e0b; font-weight: 700; }
    .shot-card { padding: 0.8rem; border-left: 3px solid #3b82f6; margin-bottom: 0.5rem; border-radius: 4px; }
    .stExpander { border: 1px solid #e0e0e0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Sidebar 配置
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ 配置")

    provider = st.selectbox(
        "LLM 提供商",
        options=["deepseek", "doubao"],
        index=0,
        help="DeepSeek（推荐，注册送免费额度）/ 豆包（字节跳动 ARK）",
    )

    st.divider()

    st.markdown("### 📝 输入方式")
    input_mode = st.radio(
        "选择输入方式",
        options=["📝 直接输入剧本", "📂 上传剧本文件", "🎭 使用示例剧本"],
        index=2,
    )

    st.divider()

    st.markdown("### 🔒 安全模式")
    safety_mode = st.selectbox(
        "内容安全扫描",
        options=["strict（生产模式）", "relaxed（测试模式）"],
        index=0,
        help="strict: 阻断违规内容 / relaxed: 只标记不阻断",
    )

    st.divider()

    st.markdown("### 📊 关于")
    st.markdown("""
    **AI Short Drama Pipeline v1.2**

    8-Phase 全链路自动化:
    剧本 → 角色/场景/道具提取 → 分镜规划 → 图片/视频 Prompt → 质量审核 → 安全扫描

    [GitHub](https://github.com/Y-w1234/ai-short-drama-pipeline)
    """)

# ============================================================
# 预设示例剧本
# ============================================================
DEMO_SCRIPT = """【第一场】李总办公室 - 下午

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

# ============================================================
# 主页面
# ============================================================
st.markdown('<p class="main-header">🎬 AI Short Drama Pipeline</p>', unsafe_allow_html=True)
st.caption("8-Phase 全链路自动化短剧生成 —— 从剧本到分镜 + AI Prompt，零代码操作")

st.divider()

# ---- 输入区域 ----
if input_mode == "📝 直接输入剧本":
    script_text = st.text_area(
        "输入短剧剧本",
        value="",
        height=280,
        placeholder="在此粘贴你的短剧剧本...\n\n示例格式：\n【第一场】办公室 - 下午\n张三：李总，不好了！\n李总：什么？！",
        help="支持中文剧本，包含场景标记和角色对白",
    )
elif input_mode == "📂 上传剧本文件":
    uploaded = st.file_uploader(
        "上传剧本文件（.txt, 最大 1MB）",
        type=["txt"],
        help="上传 .txt 格式的剧本文件",
    )
    script_text = ""
    if uploaded:
        script_text = uploaded.read().decode("utf-8")
        st.text_area("文件内容预览", value=script_text[:2000], height=200, disabled=True)
else:
    script_text = DEMO_SCRIPT
    st.info("📖 使用内置示例剧本：**《服务器宕机了》** — 3 个角色 / 2 个场景 / 职场剧情")

# ---- 运行按钮 ----
col1, col2, col3 = st.columns([2, 1, 2])
with col1:
    run_btn = st.button(
        "🚀 生成短剧方案",
        type="primary",
        use_container_width=True,
        disabled=not script_text.strip(),
    )

# ---- 执行 ----
if run_btn and script_text.strip():
    # 预处理信息
    cleaned = preprocess(script_text.strip())
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("字符数", cleaned["char_count"])
    col_b.metric("行数", cleaned["line_count"])
    col_c.metric("预估时长", f"{cleaned['estimated_minutes']} 分钟")

    st.divider()

    with st.spinner("正在生成短剧方案（Phase 0-7.5）..."):
        start_time = time.time()
        try:
            pipeline = ShortDramaPipeline(provider=provider)
            result = pipeline.run(script_text.strip())
            elapsed = time.time() - start_time
            st.success(f"生成完成！耗时 {elapsed:.1f}s")

            # ============================================================
            # 结果展示
            # ============================================================
            st.divider()

            # ---- 概览仪表盘 ----
            st.markdown("### 📊 概览")
            storyboard = result.get("storyboard", {})
            project = storyboard.get("project", {})
            quality = result.get("quality_report", {})
            safety = result.get("safety_scan", {})

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("🎬 分镜数", len(storyboard.get("storyboard", [])))
            col2.metric("👤 角色", result["characters"]["total"])
            col3.metric("🏠 场景", result["scenes"]["total"])
            col4.metric("🎭 道具", result["props"]["total"])
            col5.metric(
                "⭐ 质量评分",
                f"{quality.get('overall_score', '?')}/5",
                delta=quality.get("verdict", ""),
            )
            safety_text = "✅ 通过" if safety.get("passed") else "🚫 未通过"
            col6.metric("🛡️ 安全扫描", safety_text)

            # Token 用量
            token_usage = result["metadata"].get("token_usage", {})
            if token_usage and token_usage.get("api_calls", 0) > 0:
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("API 调用次数", token_usage["api_calls"])
                col_b.metric("Prompt Tokens", f"{token_usage['prompt_tokens']:,}")
                col_c.metric("Completion Tokens", f"{token_usage['completion_tokens']:,}")
                col_d.metric("总计 Tokens", f"{token_usage['total_tokens']:,}")

            st.divider()

            # ---- Tab 详情 ----
            tabs = st.tabs([
                "📋 角色列表", "🏠 场景详情", "🎭 道具清单",
                "🎬 分镜表", "🖼️ 图片/视频 Prompt", "📊 质量 & 安全",
            ])

            # Tab 1: 角色
            with tabs[0]:
                characters = result["characters"]["characters"]
                if characters:
                    cols = st.columns(min(len(characters), 3))
                    for i, char in enumerate(characters):
                        with cols[i % 3]:
                            st.markdown(f"""
                            <div style="padding:1rem;border:1px solid #e0e0e0;border-radius:8px;margin-bottom:0.5rem">
                                <b>{char.get('name', '?')}</b>
                                <span style="color:#888;font-size:0.8rem"> | {char.get('type','?')}</span>
                                <br><small>性别: {char.get('gender','?')} | 年龄段: {char.get('age_group','?')}</small>
                                <br><small>性格: {', '.join(char.get('personality',[]))}</small>
                                <br><small>外貌: {', '.join(char.get('appearance',[]))}</small>
                                <br><small>首句台词: {char.get('first_line','')[:40]}...</small>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("未提取到角色信息")

            # Tab 2: 场景
            with tabs[1]:
                scenes = result["scenes"]["scenes"]
                if scenes:
                    for scene in scenes:
                        with st.expander(f"**{scene.get('name','?')}** — {scene.get('location_type','?')} | {scene.get('time_of_day','?')}"):
                            st.markdown(f"**描述**: {scene.get('description','')}")
                            c1, c2 = st.columns(2)
                            c1.markdown(f"**光线**: {scene.get('lighting','')}")
                            c1.markdown(f"**氛围**: {scene.get('atmosphere','')}")
                            c2.markdown(f"**色调**: {scene.get('color_tone','')}")
                            c2.markdown(f"**出场角色**: {', '.join(scene.get('characters_present',[]))}")
                            st.markdown(f"**关键道具**: {', '.join(scene.get('key_props',[]))}")
                else:
                    st.warning("未提取到场景信息")

            # Tab 3: 道具
            with tabs[2]:
                props = result["props"]["props"]
                if props:
                    for prop in props:
                        priority_icon = {"A": "🔴", "B": "🟡", "C": "🟢"}.get(prop.get("priority", "C"), "⚪")
                        st.markdown(
                            f"{priority_icon} **{prop.get('name','?')}** "
                            f"[{prop.get('category','?')}] "
                            f"→ {prop.get('description','')} "
                            f"（{'/'.join(prop.get('scenes',[]))} / {', '.join(prop.get('used_by',[]))}）"
                        )
                else:
                    st.warning("未提取到道具信息")

            # Tab 4: 分镜表
            with tabs[3]:
                shots = storyboard.get("storyboard", [])
                st.markdown(f"**{project.get('title','N/A')}** | {project.get('genre','?')} | {project.get('estimated_duration','?')}")
                st.divider()
                for shot in shots:
                    with st.expander(f"🎬 {shot.get('shot_id','?')} — {shot.get('shot_type','?')} | {shot.get('mood','?')} | {shot.get('duration_seconds', 0)}s"):
                        c1, c2 = st.columns([3, 2])
                        with c1:
                            st.markdown(f"**画面描述**: {shot.get('visual_description','')}")
                            if shot.get("dialogue"):
                                st.markdown(f"**对白**: _{shot.get('dialogue','')}_")
                        with c2:
                            st.markdown(f"**场景**: {shot.get('scene_id','')}")
                            st.markdown(f"**机位**: {shot.get('camera_angle','')} | {shot.get('camera_setup','')}")
                            st.markdown(f"**运镜**: {shot.get('camera_movement','')}")
                            st.markdown(f"**转场**: {shot.get('transition','')}")
                            actions = shot.get("character_actions", {})
                            if actions:
                                st.markdown(f"**动作**: {', '.join(f'{k}: {v}' for k,v in actions.items())}")

            # Tab 5: Prompts
            with tabs[4]:
                st.markdown("### 🖼️ 图片 Prompt")
                img_prompts = result["image_prompts"]["prompts"]
                for p in img_prompts[:5]:  # show first 5
                    st.markdown(f"**{p.get('shot_id','')}**")
                    st.code(p.get("prompt_en", ""), language=None)
                    st.caption(f"负向: {p.get('negative_prompt','')} | {p.get('aspect_ratio','16:9')}")

                if len(img_prompts) > 5:
                    st.info(f"... 共 {len(img_prompts)} 条图片 Prompt（前 5 条已展示）")

                st.markdown("### 🎥 视频 Prompt")
                vid_prompts = result["video_prompts"]["video_prompts"]
                for p in vid_prompts[:5]:
                    st.markdown(f"**{p.get('shot_id','')}** ({p.get('duration_seconds',0)}s)")
                    st.code(p.get("prompt", ""), language=None)
                    st.caption(f"运镜: {p.get('motion_description','')} | 运动: {p.get('camera_motion','')}")

                if len(vid_prompts) > 5:
                    st.info(f"... 共 {len(vid_prompts)} 条视频 Prompt（前 5 条已展示）")

            # Tab 6: 质量 & 安全
            with tabs[5]:
                q_col, s_col = st.columns(2)

                with q_col:
                    st.markdown("### 📊 质量审核")
                    scores = quality.get("scores", {})
                    if scores:
                        for dim, info in scores.items():
                            score = info.get("score", 0)
                            color = "#10b981" if score >= 4 else "#f59e0b" if score >= 3 else "#ef4444"
                            st.markdown(
                                f"**{dim}**: "
                                f"<span style='color:{color};font-weight:700'>{'⭐'*score}{'☆'*(5-score)} {score}/5</span>"
                                f"<br><small>{info.get('reason','')}</small>",
                                unsafe_allow_html=True,
                            )
                    st.markdown(f"**总评**: {quality.get('overall_score','?')}/5 — {quality.get('verdict','?')}")
                    suggestions = quality.get("suggestions", [])
                    if suggestions:
                        st.markdown("**建议**:")
                        for s in suggestions:
                            st.markdown(f"- {s}")

                with s_col:
                    st.markdown("### 🛡️ 内容安全扫描")
                    if safety.get("passed"):
                        st.success("✅ 内容安全审核通过")
                    else:
                        st.error("🚫 内容安全审核未通过")
                    st.markdown(f"**模式**: {safety.get('scan_mode','')}")
                    st.markdown(f"**标记数**: {safety.get('total_flags',0)}")
                    st.markdown(f"**深度审核**: {'已执行' if safety.get('deep_scan_performed') else '无需'}")

                    blocked = safety.get("blocked", [])
                    if blocked:
                        st.markdown("**阻断项**:")
                        for b in blocked:
                            st.markdown(f"- 🚫 {b['category']}: {b.get('matched_keyword','')}")

                    warnings = safety.get("warnings", [])
                    if warnings:
                        st.markdown("**警告项**:")
                        for w in warnings:
                            st.markdown(f"- ⚠️ {w['category']}: {w.get('matched_keyword','')}")

            # ============================================================
            # 下载区域
            # ============================================================
            st.divider()
            dl_col1, dl_col2 = st.columns([1, 3])
            with dl_col1:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 下载完整 JSON",
                    data=json.dumps(result, ensure_ascii=False, indent=2),
                    file_name=f"short_drama_{timestamp}.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with dl_col2:
                st.caption(
                    "下载完整的生成结果 JSON 文件，包含所有角色、场景、分镜、Prompt "
                    "和质量/安全审核数据。可直接用于 AI 图像/视频生成。"
                )

        except RuntimeError as e:
            st.error(f"流水线执行失败: {e}")
        except Exception as e:
            st.error(f"未知错误: {e}")
            st.exception(e)

# ============================================================
# 空状态 — 未点击运行
# ============================================================
elif not run_btn:
    st.markdown("### 👆 点击上方按钮开始生成")
    st.markdown("""
    1. **选择输入方式**: 直接输入 / 上传文件 / 使用示例剧本
    2. **选择 LLM 提供商**: DeepSeek（推荐）或豆包
    3. **点击「生成短剧方案」**: 8-Phase 全链路自动执行
    4. **查看结果 & 下载 JSON**: 分镜表、Prompt、质量审核、安全扫描
    """)

    st.divider()
    st.caption("💡 **提示**: 未设置 API Key 时自动进入 Demo 模式，使用内置数据演示完整流程。")
