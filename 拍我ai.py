import time
import uuid
import requests

API_KEY = "sk-54fd1a9daa94cf4c96e3c11e736f86c8"

BASE_URL = "https://app-api.pixverseai.cn"


def make_headers():
    return {
        "API-KEY": API_KEY,
        "Ai-Trace-Id": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }


def create_video(
    prompt,
    duration=5,
    aspect_ratio="16:9",
    model="v6",
    quality="540p",
    add_sound=False,
    sound_text="",
    add_lip_sync=False,
    tts_text="",
    speaker_id=""
):
    url = f"{BASE_URL}/openapi/v2/video/text/generate"

    data = {
        "aspect_ratio": aspect_ratio,
        "duration": duration,
        "model": model,
        "motion_mode": "normal",
        "prompt": prompt,
        "quality": quality,
        "seed": 0,
        "water_mark": False
    }

    # 音效
    if add_sound:
        data["sound_effect_switch"] = True
        data["sound_effect_content"] = sound_text

    # 对口型 + TTS
    if add_lip_sync and tts_text.strip():
        data["lip_sync_tts_switch"] = True
        data["lip_sync_tts_content"] = tts_text

        if speaker_id.strip():
            data["lip_sync_tts_speaker_id"] = speaker_id

    res = requests.post(
        url,
        headers=make_headers(),
        json=data,
        timeout=540
    )

    print("创建状态码:", res.status_code)
    print("创建返回:", res.text)

    result = res.json()

    if result.get("ErrCode") != 0:
        return None, result

    return result.get("Resp", {}).get("video_id"), result


def query_video(video_id):
    url = f"{BASE_URL}/openapi/v2/video/result/{video_id}"

    headers = {
        "API-KEY": API_KEY,
        "Ai-Trace-Id": str(uuid.uuid4())
    }

    res = requests.get(
        url,
        headers=headers,
        timeout=60
    )

    print("查询状态码:", res.status_code)
    print("查询返回:", res.text)

    return res.json()


def generate_pai(
    prompt,
    max_attempts=300,
    sleep_seconds=5,
    model="v6",
    quality="540p",
    duration=5,
    add_sound=False,
    sound_text="",
    add_lip_sync=False,
    tts_text="",
    speaker_id=""
):
    video_id, create_result = create_video(
        prompt=prompt,
        duration=duration,
        model=model,
        quality=quality,
        add_sound=add_sound,
        sound_text=sound_text,
        add_lip_sync=add_lip_sync,
        tts_text=tts_text,
        speaker_id=speaker_id
    )

    if not video_id:
        return {
            "status": "failed",
            "error": "没有拿到 video_id",
            "raw": create_result
        }

    print("拍我AI任务ID:", video_id)

    for i in range(max_attempts):

        result = query_video(video_id)

        resp = result.get("Resp", {})
        status = resp.get("status")

        print(f"轮询第 {i + 1} 次，状态:", status)

        # 成功
        if status == 1:

            video_url = (
                resp.get("url")
                or resp.get("video_url")
                or resp.get("download_url")
            )

            print("视频地址:", video_url)

            return {
                "status": "success",
                "video_id": video_id,
                "video_url": video_url,
                "raw": result
            }

        # 生成中
        if status in [5, "5"]:
            time.sleep(sleep_seconds)
            continue

        # 失败
        return {
            "status": "failed",
            "video_id": video_id,
            "error": "任务失败",
            "raw": result
        }

    return {
        "status": "processing",
        "message": "任务仍在生成中",
        "video_id": video_id
    }


if __name__ == "__main__":

    video_prompt = input("请输入视频Prompt: ")

    model = input("模型(v6默认): ").strip() or "v6"

    add_sound = input("开启音效(y/n): ").strip().lower() == "y"

    sound_text = ""

    if add_sound:
        sound_text = (
            input("请输入音效Prompt(留空自动生成): ").strip()
            or "根据视频内容自动生成真实环境音效"
        )

    add_tts = input("开启人物说话(y/n): ").strip().lower() == "y"

    tts_text = ""
    speaker_id = ""

    if add_tts:
        tts_text = input("请输入人物台词: ").strip()
        speaker_id = input("speaker_id(可空): ").strip()

    result = generate_pai(
        prompt=video_prompt,
        model=model,
        add_sound=add_sound,
        sound_text=sound_text,
        add_lip_sync=add_tts,
        tts_text=tts_text,
        speaker_id=speaker_id
    )

    print(result)
