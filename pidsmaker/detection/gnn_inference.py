import os

import torch

from pidsmaker.tasks.batching import get_preprocessed_graphs
from pidsmaker.factory import build_model
from pidsmaker.utils.utils import get_device, log, log_start, set_seed

from .training_methods import inference_loop


def main(cfg):
    set_seed(cfg)
    log_start(__file__)

    device = get_device(cfg)
    train_data, _, test_data, max_node_num = get_preprocessed_graphs(cfg)

    models_dir = cfg.training._trained_models_dir
    model_files = sorted(
        f for f in os.listdir(models_dir) if f.endswith(".pt")
    )

    edge_losses_dir = cfg.gnn_inference._edge_losses_dir

    for model_file in model_files:
        epoch = int(model_file.replace("model_epoch_", "").replace(".pt", ""))
        log(f"Running test inference for model_epoch_{epoch}...")

        model = build_model(
            data_sample=train_data[0][0],
            device=device,
            cfg=cfg,
            max_node_num=max_node_num,
        )
        state_dict = torch.load(
            os.path.join(models_dir, model_file), map_location=device
        )
        model.load_state_dict(state_dict)
        model.reset_state()

        inference_loop.main(
            cfg=cfg,
            model=model,
            val_data=[],
            test_data=test_data,
            epoch=epoch,
            split="test",
            edge_losses_dir=edge_losses_dir,
        )
