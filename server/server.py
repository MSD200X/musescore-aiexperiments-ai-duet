#
# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from predict import generate_midi, reset_generator
import os
from flask import send_file, request
import pretty_midi
import sys
if sys.version_info.major <= 2:
    from cStringIO import StringIO
else:
    from io import StringIO
import time
import json

from flask import Flask
app = Flask(__name__, static_url_path='', static_folder=os.path.abspath('../static'))


@app.route('/predict', methods=['POST'])
def predict():
    now = time.time()
    values = json.loads(request.data)

    midi_data = pretty_midi.PrettyMIDI(StringIO(''.join(chr(v) for v in values)))

    print 'Input midi_data'
    for inst in midi_data.instruments:
      print inst
      for n in inst.notes:
        print n

    duration = float(request.args.get('duration'))
    ret_midi = generate_midi(midi_data, duration)

    return send_file(ret_midi, attachment_filename='return.mid',
        mimetype='audio/midi', as_attachment=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    model = request.args.get('model', None)
    if model:
      reset_generator(model)
      print 'Reset generator to', model

    return send_file('../static/index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
