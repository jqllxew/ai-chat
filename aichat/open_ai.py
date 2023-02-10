import openai
from aichat.chat import ChatAI, user_contexts
from aiimage import image_factory


class OpenAI(ChatAI):
    def __init__(self, api_key: str, model_id: str, max_req_length: int, max_resp_tokens: int):
        openai.api_key = api_key
        self.model_id = model_id
        self.max_req_length = max_req_length
        self.max_resp_tokens = max_resp_tokens

    # overwrite
    def get_prompt_by_uid(self, uid: str, query="", sep="\n\n"):
        prompt = super().get_prompt_by_uid(uid, query, sep)
        while len(prompt) > self.max_req_length:
            print(f"[OPEN_AI]上下文长度 {len(prompt)} 超过 {self.max_req_length}")
            user_contexts[uid].popleft()
            prompt = super().get_prompt_by_uid(uid=uid, sep=sep)
        return prompt

    def create(self, uid: str, query: str, stream=False):
        prompt = query
        if uid is not None:
            prompt = self.get_prompt_by_uid(uid, query)
        print(f"[OPEN_AI] len {len(prompt)}\n{prompt}")
        try:
            return openai.Completion.create(
                model=self.model_id,  # 对话模型的名称
                prompt=prompt,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                # 回复最大的tokens，用达芬奇003来说需满足 prompt_tokens + max_tokens <= 4000
                # 参考文档的MAX REQUEST https://beta.openai.com/docs/models/gpt-3
                max_tokens=self.max_resp_tokens,
                top_p=1,
                frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.6,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                stop=["#"],
                stream=stream), None
        except Exception as e:
            print(e)
            if uid is not None and user_contexts.get(uid) is not None:
                user_contexts[uid].pop()
            return None, f"[OPEN_AI]错误信息: {e}"

    def reply_text(self, uid: str, query: str):
        res, err = self.create(uid, query)
        if err is not None:
            return err
        res_content = res.choices[0]["text"].strip()
        if uid is not None and user_contexts.get(uid) is not None:
            user_contexts[uid].append(res_content)
        print(f"[OPEN_AI] reply={res_content}")
        return res_content

    def reply_stream(self, uid: str, query: str):
        res, err = self.create(uid, query, True)
        if err is not None:
            raise Exception(err)
        res_content = ""
        for r in res:
            t = r.choices[0].text
            res_content += t
            yield t
        res_content = res_content.strip()
        if uid is not None and user_contexts.get(uid) is not None:
            user_contexts[uid].append(res_content)
        print(f"[OPEN_AI] reply={res_content}")

    def reply_image(self, uid: str, query: str, from_type: str):
        image_res = image_factory.generate_by_query(uid, query, from_type)
        reply_format = "提示词：{}\n负提示：{}\n随机数：{}\n耗时秒：{:.3f}\n宽高：{}\n".format(
            image_res.prompt if image_res.image is None else (image_res.prompt + '+[图片参数]'),
            "默认" if image_res.neg_prompt == "" else image_res.neg_prompt,
            image_res.seed, image_res.generate_seconds, f"{image_res.width}x{image_res.height}")
        if image_res.generate_err is None:
            if from_type == 'qq':
                reply_format += f"[CQ:image,file={image_res.generate_image_path}]"
            elif from_type == 'wx':
                reply_format += f"[image={image_res.generate_image_path}]"
            else:
                reply_format += image_res.generate_image_path
        else:
            reply_format += f"generate error because {image_res.generate_err}"
        return reply_format
