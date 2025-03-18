import json
import flask
import numpy as np
from flask import request, Blueprint
import ai
from plugin.tx_cos import tmp_sts

test_api = Blueprint(name="test_api", import_name=__name__, url_prefix='/test')


@test_api.route('/ctx_get/<uid>', methods=['GET'])
def ctx_get(uid):
    if isinstance(uid, str) and uid.isdigit():
        uid = np.int64(uid)
    ctx = ai.chat.u_model(uid).ctx
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
        res = ai.main(sid, qry, "test")
    else:
        ai.chat.u_change_model(sid, model)
        res = ai.chat.u_model(sid).reply_stream(qry)
    resp = flask.make_response(res)
    return resp
