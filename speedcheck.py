import tflite_runtime.interpreter as tflite
import numpy as np
import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m','--model', type=str,required=True, dest='model')
parser.add_argument('-s','--steps', type=int,required=True, dest='steps')
args = parser.parse_args()

interpreter = tflite.Interpreter(model_path=args.model)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()[0]
target_size = input_details['shape']
input_idx = input_details['index']
output_idx = interpreter.get_output_details()[0]['index']


for _ in tqdm.trange(args.steps):

    interpreter.set_tensor(input_idx, np.ones(target_size,np.uint8))
    interpreter.invoke()
    a = interpreter.get_tensor(output_idx)