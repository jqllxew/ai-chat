

import openai

res = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # 对话模型的名称
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ],
    stream=True
)

print(res)
for x in res:
    print(x.choices[0]['delta'].get('content') or '\n', end='')
