import time
import json
import requests

API_KEY = "b19eb56dc466df154096a3fb43bcdb8e6837a2a552b4a87b6ace72af0ccae969"
BASE_URL = "https://api-auroraai.visionular.cn"


def create_video(
    prompt,
    duration=5,
    resolution="720P",
    size="16x9",
    model="seedance-2-0",
    image_url=None
):
    url = f"{BASE_URL}/v1/video-generation"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "size": size
    }

    if image_url:
        payload["images"] = [image_url]

    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        res = requests.post(
            url,
            headers=headers,
            data=body,
            timeout=60
        )

        try:
            result = res.json()
        except Exception:
            result = {
                "http_status": res.status_code,
                "text": res.text
            }

        create_video.last_response = result

        return (
            result.get("task_id")
            or result.get("taskId")
            or result.get("id")
            or result.get("data", {}).get("task_id")
            or result.get("data", {}).get("taskId")
            or result.get("data", {}).get("id")
        )

    except Exception as e:
        create_video.last_response = {
            "error": str(e)
        }
        return None


def query_video(task_id):
    url = f"{BASE_URL}/v1/query/video-generation"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    params = {
        "task_id": task_id
    }

    try:
        res = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=60
        )

        try:
            return res.json()
        except Exception:
            return {
                "http_status": res.status_code,
                "text": res.text
            }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


def get_video_url(result):
    data = result.get("data", {})

    possible_urls = [
        result.get("video_url"),
        result.get("url"),
        result.get("file_url"),
        result.get("output_url"),
        result.get("result_url"),

        data.get("video_url"),
        data.get("url"),
        data.get("file_url"),
        data.get("output_url"),
        data.get("result_url"),
        data.get("fileUrl"),
        data.get("videoUrl"),

        data.get("video", {}).get("url") if isinstance(data.get("video"), dict) else None,
    ]

    for url in possible_urls:
        if url:
            return url

    return None


def generate_seedance(
    prompt,
    resolution="720P",
    duration=5,
    max_attempts=300,
    sleep_seconds=5,
    image=None,
    image_url=None
):
    if image is not None and not image_url:
        return {
            "status": "failed",
            "error": "Seedance 当前文档要求图片必须是公网 URL，Streamlit 本地上传图不能直接传。请先用可灵或拍我AI测试图生视频。"
        }

    task_id = create_video(
        prompt=prompt,
        duration=duration,
        resolution=resolution,
        image_url=image_url
    )

    if not task_id:
        return {
            "status": "failed",
            "error": "没有拿到 task_id，创建任务失败",
            "raw_create_response": getattr(create_video, "last_response", None)
        }

    for i in range(max_attempts):
        result = query_video(task_id)
        data = result.get("data", {})

        status = (
            result.get("status")
            or result.get("state")
            or data.get("status")
            or data.get("state")
            or data.get("task_status")
            or data.get("taskStatus")
        )

        video_url = get_video_url(result)

        if video_url:
            return {
                "status": "success",
                "task_id": task_id,
                "video_url": video_url,
                "raw": result
            }

        status_text = str(status).lower()

        if status_text in ["success", "succeed", "succeeded", "completed", "done"]:
            return {
                "status": "success",
                "task_id": task_id,
                "video_url": video_url,
                "raw": result
            }

        if status_text in ["failed", "fail", "error"]:
            return {
                "status": "failed",
                "task_id": task_id,
                "raw": result
            }

        time.sleep(sleep_seconds)

    return {
        "status": "processing",
        "task_id": task_id
    }


if __name__ == "__main__":
    prompt = input("请输入Prompt: ")

    result = generate_seedance(
        prompt=prompt,
        duration=5,
        resolution="720P"
    )

    print(result)
