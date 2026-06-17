import streamlit as st

from keling import generate_kling
from seedance import generate_seedance
from 拍我ai import generate_pai
from aurora import generate_image

from database import (
    init_db,
    register_user,
    login_user,
    save_generation,
    get_my_generations,
    get_all_generations
)


st.set_page_config(page_title="AI生成平台", layout="wide")

init_db()


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""


# =========================
# 登录 / 注册页面
# =========================
if not st.session_state.logged_in:

    st.title("AI生成平台")

    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")

        if st.button("登录"):
            if username.strip() == "" or password.strip() == "":
                st.error("请输入用户名和密码")
            else:
                ok, role = login_user(username, password)

                if ok:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = role
                    st.rerun()
                else:
                    st.error("用户名或密码错误")

    with tab2:
        new_username = st.text_input("注册用户名", key="register_username")
        new_password = st.text_input("注册密码", type="password", key="register_password")

        if st.button("注册"):
            if new_username.strip() == "" or new_password.strip() == "":
                st.error("请输入注册用户名和密码")
            else:
                ok, msg = register_user(new_username, new_password)

                if ok:
                    st.success("注册成功，请返回登录")
                else:
                    st.error(msg)

    st.stop()


# =========================
# 主页面
# =========================
st.title("AI生成平台")

st.sidebar.success(f"当前用户：{st.session_state.username}")
st.sidebar.write(f"角色：{st.session_state.role}")

