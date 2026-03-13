import os

import numpy as np
import torch

from pidsmaker.config import update_cfg_for_multi_dataset
from pidsmaker.utils.data_utils import CollatableTemporalData
from pidsmaker.utils.dataset_utils import get_node_map, get_rel2id
from pidsmaker.utils.utils import (
    gen_relation_onehot,
    get_multi_datasets,
    get_split_to_files,
    log_tqdm,
)

from .feat_inference_methods import (
    feat_inference_alacarte,
    feat_inference_doc2vec,
    feat_inference_fasttext,
    feat_inference_flash,
    feat_inference_HFH,
    feat_inference_TRW,
    feat_inference_word2vec,
)


def feat_inference(indexid2vec, etype2oh, ntype2oh, sorted_paths, out_dir, cfg):
    # Pre-convert onehot dicts to numpy to avoid creating torch tensors per edge.
    # gen_relation_onehot stores bidirectional entries (str→tensor AND tensor→str),
    # so filter to string keys only.
    ntype2oh_np = {k: v.numpy() for k, v in ntype2oh.items() if isinstance(k, str)}
    etype2oh_np = {k: v.numpy() for k, v in etype2oh.items() if isinstance(k, str)}
    zero_etype_np = np.zeros_like(next(iter(etype2oh_np.values())))

    for path in log_tqdm(sorted_paths, desc="Computing edge embeddings"):
        graph = torch.load(path)
        sorted_edges = list(graph.edges(data=True, keys=True))

        n_edges = len(sorted_edges)
        src = np.empty(n_edges, dtype=np.int64)
        dst = np.empty(n_edges, dtype=np.int64)
        t = np.empty(n_edges, dtype=np.int64)
        y = np.empty(n_edges, dtype=np.int64)
        msg = []

        for i, (u, v, k, attr) in enumerate(sorted_edges):
            src[i] = int(u)
            dst[i] = int(v)
            t[i] = int(attr["time"])
            y[i] = int(attr.get("y", 0))

            # If the graph structure has been changed in transformation, we may loose
            # the edge label
            edge_label = etype2oh_np[attr["label"]] if "label" in attr else zero_etype_np

            # Only types
            if indexid2vec is None:
                msg.append(
                    np.concatenate(
                        [
                            ntype2oh_np[graph.nodes[u]["node_type"]],
                            edge_label,
                            ntype2oh_np[graph.nodes[v]["node_type"]],
                        ]
                    )
                )

            # Types + node embeddings
            else:
                msg.append(
                    np.concatenate(
                        [
                            ntype2oh_np[graph.nodes[u]["node_type"]],
                            indexid2vec[u],
                            edge_label,
                            ntype2oh_np[graph.nodes[v]["node_type"]],
                            indexid2vec[v],
                        ]
                    )
                )

        data = CollatableTemporalData(
            src=torch.from_numpy(src),
            dst=torch.from_numpy(dst),
            t=torch.from_numpy(t),
            msg=torch.from_numpy(np.vstack(msg)).to(torch.float),
            y=torch.from_numpy(y),
        )

        os.makedirs(out_dir, exist_ok=True)
        file = path.split("/")[-1]
        torch.save(data, os.path.join(out_dir, f"{file}.TemporalData.simple"))


def get_indexid2vec(cfg):
    method = cfg.featurization.feat_training.used_method.strip()
    if method in ["only_type", "only_ones"]:
        return None
    if method == "alacarte":
        return feat_inference_alacarte.main(cfg)
    if method == "doc2vec":
        return feat_inference_doc2vec.main(cfg)
    if method == "hierarchical_hashing":
        return feat_inference_HFH.main(cfg)
    if method == "word2vec":
        return feat_inference_word2vec.main(cfg)
    if method == "temporal_rw":
        return feat_inference_TRW.main(cfg)
    if method == "flash":
        return feat_inference_flash.main(cfg)
    if method == "fasttext":
        return feat_inference_fasttext.main(cfg)

    raise ValueError(f"Invalid node embedding method {method}")


def main_from_config(cfg):
    rel2id = get_rel2id(cfg)
    ntype2id = get_node_map()
    etype2onehot = gen_relation_onehot(rel2id=rel2id)
    ntype2onehot = gen_relation_onehot(rel2id=ntype2id)

    base_dir = cfg.preprocessing.transformation._graphs_dir
    split_to_files = get_split_to_files(cfg, base_dir)

    # Here we get a mapping {node_id => embedding vector}
    indexid2vec = get_indexid2vec(cfg)

    base_edge_embeds_dir = getattr(cfg.featurization.feat_inference, "_base_edge_embeds_dir", "")

    # Create edges for Train, Val, Test sets
    for split, sorted_paths in split_to_files.items():
        out_dir = os.path.join(cfg.featurization.feat_inference._edge_embeds_dir, f"{split}/")
        os.makedirs(out_dir, exist_ok=True)

        paths_to_compute = []
        for path in sorted_paths:
            file = path.split("/")[-1]
            out_file = os.path.join(out_dir, f"{file}.TemporalData.simple")
            if base_edge_embeds_dir:
                base_file = os.path.join(
                    base_edge_embeds_dir, split, f"{file}.TemporalData.simple"
                )
                if os.path.exists(base_file) and not os.path.exists(out_file):
                    os.symlink(base_file, out_file)
                    continue
            if not os.path.exists(out_file):
                paths_to_compute.append(path)

        if paths_to_compute:
            feat_inference(
                indexid2vec=indexid2vec,
                etype2oh=etype2onehot,
                ntype2oh=ntype2onehot,
                sorted_paths=paths_to_compute,
                out_dir=out_dir,
                cfg=cfg,
            )


def main(cfg):
    multi_dataset_training = cfg.detection.graph_preprocessing.multi_dataset_training
    if not multi_dataset_training:
        main_from_config(cfg)

    # Multi-dataset mode
    else:
        trained_model_dir = cfg.featurization.feat_training._model_dir
        multi_datasets = get_multi_datasets(cfg)
        for dataset in multi_datasets:
            updated_cfg, should_restart = update_cfg_for_multi_dataset(cfg, dataset)
            updated_cfg.featurization.feat_training._model_dir = trained_model_dir

            if should_restart["feat_inference"]:
                main_from_config(updated_cfg)
