import io
import json
import time

import flask
from PIL import Image
from flask import request, Blueprint
import ai
from plugin import tx_cos
from plugin.tx_cos import tmp_sts

test_api = Blueprint(name="test_api", import_name=__name__, url_prefix='/test')

@test_api.route('/ctx_get/<uid>', methods=['GET'])
def ctx_get(uid):
    if isinstance(uid, str) and uid.isdigit():
        uid = int(uid)
    ctx = ai.chat.u_model(uid).ctx
    return json.dumps(list(ctx), ensure_ascii=False)

@test_api.route('/cos_sts', methods=['GET'])
def cos_temp():
    return json.dumps(tmp_sts(300), ensure_ascii=False)

def _stream(qry, model, sid):
    if not sid:
        sid = "test01"
    qry = qry.strip()
    if qry.find("#") == 0:
        res = ai.main(sid, qry, "test")
    else:
        ai.chat.u_change_model(sid, model)
        res = ai.chat.u_model(sid).reply_stream(qry)
    resp = flask.make_response(res)
    return resp


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
    qry, model, sid = q.get("q"), q.get("model"), q.get("sid")
    return _stream(qry, model, sid)


@test_api.route('/stream-form', methods=['POST'])
def stream_form():
    """
    let file = document.getElementById('file').files[0]
    let fd = new FormData()
    fd.append('image', file)
    fd.append('q', '能看懂吗？')
    fd.append('model', 'gpt')
    fetch('/test/stream-form', {method: 'POST', body: fd})
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
    qry, model, sid = request.form.get("q"), request.form.get("model"), request.form.get("sid")
    img = request.files.get("image")
    if img:
        if not sid:
            sid = "test01"
        _img = Image.open(io.BytesIO(img.read()))
        url = tx_cos.upload(f"{model}/{sid}/{int(time.time() * 1000)}.jpg", _img)
        qry = f"{qry}\nimg={url}"
    return _stream(qry, model, sid)