if st.sidebar.button("退出登录"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()


st.sidebar.markdown("---")
st.sidebar.subheader("历史记录")

if st.sidebar.button("查看我的生成记录"):
    rows = get_my_generations(st.session_state.username)

    if not rows:
        st.sidebar.info("暂无生成记录")
    else:
        for row in rows[:20]:
            history_model, history_prompt, history_result, created_at = row

            st.sidebar.markdown(f"**{created_at}**")
            st.sidebar.write(f"模型：{history_model}")
            st.sidebar.write(history_prompt[:50] + "...")
            st.sidebar.markdown("---")


if st.session_state.role == "admin":
    if st.sidebar.button("查看全部用户生成记录"):
        rows = get_all_generations()

        if not rows:
            st.sidebar.info("暂无生成记录")
        else:
            st.subheader("全部用户生成记录")

            for row in rows:
                username, history_model, history_prompt, history_result, created_at = row

                st.markdown(f"### {created_at}")
                st.write(f"用户：{username}")
                st.write(f"模型：{history_model}")
                st.write(f"Prompt：{history_prompt}")
                st.write(f"结果：{history_result}")
                st.markdown("---")


task_type = st.radio(
    "选择生成类型",
    ["视频", "图片"],
    horizontal=True
)


# =========================
# 视频模式
# =========================
if task_type == "视频":

    model = st.selectbox(
        "选择视频模型",
        ["可灵", "拍我AI", "Seedance"]
    )

    resolution = st.selectbox(
        "选择分辨率",
        ["480P", "720P"],
        index=1
    )

    duration = st.radio(
        "视频时长",
        [5, 10],
        index=0,
        horizontal=True,
        format_func=lambda x: f"{x}秒"
    )

    uploaded_images = st.file_uploader(
        "上传参考图片（可选，可多选；当前生成默认使用第一张）",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    first_image = None

    if uploaded_images:
        st.info(f"已上传 {len(uploaded_images)} 张参考图")

        cols = st.columns(min(len(uploaded_images), 4))

        for i, img in enumerate(uploaded_images):
            with cols[i % 4]:
                st.image(img, caption=f"参考图 {i + 1}", use_container_width=True)

        first_image = uploaded_images[0]

    prompt = st.text_area(
        "请输入视频描述",
        height=300
    )

    st.markdown("---")

    add_audio = st.checkbox("生成声音/环境音", value=True)

    voice_text = ""
    speaker_id = ""
    pai_model = None

    if model == "拍我AI":

        if add_audio:
            pai_model = "v5"
            st.info("拍我AI已开启音效，自动使用 v5，因为 v6 不支持 sound_effect_switch。")
        else:
            pai_model = "v6"
            st.info("拍我AI未开启音效，自动使用 v6。")

        pai_model = st.selectbox(
            "拍我AI模型",
            ["v5", "v6"],
            index=0 if add_audio else 1
        )

        add_voice = st.checkbox("朗读台词 / 对口型 TTS", value=False)

        if add_voice:
            voice_text = st.text_area(
                "请输入要朗读的台词",
                height=160,
                placeholder="例如：女孩说：你终于来了。男孩说：我一直在等你。"
            )
            speaker_id = st.text_input("speaker_id，可不填", value="")

    else:
        add_voice = False
        st.info("可灵：开启声音会调用 video-to-audio；Seedance：按当前接口返回结果。")


# =========================
# 图片模式
# =========================
else:

    model = st.selectbox(
        "选择图片模型",
        [
            "gpt-image-2",
            "gemini-3-pro-image-preview",
            "gemini-3.1-flash-image-preview",
            "seedream-4.0",
            "seedream-5.0-lite"
        ]
    )

    image_size = st.selectbox(
        "选择图片尺寸",
        [
            "1024x1024",
            "auto",
            "16x9",
            "9x16",
            "1x1",
            "3x4",
            "4x3"
        ],
        index=0
    )

    quality = st.selectbox(
        "选择图片质量",
        [
            "auto",
            "high",
            "medium",
            "low",
            "1K",
            "2K",
            "3K"
        ],
        index=0
    )

    max_images = st.selectbox(
        "生成图片数量",
        [1, 2, 3, 4],
        index=0
    )

    prompt = st.text_area(
        "请输入图片描述",
        height=300
    )


def get_video_url(result):
    if not isinstance(result, dict):
        return None

    if result.get("video_url"):
        return result["video_url"]

    try:
        return result["raw"]["data"]["task_result"]["videos"][0]["url"]
    except Exception:
        pass

    try:
        return result["raw"]["Resp"]["url"]
    except Exception:
        pass

    try:
        return result["raw"]["Resp"]["result"]["url"]
    except Exception:
        pass

    try:
        return result["raw"]["data"]["video_url"]
    except Exception:
        pass

    try:
        return result["raw"]["data"]["url"]
    except Exception:
        pass

    return None


if st.button("开始生成"):

    if prompt.strip() == "":
        st.error("请输入Prompt")

    else:
        with st.spinner("正在生成，请等待..."):

            if task_type == "视频":

                if model == "可灵":
                    result = generate_kling(
                        prompt,
                        audio=add_audio,
                        duration=duration,
                        image=first_image
                    )

                elif model == "拍我AI":
                    result = generate_pai(
                        prompt,
                        model=pai_model,
                        duration=duration,
                        add_sound=add_audio,
                        sound_text="根据视频内容生成真实自然的环境音效",
                        add_lip_sync=add_voice,
                        tts_text=voice_text,
                        speaker_id=speaker_id,
                        image=first_image
                    )

                else:
                    result = generate_seedance(
                        prompt,
                        resolution=resolution,
                        duration=duration,
                        image=first_image
                    )

            else:
                result = generate_image(
                    prompt=prompt,
                    model=model,
                    size=image_size,
                    quality=quality,
                    max_images=max_images
                )

        if isinstance(result, dict) and result.get("status") == "failed":
            st.error("生成失败")
            st.json(result)

        else:
            st.success("生成完成")

            save_generation(
                st.session_state.username,
                f"{task_type}-{model}",
                prompt,
                result
            )

            if task_type == "图片":

                image_urls = result.get("image_urls", [])

                if image_urls:
                    for i, img_url in enumerate(image_urls):
                        st.image(img_url, caption=f"生成图片 {i + 1}", use_container_width=True)
                        st.write("图片链接：")
                        st.write(img_url)
                else:
                    st.error("没有找到图片链接")
                    st.json(result)

            else:

                video_url = get_video_url(result)

                if video_url:
                    st.video(video_url)
                    st.write("视频链接：")
                    st.write(video_url)
                else:
                    st.error("没有找到视频链接")
                    st.json(result)
