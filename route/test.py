
import json
from collections import deque
from flask import request, Blueprint
from aichat.chat import user_contexts
from aichat.chat_factory import chat

test_api = Blueprint(name="test_api", import_name=__name__, url_prefix='/test')


# 测试接口
@test_api.route('/chat', methods=['post'])
def chat_api():
    req_data = request.get_data()
    if req_data is None or req_data == "" or req_data == {}:
        res = {'code': 1, 'msg': '请求内容不能为空'}
        return json.dumps(res, ensure_ascii=False)
    data = json.loads(req_data)
    print(data)
    try:
        msg = chat(0, data['msg'], 'test')
    except Exception as error:
        res = {'code': 1, 'msg': '请求异常: ' + str(error)}
        return json.dumps(res, ensure_ascii=False)
    else:
        res = {'code': 0, 'data': msg}
        return json.dumps(res, ensure_ascii=False)


@test_api.route('/ctx', methods=['GET'])
def ctx():
    data = {}
    for k, v in user_contexts.items():
        data[k] = list(v)
    return json.dumps(data, ensure_ascii=False)


@test_api.route('/ctx_set/<int:uid>', methods=['GET'])
def ctx_set(uid):
    msg = request.args.get('msg')
    if user_contexts.get(uid) is None:
        user_contexts[uid] = deque()
    user_contexts[uid].append(msg)
    data = {}
    for k, v in user_contexts.items():
        data[k] = list(v)
    return json.dumps(data, ensure_ascii=False)
