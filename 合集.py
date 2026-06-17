from keling import generate_kling
from seedance import generate_seedance
from 拍我ai import generate_pai
from aurora import generate_image


def generate_video(model, prompt, tts_text=""):

    if model == "kling":
        return generate_kling(prompt)

    elif model == "seedance":
        return generate_seedance(prompt)

    elif model == "拍我ai":
        return generate_pai(
            prompt,
            add_sound=True,
            sound_text="cinematic background music, ambient sound effects",
            add_lip_sync=bool(tts_text.strip()),
            tts_text=tts_text,
            speaker_id=""
        )

    else:
        return {
            "status": "failed",
            "error": "未知视频模型"
        }


def generate_picture(
    prompt,
    model="gpt-image-2",
    size="1024x1024",
    quality="auto",
    max_images=1
):
    return generate_image(
        prompt=prompt,
        model=model,
        size=size,
        quality=quality,
        max_images=max_images
    )


print("请选择生成类型")
print("1. 生成视频")
print("2. 生成图片")

task_choice = input("输入编号: ").strip()

if task_choice == "1":

    print("请选择视频模型")
    print("1. 可灵")
    print("2. 拍我AI")
    print("3. Seedance")

    choice = input("输入编号: ").strip()
    prompt = input("请输入视频 Prompt: ")

    tts_text = ""

    if choice == "2":
        tts_text = input("请输入台词，不需要可留空: ")

    if choice == "1":
        result = generate_video("kling", prompt)

    elif choice == "2":
        result = generate_video("拍我ai", prompt, tts_text)

    elif choice == "3":
        result = generate_video("seedance", prompt)

    else:
        result = {
            "status": "failed",
            "error": "输入错误"
        }

elif task_choice == "2":

    print("请选择图片模型")
    print("1. gpt-image-2")
    print("2. gemini-3-pro-image-preview")
    print("3. gemini-3.1-flash-image-preview")
    print("4. seedream-4.0")
    print("5. seedream-5.0-lite")

    choice = input("输入编号: ").strip()
    prompt = input("请输入图片 Prompt: ")

    model_map = {
        "1": "gpt-image-2",
        "2": "gemini-3-pro-image-preview",
        "3": "gemini-3.1-flash-image-preview",
        "4": "seedream-4.0",
        "5": "seedream-5.0-lite"
    }

    model = model_map.get(choice)

    if not model:
        result = {
            "status": "failed",
            "error": "输入错误"
        }
    else:
        size = input("请输入尺寸，默认 1024x1024: ").strip() or "1024x1024"
        quality = input("请输入质量，默认 auto: ").strip() or "auto"

        try:
            max_images = int(input("生成数量，默认 1: ").strip() or "1")
        except Exception:
            max_images = 1

        result = generate_picture(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            max_images=max_images
        )

else:
    result = {
        "status": "failed",
        "error": "输入错误"
    }

print(result)

