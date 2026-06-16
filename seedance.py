import time
import requests

API_KEY = "b19eb56dc466df154096a3fb43bcdb8e6837a2a552b4a87b6ace72af0ccae969"
BASE_URL = "https://api-auroraai.visionular.cn"


def create_video(prompt, duration=15, resolution="720P", size="16x9", model="seedance-2-0"):
    url = f"{BASE_URL}/v1/video-generation"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "size": size
    }

    res = requests.post(url, headers=headers, json=data, timeout=60)
    print("创建状态码:", res.status_code)
    print("创建返回:", res.text)

    result = res.json()

    return result.get("task_id") or result.get("data", {}).get("task_id")


def query_video(task_id):
    url = f"{BASE_URL}/v1/query/video-generation"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    params = {
        "task_id": task_id
    }

    res = requests.get(url, headers=headers, params=params, timeout=60)
    print("查询状态码:", res.status_code)
    print("查询返回:", res.text)

    return res.json()


def get_video_url(result):
    data = result.get("data", {})

    possible_paths = [
        result.get("video_url"),
        result.get("url"),
        data.get("file_url"),
        data.get("video_url"),
        data.get("url"),
        data.get("output_url"),
        data.get("result_url"),
    ]

    for item in possible_paths:
        if item:
            return item

    return None


def generate_seedance(
    prompt,
    resolution="720P",
    duration=15,
    max_attempts=300,
    sleep_seconds=5
):
    task_id = create_video(
        prompt=prompt,
        duration=duration,
        resolution=resolution
    )

    if not task_id:
        return {
            "status": "failed",
            "error": "没有拿到 task_id"
        }

    print("Seedance任务ID:", task_id)

    for i in range(max_attempts):
        result = query_video(task_id)

        data = result.get("data", {})
        status = (
            result.get("status")
            or result.get("state")
            or data.get("status")
            or data.get("state")
            or data.get("task_status")
        )

        print(f"轮询第 {i + 1} 次，状态:", status)

        status_text = str(status).lower()

        if status_text in ["succeed", "succeeded", "success", "completed", "done"]:
            video_url = get_video_url(result)

            return {
                "status": "success",
                "task_id": task_id,
                "video_url": video_url,
                "resolution": resolution,
                "raw": result
            }

        if status_text in ["failed", "fail", "error"]:
            return {
                "status": "failed",
                "task_id": task_id,
                "error": "任务失败",
                "raw": result
            }

        time.sleep(sleep_seconds)

    return {
        "status": "processing",
        "message": "任务还在生成中，可以稍后用 task_id 查询",
        "task_id": task_id
    }


if __name__ == "__main__":
    test_prompt = input("请输入Seedance测试Prompt: ")
    resolution = input("分辨率 480P / 720P，默认720P: ").strip() or "720P"
    print(generate_seedance(test_prompt, resolution=resolution))
