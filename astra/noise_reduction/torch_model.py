
from pathlib import Path
import numpy as np

import torch
import tqdm

from .DTLN_model import Pytorch_DTLN_stateful


def load_torch_model(model_path: Path|str)->Pytorch_DTLN_stateful:
    model = Pytorch_DTLN_stateful()
    model_path = str(model_path.resolve()) if isinstance(model_path, Path) else model_path
    model.load_state_dict(torch.load(model_path))
    model.eval()
    return model

def denoise_torch(model: Pytorch_DTLN_stateful, audio: np.ndarray)->np.ndarray:
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

    in_state1 = torch.zeros(2, 1, 128, 2)
    in_state2 = torch.zeros(2, 1, 128, 2)

    for idx in tqdm.tqdm(range(num_blocks)):
        # shift values and write to buffer
        in_buffer[:-block_shift] = in_buffer[block_shift:]
        in_buffer[-block_shift:] = audio[idx * block_shift:(idx * block_shift) + block_shift]
        in_block = np.expand_dims(in_buffer, axis=0).astype(np.float32)
        x = torch.from_numpy(in_block)
        with torch.no_grad():
            out_block, in_state1, in_state2 = model(x, in_state1, in_state2)
        out_block = out_block.numpy()
        # shift values and write to buffer
        out_buffer[:-block_shift] = out_buffer[block_shift:]
        out_buffer[-block_shift:] = np.zeros((block_shift))
        out_buffer += np.squeeze(out_block)
        # write block to output file
        out[idx * block_shift:(idx * block_shift) + block_shift] = out_buffer[:block_shift]

    return out
