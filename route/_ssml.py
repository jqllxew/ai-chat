import re


def find_ssml(text):
    match = re.search(r'<speak.+?>.*?</speak>', text, flags=re.DOTALL)
    return match.group() if match else None
