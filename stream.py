import streamlit as st

from keling import generate_kling
from seedance import generate_seedance
from 拍我ai import generate_pai

from database import (
    init_db,
    register_user,
    login_user,
    save_generation,
    get_my_generations,
    get_all_generations
)


st.set_page_config(page_title="AI视频生成平台", layout="wide")

init_db()


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""


if not st.session_state.logged_in:

    st.title("AI视频生成平台")

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


st.title("AI视频生成平台")

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


model = st.selectbox(
    "选择模型",
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


uploaded_image = st.file_uploader(
    "上传参考图片（可选，用于图生视频）",
    type=["jpg", "jpeg", "png"]
)

if uploaded_image is not None:
    st.image(uploaded_image, caption="已上传参考图", use_container_width=True)
    st.info("检测到参考图。后端支持后，将使用图生视频；目前如果后端没改，仍可能只按文生视频生成。")


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


if st.button("生成视频"):

    if prompt.strip() == "":
        st.error("请输入Prompt")

    else:
        with st.spinner("正在生成视频，请等待..."):

            if uploaded_image is not None:
                st.warning("你上传了参考图，但还需要对应模型后端支持图生视频接口。")

            if model == "可灵":
                result = generate_kling(
                    prompt,
                    audio=add_audio,
                    image=uploaded_image
                )

            elif model == "拍我AI":
                result = generate_pai(
                    prompt,
                    model=pai_model,
                    add_sound=add_audio,
                    sound_text="根据视频内容生成真实自然的环境音效",
                    add_lip_sync=add_voice,
                    tts_text=voice_text,
                    speaker_id=speaker_id,
                    image=uploaded_image
                )

            else:
                result = generate_seedance(
                    prompt,
                    resolution=resolution,
                    duration=duration,
                    image=uploaded_image
                )

        if isinstance(result, dict) and result.get("status") == "failed":
            st.error("生成失败")
            st.json(result)

        else:
            st.success("生成完成")

            save_generation(
                st.session_state.username,
                model,
                prompt,
                result
            )

            video_url = get_video_url(result)

            if video_url:
                st.video(video_url)
                st.write("视频链接：")
                st.write(video_url)
            else:
                st.error("没有找到视频链接")
                st.json(result)
