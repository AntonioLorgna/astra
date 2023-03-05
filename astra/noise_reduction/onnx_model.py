
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import numpy as np
import tqdm, onnxruntime


@dataclass
class ModelDTLNONNX:
    interpreter: onnxruntime.InferenceSession
    model_input_names: List[str]
    model_inputs: List[onnxruntime.NodeArg]


def load_onnx_models(models_path: Tuple[Path|str]):
    models = list(models_path)
    for i, model_path in enumerate(models_path):
        model_path = str(model_path.resolve()) if isinstance(model_path, Path) else model_path
        interpreter = onnxruntime.InferenceSession(model_path)
        model_input_names = [inp.name for inp in interpreter.get_inputs()]
        # preallocate input
        model_inputs = {
            inp.name: np.zeros(
                [dim if isinstance(dim, int) else 1 for dim in inp.shape],
                dtype=np.float32)
            for inp in interpreter.get_inputs()}
        model1 = ModelDTLNONNX(interpreter, model_input_names, model_inputs)
        models[i] = model1
        # for item in model_inputs.items():
        #     print("[ model1 ] input {} , shape: {}".format(item[0], item[1].shape))
    return tuple(models)


def denoise_onnx(model1: ModelDTLNONNX, model2: ModelDTLNONNX, audio: np.ndarray)->np.ndarray:
    block_len = 512
    block_shift = 128

    # preallocate output audio
    out = np.zeros((len(audio)))
    # create buffer
    in_buffer = np.zeros((block_len), dtype=np.float32)
    out_buffer = np.zeros((block_len), dtype=np.float32)
    # calculate number of blocks
    num_blocks = (audio.shape[0] - (block_len - block_shift)) // block_shift
    # iterate over the number of blocks
    for idx in tqdm.tqdm(range(num_blocks)):
        # shift values and write to buffer
        in_buffer[:-block_shift] = in_buffer[block_shift:]
        in_buffer[-block_shift:] = audio[idx * block_shift:(idx * block_shift) + block_shift]
        in_block = np.expand_dims(in_buffer, axis=0).astype(np.float32)

        in_block_fft = np.fft.rfft(in_buffer)
        in_mag = np.abs(in_block_fft)
        in_phase = np.angle(in_block_fft)
        # reshape magnitude to input dimensions
        in_mag = np.reshape(in_mag, (1, 1, -1)).astype(np.float32)

        # set block to input
        model1.model_inputs[model1.model_input_names[0]] = in_mag
        # run calculation
        model_outputs_1 = model1.interpreter.run(None, model1.model_inputs)
        # get the output of the first block
        estimated_mag = model_outputs_1[0]

        # set out states back to input
        model1.model_inputs["h1_in"][0] = model_outputs_1[1][0]
        model1.model_inputs["c1_in"][0] = model_outputs_1[1][1]
        model1.model_inputs["h2_in"][0] = model_outputs_1[1][2]
        model1.model_inputs["c2_in"][0] = model_outputs_1[1][3]

        # calculate the ifft
        estimated_complex = estimated_mag * np.exp(1j * in_phase)
        estimated_block = np.fft.irfft(estimated_complex)
        # reshape the time domain block
        estimated_block = np.reshape(estimated_block, (1, -1, 1)).astype(np.float32)
        # set tensors to the second block
        # interpreter_2.set_tensor(input_details_1[1]['index'], states_2)
        model2.model_inputs[model2.model_input_names[0]] = estimated_block
        # run calculation
        model_outputs_2 = model2.interpreter.run(None, model2.model_inputs)
        # get output
        out_block = model_outputs_2[0]
        # set out states back to input

        model2.model_inputs["h1_in"][0] = model_outputs_2[1][0]
        model2.model_inputs["c1_in"][0] = model_outputs_2[1][1]
        model2.model_inputs["h2_in"][0] = model_outputs_2[1][2]
        model2.model_inputs["c2_in"][0] = model_outputs_2[1][3]

        # shift values and write to buffer
        out_buffer[:-block_shift] = out_buffer[block_shift:]
        out_buffer[-block_shift:] = np.zeros((block_shift))
        out_buffer += np.squeeze(out_block)

        # print(idx, np.abs(out_buffer).sum())
        # write block to output file
        out[idx * block_shift:(idx * block_shift) + block_shift] = out_buffer[:block_shift]

    return out