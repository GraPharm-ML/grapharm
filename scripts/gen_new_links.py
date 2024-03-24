import os
import sys
import json
import argparse
import pandas as pd

import torch
import torch_geometric as pyg
from torch import optim
from torch import nn
from torch.nn import functional as F
from torch import distributed as dist
from torch.utils import data as torch_data
from torch_geometric.data import Data

sys.path.append(".")
from ultra import tasks, util
from ultra.models import Ultra

datadir = "data"
inv_entity_vocab = json.load(open(f"{datadir}/hetionet/inv_entity_vocab.json", "r"))
inv_rel_vocab = json.load(open(f"{datadir}/hetionet/inv_rel_vocab.json", "r"))
edge_type_df = pd.read_csv(f"{datadir}/metaedges.tsv", sep="\t")

ckpt_choices = ["ultra_50g.pth",
                "ultra50g_hetionet50.pth",
                "ultra50g_hetionet100.pth",
                "ultra50g_hetionet70.pth"]
dataset_choices = ["Hetionet", "HetionetA"]

parser = argparse.ArgumentParser()
parser.add_argument("-ckpt", choices=ckpt_choices, default="ultra_50g.pth",
                    help="name of checkpoint, choose in this list: {}".format(ckpt_choices))
parser.add_argument("-dataset", choices=dataset_choices,
                    help="name of dataset")
parser.add_argument("-gpus", default="null",
                    help="specify gpus if available")

args = parser.parse_args()

rootdir = os.path.abspath(".")
cfg_file = f"{rootdir}/assets/config/transductive/inference.yaml"
savepath = "{}/outputs/{}-{}.csv".format(rootdir,
                                         args.ckpt.split(".")[0],
                                         args.dataset)

os.makedirs(os.path.dirname(savepath), exist_ok=True)

vars = dict(bpe=None,
            ckpt='{}/assets/ckpts/{}'.format(rootdir, args.ckpt),
            dataset=args.dataset,
            epochs=0,
            gpus=args.gpus)
cfg = util.load_config(cfg_file, vars)

task_name = cfg.task["name"]
dataset = util.build_dataset(cfg)
device = util.get_device(cfg)

train_data, valid_data, test_data = dataset[0], dataset[1], dataset[2]
train_data = train_data.to(device)
valid_data = valid_data.to(device)
test_data = test_data.to(device)

model = Ultra(
    rel_model_cfg=cfg.model.relation_model,entity_model_cfg=cfg.model.entity_model,
    )

if "checkpoint" in cfg and cfg.checkpoint is not None:
    state = torch.load(cfg.checkpoint, map_location="cpu")
    model.load_state_dict(state["model"])

model = model.to(device)

filtered_data = Data(edge_index=dataset._data.target_edge_index, edge_type=dataset._data.target_edge_type, num_nodes=dataset[0].num_nodes)
val_filtered_data = test_filtered_data = filtered_data

val_filtered_data = val_filtered_data.to(device)
test_filtered_data = test_filtered_data.to(device)

world_size = util.get_world_size()
rank = util.get_rank()

test_triplets = torch.cat([test_data.target_edge_index, test_data.target_edge_type.unsqueeze(0)]).t()

sampler = torch_data.DistributedSampler(test_triplets, world_size, rank)
test_loader = torch_data.DataLoader(test_triplets, cfg.train.batch_size, sampler=sampler)

model.eval()
rankings = []
num_negatives = []

entity_vocab = dict(zip(inv_entity_vocab.values(), inv_entity_vocab.keys()))
rel_vocab = dict(zip(inv_rel_vocab.values(), inv_rel_vocab.keys()))

df = pd.DataFrame(columns=["source", "metaedge", "target", "source_pred", "target_pred"])

for i, batch in enumerate(test_loader):
    print(f"Predict batch {i}")
    t_batch, h_batch = tasks.all_negative(test_data, batch)
    t_pred = model(test_data, t_batch)
    h_pred = model(test_data, h_batch)
    
    t_mask, h_mask = tasks.strict_negative_mask(test_data, batch)
    pos_h_index, pos_t_index, pos_r_index = batch.t()
    
    pos_t_pred_index = t_pred.argmax(axis=1).cpu().numpy().tolist()
    pos_h_pred_index = h_pred.argmax(axis=1).cpu().numpy().tolist()
    
    hs = [entity_vocab[x] for x in pos_h_index.cpu().numpy()]
    ts = [entity_vocab[x] for x in pos_t_index.cpu().numpy()]
    rs = [rel_vocab[x] for x in pos_r_index.cpu().numpy()]
    
    hs_pred = [entity_vocab[x] for x in pos_h_pred_index]
    ts_pred = [entity_vocab[x] for x in pos_t_pred_index]

    df_batch = pd.DataFrame({"source": hs, "metaedge": rs, "target": ts,
                             "source_pred": hs_pred, "target_pred": ts_pred})
    df = pd.concat([df, df_batch], ignore_index=True)
    df.to_csv(savepath, index=False)