import time
import json
import requests

API_KEY = "81f066249921b04d6a93fdc19923f58599ee82feef73cbde27b9216475a1fb59"
BASE_URL = "https://api-auroraai.visionular.cn"


def get_headers(json_mode=True):
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    if json_mode:
        headers["Content-Type"] = "application/json; charset=utf-8"

    return headers


def create_image_task(
    prompt,
    model="gpt-image-2",
    size="1024x1024",
    quality="auto",
    max_images=1,
    images=None
):
    url = f"{BASE_URL}/v1/image-generation"

    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "max_images": max_images
    }

    if images:
        payload["images"] = images

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    res = requests.post(
        url,
        headers=get_headers(json_mode=True),
        data=body,
        timeout=120
    )

    print("创建图片状态码:", res.status_code)
    print("创建图片返回:", res.text)

    try:
        return res.json()
    except Exception:
        return {
            "status": "failed",
            "error": "创建图片接口返回不是 JSON",
            "http_status": res.status_code,
            "text": res.text
        }


def query_image_task(task_id):
    url = f"{BASE_URL}/v1/query/image-generation"

    params = {
        "task_id": task_id
    }

    res = requests.get(
        url,
        headers=get_headers(json_mode=False),
        params=params,
        timeout=60
    )

    print("查询图片状态码:", res.status_code)
    print("查询图片返回:", res.text)

    try:
        return res.json()
    except Exception:
        return {
            "status": "failed",
            "error": "查询图片接口返回不是 JSON",
            "http_status": res.status_code,
            "text": res.text
        }


def extract_task_id(result):
    data = result.get("data", {})

    return (
        result.get("task_id")
        or result.get("taskId")
        or result.get("id")
        or data.get("task_id")
        or data.get("taskId")
        or data.get("id")
    )


def extract_status(result):
    data = result.get("data", {})

    return (
        result.get("status")
        or result.get("state")
        or data.get("status")
        or data.get("state")
        or data.get("task_status")
        or data.get("taskStatus")
    )


def extract_image_urls(result):
    urls = []

    data = result.get("data", {})

    single_urls = [
        result.get("image_url"),
        result.get("imageUrl"),
        result.get("url"),
        result.get("file_url"),
        result.get("fileUrl"),
        result.get("output_url"),
        result.get("outputUrl"),
        result.get("result_url"),
        result.get("resultUrl"),

        data.get("image_url"),
        data.get("imageUrl"),
        data.get("url"),
        data.get("file_url"),
        data.get("fileUrl"),
        data.get("output_url"),
        data.get("outputUrl"),
        data.get("result_url"),
        data.get("resultUrl"),
    ]

    for item in single_urls:
        if isinstance(item, str) and item.startswith("http"):
            urls.append(item)

    list_fields = [
        result.get("images"),
        result.get("image_urls"),
        result.get("imageUrls"),
        result.get("urls"),
        result.get("results"),
        result.get("output_images"),
        result.get("outputImages"),

        data.get("images"),
        data.get("image_urls"),
        data.get("imageUrls"),
        data.get("urls"),
        data.get("results"),
        data.get("output_images"),
        data.get("outputImages"),
    ]

    for item_list in list_fields:
        if isinstance(item_list, list):
            for item in item_list:
                if isinstance(item, str) and item.startswith("http"):
                    urls.append(item)

                elif isinstance(item, dict):
                    url = (
                        item.get("url")
                        or item.get("image_url")
                        or item.get("imageUrl")
                        or item.get("file_url")
                        or item.get("fileUrl")
                        or item.get("output_url")
                        or item.get("outputUrl")
                    )

                    if isinstance(url, str) and url.startswith("http"):
                        urls.append(url)

    return list(dict.fromkeys(urls))


def generate_image(
    prompt,
    model="gpt-image-2",
    size="1024x1024",
    quality="auto",
    max_images=1,
    images=None,
    max_attempts=180,
    sleep_seconds=3
):
    create_result = create_image_task(
        prompt=prompt,
        model=model,
        size=size,
        quality=quality,
        max_images=max_images,
        images=images
    )

    image_urls = extract_image_urls(create_result)

    if image_urls:
        return {
            "status": "success",
            "image_urls": image_urls,
            "raw": create_result
        }

    task_id = extract_task_id(create_result)

    if not task_id:
        return {
            "status": "failed",
            "error": "没有拿到 task_id，也没有直接返回图片链接",
            "raw": create_result
        }

    for i in range(max_attempts):
        result = query_image_task(task_id)

        image_urls = extract_image_urls(result)
        status = extract_status(result)
        status_text = str(status).lower()

        print(f"第 {i + 1} 次查询图片，状态:", status)

        if image_urls:
            return {
                "status": "success",
                "task_id": task_id,
                "image_urls": image_urls,
                "raw": result
            }

        if status_text in ["success", "succeed", "succeeded", "completed", "done"]:
            return {
                "status": "success",
                "task_id": task_id,
                "image_urls": image_urls,
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
        "task_id": task_id,
        "message": "图片任务仍在生成中"
    }


if __name__ == "__main__":
    prompt = input("请输入图片 Prompt: ")

    result = generate_image(
        prompt=prompt,
        model="gpt-image-2",
        size="1024x1024",
        quality="auto",
        max_images=1
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
