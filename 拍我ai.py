import time
import uuid
import requests

API_KEY = "sk-54fd1a9daa94cf4c96e3c11e736f86c8"
BASE_URL = "https://app-api.pixverseai.cn"


def make_headers(json_mode=True):
    headers = {
        "API-KEY": API_KEY,
        "Ai-Trace-Id": str(uuid.uuid4())
    }

    if json_mode:
        headers["Content-Type"] = "application/json"

    return headers


def upload_image(image):
    url = f"{BASE_URL}/openapi/v2/image/upload"

    files = {
        "image": (
            image.name,
            image.getvalue(),
            image.type
        )
    }

    res = requests.post(
        url,
        headers=make_headers(json_mode=False),
        files=files,
        timeout=120
    )

    print("图片上传状态码:", res.status_code)
    print("图片上传返回:", res.text)

    result = res.json()

    if result.get("ErrCode") != 0:
        return None, result

    img_id = (
        result.get("Resp", {}).get("img_id")
        or result.get("Resp", {}).get("id")
        or result.get("Resp", {}).get("image_id")
    )

    return img_id, result


def create_text_video(
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

    if add_sound:
        data["sound_effect_switch"] = True
        data["sound_effect_content"] = sound_text

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

    print("文生视频创建状态码:", res.status_code)
    print("文生视频创建返回:", res.text)

    result = res.json()

    if result.get("ErrCode") != 0:
        return None, result

    return result.get("Resp", {}).get("video_id"), result


def create_image_video(
    prompt,
    img_id,
    duration=5,
    model="v6",
    quality="540p",
    add_sound=False,
    sound_text=""
):
    url = f"{BASE_URL}/openapi/v2/video/img/generate"

    data = {
        "duration": duration,
        "img_id": img_id,
        "model": model,
        "motion_mode": "normal",
        "prompt": prompt,
        "quality": quality,
        "seed": 0,
        "water_mark": False
    }

    if add_sound:
        data["sound_effect_switch"] = True
        data["sound_effect_content"] = sound_text

    res = requests.post(
        url,
        headers=make_headers(),
        json=data,
        timeout=540
    )

    print("图生视频创建状态码:", res.status_code)
    print("图生视频创建返回:", res.text)

    result = res.json()

    if result.get("ErrCode") != 0:
        return None, result

    return result.get("Resp", {}).get("video_id"), result


def query_video(video_id):
    url = f"{BASE_URL}/openapi/v2/video/result/{video_id}"

    res = requests.get(
        url,
        headers=make_headers(json_mode=False),
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
    speaker_id="",
    image=None
):
    if image is not None:
        img_id, upload_result = upload_image(image)

        if not img_id:
            return {
                "status": "failed",
                "error": "图片上传失败，没有拿到 img_id",
                "raw": upload_result
            }

        video_id, create_result = create_image_video(
            prompt=prompt,
            img_id=img_id,
            duration=duration,
            model=model,
            quality=quality,
            add_sound=add_sound,
            sound_text=sound_text
        )

    else:
        video_id, create_result = create_text_video(
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

        if status == 1:
            video_url = (
                resp.get("url")
                or resp.get("video_url")
                or resp.get("download_url")
            )

            return {
                "status": "success",
                "video_id": video_id,
                "video_url": video_url,
                "quality": quality,
                "raw": result
            }

        if status in [5, "5"]:
            time.sleep(sleep_seconds)
            continue

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
