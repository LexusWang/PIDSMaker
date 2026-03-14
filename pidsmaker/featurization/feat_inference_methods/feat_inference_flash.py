import math
import os
import pickle

import numpy as np
import torch
from gensim.models import Word2Vec

from pidsmaker.featurization.feat_training_methods.feat_training_flash import get_node2corpus
from pidsmaker.utils.utils import log, log_start, log_tqdm


def infer(document, w2vmodel, encoder):
    """
    Each node is associated to a `document` which is the list of (msg => edge type => msg)
    involving this node.
    We get the embedding of each word inside this document and we do the mean of all embeddings.
    OOV words are simply ignored.
    """
    word_embeddings = [w2vmodel.wv[word] for word in document if word in w2vmodel.wv]

    embedding_dim = w2vmodel.vector_size

    if not word_embeddings:
        return np.zeros(embedding_dim)

    word_embeddings_array = np.array(word_embeddings)

    output_embedding = torch.tensor(word_embeddings_array, dtype=torch.float)
    if len(document) < 100000:
        output_embedding = encoder.embed(output_embedding)

    output_embedding = output_embedding.detach().cpu().numpy()
    return np.mean(output_embedding, axis=0)


class PositionalEncoder:
    def __init__(self, d_model, max_len=100000):
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        self.pe = torch.zeros(max_len, d_model)
        self.pe[:, 0::2] = torch.sin(position * div_term)
        self.pe[:, 1::2] = torch.cos(position * div_term)

    def embed(self, x):
        return x + self.pe[: x.size(0)]


def main(cfg):
    log_start(__file__)

    trained_w2v_dir = cfg.featurization.feat_training._model_dir
    cache_path = os.path.join(trained_w2v_dir, "indexid2vec.pkl")

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                indexid2vec = pickle.load(f)

            # For PROVATTACK attack variants the cache was built on train/val only (base dataset).
            # Compute embeddings for any test-split nodes not yet in the cache (e.g. graph_65).
            node2corpus_test = get_node2corpus(cfg, splits=["test"])
            new_nodes = {
                nid: corpus for nid, corpus in node2corpus_test.items() if nid not in indexid2vec
            }
            if new_nodes:
                w2vmodel = Word2Vec.load(
                    os.path.join(trained_w2v_dir, "word2vec_model_final.model")
                )
                w2v_vector_size = cfg.featurization.feat_training.emb_dim
                encoder = PositionalEncoder(w2v_vector_size)
                for indexid, corpus in log_tqdm(new_nodes.items(), desc="Embedding new nodes"):
                    indexid2vec[indexid] = infer(corpus, w2vmodel, encoder)

            return indexid2vec
        except (EOFError, pickle.UnpicklingError) as e:
            log(f"WARNING: Corrupt cache at {cache_path} ({e}). Deleting and recomputing.")
            os.remove(cache_path)

    w2vmodel = Word2Vec.load(os.path.join(trained_w2v_dir, "word2vec_model_final.model"))
    w2v_vector_size = cfg.featurization.feat_training.emb_dim

    node2corpus = get_node2corpus(cfg, splits=["train", "val", "test"])
    indexid2vec = {}
    for indexid, corpus in log_tqdm(node2corpus.items(), desc="Embeding all nodes in the dataset"):
        indexid2vec[indexid] = infer(corpus, w2vmodel, PositionalEncoder(w2v_vector_size))

    with open(cache_path, "wb") as f:
        pickle.dump(indexid2vec, f)

    return indexid2vec
