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


import magenta

from magenta.models.melody_rnn import melody_rnn_config_flags
from magenta.models.melody_rnn import melody_rnn_model
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.models.polyphony_rnn import polyphony_model
from magenta.models.polyphony_rnn import polyphony_sequence_generator

from magenta.protobuf import generator_pb2
from magenta.protobuf import music_pb2


import os
import time
import tempfile
import pretty_midi


DEFAULT_GENERATOR = 'polyphony_rnn'
#DEFAULT_GENERATOR = 'basic_rnn'
#DEFAULT_GENERATOR = 'attention_rnn'
#DEFAULT_GENERATOR = 'lookback_rnn'

# TODO(deck): Fix key in this dictionary to be 'polyphony_rnn', not 'polyphony'
polyphony_model.default_configs['polyphony_rnn'] = (
    polyphony_model.default_configs['polyphony'])
configs = magenta.models.melody_rnn.melody_rnn_model.default_configs
configs.update(polyphony_model.default_configs)
print 'Loading bundle', DEFAULT_GENERATOR
steps_per_quarter = 4

class GlobalGenerator:
  def __init__(self):
    self.reset_generator(DEFAULT_GENERATOR)

  def reset_generator(self, generator_name):
    config  = configs[generator_name]
    bundle_file = magenta.music.read_bundle_file(
        os.path.abspath(generator_name + '.mag'))

    if generator_name == 'polyphony_rnn':
      self.generator = (
          polyphony_sequence_generator.PolyphonyRnnSequenceGenerator(
              model=polyphony_model.PolyphonyRnnModel(config),
              details=config.details,
              steps_per_quarter=steps_per_quarter,
              bundle=bundle_file))
    else:
      self.generator = melody_rnn_sequence_generator.MelodyRnnSequenceGenerator(
          model=melody_rnn_model.MelodyRnnModel(config),
          details=config.details,
          steps_per_quarter=steps_per_quarter,
          bundle=bundle_file)


GLOBAL_GENERATOR = GlobalGenerator()

def _steps_to_seconds(steps, qpm):
  return steps * 60.0 / qpm / steps_per_quarter

def reset_generator(generator_name):
  GLOBAL_GENERATOR.reset_generator(generator_name)
  print 'New generator is ', type(GLOBAL_GENERATOR.generator)

def generate_midi(midi_data, total_seconds=10):
    primer_sequence = magenta.music.midi_io.midi_to_sequence_proto(midi_data)

    # predict the tempo
    if len(primer_sequence.notes) > 4:
        estimated_tempo = midi_data.estimate_tempo()
        if estimated_tempo > 240:
            qpm = estimated_tempo / 2
        else:
            qpm = estimated_tempo
    else:
        qpm = 120
    primer_sequence.tempos[0].qpm = qpm

    print 'Primer sequence is'
    for note in primer_sequence.notes:
      print 'Note %i %4.4f %4.4f' % (note.pitch, note.start_time, note.end_time)
    print 'With tempo', qpm

    generator_options = generator_pb2.GeneratorOptions()
    # Set the start time to begin on the next step after the last note ends.
    last_end_time = (max(n.end_time for n in primer_sequence.notes)
                     if primer_sequence.notes else 0)
    generator_options.generate_sections.add(
        start_time=last_end_time + _steps_to_seconds(1, qpm),
        end_time=total_seconds)

    # generate the output sequence
    generated_sequence = GLOBAL_GENERATOR.generator.generate(
        primer_sequence, generator_options)
    output = tempfile.NamedTemporaryFile()
    magenta.music.midi_io.sequence_proto_to_midi_file(generated_sequence, output.name)
    output.seek(0)
    return output
