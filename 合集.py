from keling import generate_kling
from seedance import generate_seedance
from 拍我ai import generate_pai


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
            "error": "未知模型"
        }


print("请选择模型")
print("1. 可灵")
print("2. 拍我AI")
print("3. Seedance")

choice = input("输入编号: ")
prompt = input("请输入Prompt: ")

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
    print("输入错误")
    exit()

print(result)

