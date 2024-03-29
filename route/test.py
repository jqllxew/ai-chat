import json

import flask
from flask import request, Blueprint

import aichat

test_api = Blueprint(name="test_api", import_name=__name__, url_prefix='/test')


@test_api.route('/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    try:
        res = {'code': 0, 'data': aichat.chat('test01', data['msg'], 'test')}
    except Exception as error:
        res = {'code': 1, 'msg': 'err: ' + str(error)}
    return json.dumps(res, ensure_ascii=False)


@test_api.route('/ctx_set/<uid>', methods=['GET'])
def ctx_set(uid):
    ctx = aichat.u_model(uid).ctx
    ctx.append(request.args.get('msg'))
    return json.dumps(list(ctx), ensure_ascii=False)


@test_api.route('/stream', methods=['POST'])
def stream():
    """
    fetch('/test/stream', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({q: '你是谁？',model: 'glm'})})
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
    aichat.u_change_model("test01", q.get("model"))
    g = aichat.u_model("test01").reply_stream(q.get("q"))
    resp = flask.make_response(g)
    return resp
