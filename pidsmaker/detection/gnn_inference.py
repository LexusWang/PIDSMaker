import os

import torch

from pidsmaker.detection.graph_preprocessing import get_preprocessed_graphs
from pidsmaker.factory import build_model
from pidsmaker.utils.utils import get_device, log, log_start, set_seed

from .training_methods import inference_loop


def main(cfg):
    set_seed(cfg)
    log_start(__file__)

    device = get_device(cfg)
    train_data, _, test_data, max_node_num = get_preprocessed_graphs(cfg)

    models_dir = cfg.detection.gnn_training._trained_models_dir
    model_files = sorted(
        f for f in os.listdir(models_dir) if f.endswith(".pt")
    )
    model_files = [model_files[-1]]  # only run inference on the last saved model

    edge_losses_dir = cfg.detection.gnn_inference._edge_losses_dir

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
        # Remove memory buffers whose shape may differ when the attack dataset has more
        # nodes than the training dataset (e.g. training_full vs training_full_phobosransomware).
        # These buffers are zeroed by reset_state() immediately after loading anyway.
        model_state = model.state_dict()
        filtered = {
            k: v for k, v in state_dict.items()
            if k not in model_state or v.shape == model_state[k].shape
        }
        model.load_state_dict(filtered, strict=False)
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
