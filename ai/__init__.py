import ai.chat as chat
import ai.image as image


def main(uid: str, query: str, from_type: str):
    query = query.strip()
    if not query:
        return "请说出您的问题哦~"
    elif query.find("#draw") == 0:
        return image.draw(uid, query[5:], from_type)
    elif query.find("#changechat") == 0:
        chat_type = query.replace("#changechat", "", 1).strip()
        err = chat.u_change_model(uid, chat_type, from_type)
        return err or f"changed to {chat_type}"
    elif query.find("#changeimage") == 0:
        image_type = query.replace("#changeimage", "", 1).strip()
        err = image.u_change_model(uid, image_type, from_type)
        return err or f"changed to {image_type}"
    reply, err = chat.u_model(uid, from_type).reply(query)
    return err or reply


__all__ = ["main", "base"]
