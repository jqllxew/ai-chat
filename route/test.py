import json
from collections import deque

import flask
from flask import request, Blueprint

import aichat
from aichat import user_contexts

test_api = Blueprint(name="test_api", import_name=__name__, url_prefix='/test')


@test_api.route('/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    try:
        res = {'code': 0, 'data': aichat.chat('test01', data['msg'], 'test')}
    except Exception as error:
        res = {'code': 1, 'msg': '请求异常: ' + str(error)}
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


@test_api.route('/stream', methods=['POST'])
def stream():
    """
    fetch('/test/stream', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({q: '你是谁？'})})
    .then(x => x.body.pipeThrough(new TextDecoderStream()).getReader())
    .then(async reader => {
        console.log(reader);
        while(true) {
            var {value, done} = await reader.read();
            if (done) break;
            console.log(value);
        }
    })
    :return:
    """
    q = request.get_json()
    g = aichat.u_model("test01").reply_stream(q.get("q"))
    return flask.make_response(g)
