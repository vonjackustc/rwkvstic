
from rwkvstic.rwkvMaster import RWKVMaster
from rwkvstic.agnostic.agnosticRwkv import AgnostigRWKV

from rwkvstic.agnostic.backends.torch import RWKVCudaQuantOps
from rwkvstic.agnostic.agnosticRwkvLeg import LegacyRWKV


def loadPreQuantized(path, tokenizer=None):
    import torch

    weights = torch.load(
        path, **({"map_location": "cpu"} if not torch.cuda.is_available() else {}))

    # filter out the keys that are not .block
    weightsKeys = [x for x in weights.keys() if "blocks" in x]
    n_layers = 0
    for weight in weightsKeys:
        ww = weight.split("blocks.")
        ww = ww[1].split(".")
        if int(ww[0]) > n_layers:
            n_layers = int(ww[0])
        if isinstance(weights[weight], torch.Tensor) & weights[weight].dtype == torch.bfloat16:
            weights[weight] = weights[weight].to(torch.float64)

    ops = RWKVCudaQuantOps(
        preQuantized=True, embed=len(weights["blocks.0.ln2.weight"]), layers=(n_layers+1), chunksize=32, target=100, maxQuantTarget=100, useLogFix="logfix" in path, useGPU=torch.cuda.is_available(), runtimedtype=torch.float64)
    if "logfix" in path:
        model = LegacyRWKV(ops, weights)
    else:
        model = AgnostigRWKV(ops, weights)
    emptyState = ops.emptyState
    initTensor = ops.initTensor

    return RWKVMaster(model, emptyState, initTensor, ops.sample, tokenizer)
