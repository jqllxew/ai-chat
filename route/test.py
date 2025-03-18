import json

import flask
from flask import request, Blueprint
import ai
from plugin.tx_cos import tmp_sts

test_api = Blueprint(name="test_api", import_name=__name__, url_prefix='/test')


@test_api.route('/ctx_get/<uid>', methods=['GET'])
def ctx_set(uid):
    ctx = ai.chat.u_model(uid).ctx
    # ctx.append(request.args.get('msg'))
    return json.dumps(list(ctx), ensure_ascii=False)


@test_api.route('/cos_sts', methods=['GET'])
def cos_temp():
    return json.dumps(tmp_sts(300), ensure_ascii=False)


@test_api.route('/stream', methods=['POST'])
def stream():
    """
    fetch('/test/stream', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({q: '你是谁？',model: 'gpt'})})
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
    qry = q.get("q")
    model = q.get("model")
    sid = q.get("sid")
    if not sid:
        sid = "test01"
    if qry.find("#") == 0:
        res = chat.chat(sid, qry, "test")
    else:
        chat.u_change_model(sid, model)
        res = chat.u_model(sid).reply_stream(qry)
    resp = flask.make_response(res)
    return resp

# @test_api.route('/chat', methods=['POST'])
# def chat_api():
#     data = request.get_json()
#     try:
#         res = {'code': 0, 'data': chat.chat('test01', data['msg'], 'test')}
#     except Exception as error:
#         res = {'code': 1, 'msg': 'err: ' + str(error)}
#     return json.dumps(res, ensure_ascii=False)
