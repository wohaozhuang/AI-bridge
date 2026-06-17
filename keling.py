import time
import jwt
import requests
import base64

ACCESS_KEY = "ADTGPyPydenrbtA4dryptBJRykN9hrPC"
SECRET_KEY = "gkBNLaKedMDmhpaCGEBr3FPYKbFPRPnT"

BASE_URL = "https://api-beijing.klingai.com"


def make_token():
    payload = {
        "iss": ACCESS_KEY,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def get_headers():
    return {
        "Authorization": f"Bearer {make_token()}",
        "Content-Type": "application/json"
    }


def image_to_base64(image):
    return base64.b64encode(image.getvalue()).decode("utf-8")


def create_text_video(
    prompt,
    duration="5",
    aspect_ratio="16:9",
    mode="std"
):
    url = f"{BASE_URL}/v1/videos/text2video"

    data = {
        "model_name": "kling-v1",
        "prompt": prompt,
        "duration": str(duration),
        "aspect_ratio": aspect_ratio,
        "mode": mode,
        "cfg_scale": 0.5
    }

    res = requests.post(url, headers=get_headers(), json=data, timeout=60)
    print("文生视频创建状态码:", res.status_code)
    print("文生视频创建返回:", res.text)

    res.raise_for_status()
    result = res.json()

    return result.get("data", {}).get("task_id")


def create_image_video(
    prompt,
    image,
    duration="5",
    aspect_ratio="16:9",
    mode="std"
):
    url = f"{BASE_URL}/v1/videos/image2video"

    image_base64 = image_to_base64(image)

    data = {
        "model_name": "kling-v1",
        "image": image_base64,
        "prompt": prompt,
        "duration": str(duration),
        "aspect_ratio": aspect_ratio,
        "mode": mode,
        "cfg_scale": 0.5
    }

    res = requests.post(url, headers=get_headers(), json=data, timeout=60)
    print("图生视频创建状态码:", res.status_code)
    print("图生视频创建返回:", res.text)

    res.raise_for_status()
    result = res.json()

    return result.get("data", {}).get("task_id")


def query_text_video(task_id):
    url = f"{BASE_URL}/v1/videos/text2video/{task_id}"

    res = requests.get(url, headers=get_headers(), timeout=60)
    print("查询文生视频状态码:", res.status_code)
    print("查询文生视频返回:", res.text)

    res.raise_for_status()
    return res.json()


def query_image_video(task_id):
    url = f"{BASE_URL}/v1/videos/image2video/{task_id}"

    res = requests.get(url, headers=get_headers(), timeout=60)
    print("查询图生视频状态码:", res.status_code)
    print("查询图生视频返回:", res.text)

    res.raise_for_status()
    return res.json()


def generate_video(prompt, duration="5", image=None):
    if image is not None:
        task_id = create_image_video(
            prompt=prompt,
            image=image,
            duration=duration
        )
        query_func = query_image_video
    else:
        task_id = create_text_video(
            prompt=prompt,
            duration=duration
        )
        query_func = query_text_video

    if not task_id:
        print("❌ 没有拿到视频 task_id")
        return None, None

    print("视频任务ID:", task_id)

    for i in range(120):
        result = query_func(task_id)

        data = result.get("data", {})
        status = data.get("task_status")

        print(f"第 {i + 1} 次查询视频，状态:", status)

        if status == "succeed":
            videos = data.get("task_result", {}).get("videos", [])

            if not videos:
                print("❌ 视频成功但没有 videos")
                return None, None

            video = videos[0]
            video_url = video.get("url")
            video_id = video.get("id")

            return video_url, video_id

        if status == "failed":
            print("❌ 视频生成失败:", result)
            return None, None

        time.sleep(5)

    print("❌ 视频生成超时")
    return None, None


def create_video_to_audio(
    video_url=None,
    video_id=None,
    sound_effect_prompt="",
    bgm_prompt="",
    asmr_mode=True
):
    url = f"{BASE_URL}/v1/audio/video-to-audio"

    data = {
        "sound_effect_prompt": sound_effect_prompt,
        "bgm_prompt": bgm_prompt,
        "asmr_mode": asmr_mode
    }

    if video_id:
        data["video_id"] = video_id
    elif video_url:
        data["video_url"] = video_url
    else:
        raise ValueError("video_id 和 video_url 必须二选一")

    res = requests.post(url, headers=get_headers(), json=data, timeout=60)
    print("创建音频状态码:", res.status_code)
    print("创建音频返回:", res.text)

    res.raise_for_status()
    result = res.json()

    return result.get("data", {}).get("task_id")


def query_video_to_audio(task_id):
    url = f"{BASE_URL}/v1/audio/video-to-audio/{task_id}"

    res = requests.get(url, headers=get_headers(), timeout=60)
    print("查询音频状态码:", res.status_code)
    print("查询音频返回:", res.text)

    res.raise_for_status()
    return res.json()


def get_final_video_url(result):
    data = result.get("data", {})
    task_result = data.get("task_result", {})

    possible = [
        task_result.get("url"),
        task_result.get("video_url"),
        task_result.get("result_url"),
        data.get("video_url"),
        data.get("url")
    ]

    for item in possible:
        if item:
            return item

    videos = task_result.get("videos", [])
    if videos:
        return videos[0].get("url")

    return None


def generate_audio_for_video(
    video_url=None,
    video_id=None,
    sound_effect_prompt="",
    bgm_prompt="",
    asmr_mode=True
):
    task_id = create_video_to_audio(
        video_url=video_url,
        video_id=video_id,
        sound_effect_prompt=sound_effect_prompt,
        bgm_prompt=bgm_prompt,
        asmr_mode=asmr_mode
    )

    if not task_id:
        print("❌ 没有拿到音频 task_id")
        return None

    print("音频任务ID:", task_id)

    for i in range(120):
        result = query_video_to_audio(task_id)

        data = result.get("data", {})
        status = data.get("task_status")

        print(f"第 {i + 1} 次查询音频，状态:", status)

        if status == "succeed":
            final_url = get_final_video_url(result)
            return final_url

        if status == "failed":
            print("❌ 音频生成失败:", result)
            return None

        time.sleep(5)

    print("❌ 音频生成超时")
    return None


def generate_kling(
    prompt,
    audio=True,
    duration="5",
    image=None
):
    video_url, video_id = generate_video(
        prompt,
        duration=duration,
        image=image
    )

    if not video_url and not video_id:
        return {
            "status": "failed",
            "error": "视频生成失败"
        }

    if not audio:
        return {
            "status": "success",
            "video_url": video_url,
            "video_id": video_id
        }

    final_url = generate_audio_for_video(
        video_url=video_url,
        video_id=video_id,
        sound_effect_prompt="根据视频内容生成真实自然的环境音效",
        bgm_prompt="电影感背景音乐，氛围自然，不要盖过音效",
        asmr_mode=True
    )

    if not final_url:
        return {
            "status": "failed",
            "error": "视频生成成功，但声音生成失败",
            "video_url": video_url,
            "video_id": video_id
        }

    return {
        "status": "success",
        "video_url": final_url,
        "video_id": video_id
    }


if __name__ == "__main__":
    video_prompt = input("请输入视频Prompt: ")
    result = generate_kling(video_prompt, audio=True)
    print(result)
