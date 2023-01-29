from collections import deque
import openai
from aichat.chat import ChatAI, user_contexts
from aiimage import image_factory


class OpenAI(ChatAI):
    def __init__(self, api_key: str, model_id: str, max_req_length: int, max_resp_tokens: int):
        openai.api_key = api_key
        self.model_id = model_id
        self.max_req_length = max_req_length
        self.max_resp_tokens = max_resp_tokens

    def reply_text(self, uid: int, query: str):
        if uid is not None:
            if user_contexts.get(uid) is None:
                user_contexts[uid] = deque()
            user_contexts[uid].append(query)
            _query = "\r\n".join(user_contexts[uid])
            while len(_query) > self.max_req_length:
                print(f"[OPEN_AI]上下文长度 {len(_query)} 超过 {self.max_req_length}")
                user_contexts[uid].popleft()
                _query = "\r\n".join(user_contexts[uid])
            query = _query
        print(f"[OPEN_AI] len {len(query)}\n{query}")
        try:
            response = openai.Completion.create(
                model=self.model_id,  # 对话模型的名称
                prompt=query,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                # 回复最大的tokens，用达芬奇003来说需满足 prompt_tokens + max_tokens <= 4000
                # 参考文档的MAX REQUEST https://beta.openai.com/docs/models/gpt-3
                max_tokens=self.max_resp_tokens,
                top_p=1,
                frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.6,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                stop=["#"]
            )
            res_content = response.choices[0]["text"].strip()
            if uid is not None and user_contexts.get(uid) is not None:
                user_contexts[uid].append(res_content)
        except Exception as e:
            print(e)
            if uid is not None and user_contexts.get(uid) is not None:
                user_contexts[uid].pop()
            return f"[OPEN_AI]错误信息: {e}"
        print(f"[OPEN_AI] reply={res_content}")
        return res_content

    def reply_image(self, uid: int, query: str, from_type: str):
        reply_format = "提示词：{}\n负提示：{}\n随机数：{}\n耗时秒：{:.3f}\n宽高：{}\n"
        image_res = image_factory.generate_by_query(uid, query, from_type)
        reply_format = reply_format.format(
            image_res.prompt if image_res.image is None else (image_res.prompt + '+[图片参数]'),
            "默认" if image_res.neg_prompt == "" else image_res.neg_prompt,
            image_res.seed, image_res.generate_seconds, f"{image_res.width}x{image_res.height}")
        if image_res.generate_err is None:
            if from_type == 'qq':
                reply_format += f"[CQ:image,file={image_res.generate_image_path}]"
            else:
                reply_format += image_res.generate_image_path
        else:
            reply_format += f"generate error because {image_res.generate_err}"
        return reply_format

    # def create_img(self, query):
    #     try:
    #         print("[OPEN_AI] image_query={}".format(query))
    #         response = openai.Image.create(
    #             prompt=query,  # 图片描述
    #             n=1,  # 每次生成图片的数量
    #             size="512x512"  # 图片大小,可选有 256x256, 512x512, 1024x1024
    #         )
    #         image_url = response['data'][0]['url']
    #         print("[OPEN_AI] image_url={}".format(image_url))
    #     except Exception as e:
    #         print(e)
    #         return None
    #     return image_url
    #
    # def edit_img(self, query, src_img):
    #     try:
    #         response = openai.Image.create_edit(
    #             image=open(src_img, 'rb'),
    #             mask=open('cat-mask.png', 'rb'),
    #             prompt=query,
    #             n=1,
    #             size='512x512'
    #         )
    #         image_url = response['data'][0]['url']
    #         print("[OPEN_AI] image_url={}".format(image_url))
    #     except Exception as e:
    #         print(e)
    #         return None
    #     return image_url
    #
    # def migration_img(self, query, src_img):
    #
    #     try:
    #         response = openai.Image.create_variation(
    #             image=open(src_img, 'rb'),
    #             n=1,
    #             size="512x512"
    #         )
    #         image_url = response['data'][0]['url']
    #         print("[OPEN_AI] image_url={}".format(image_url))
    #     except Exception as e:
    #         print(e)
    #         return None
    #     return image_url
