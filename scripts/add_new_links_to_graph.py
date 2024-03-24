import warnings
warnings.filterwarnings("ignore")

import os
import argparse
import pandas as pd

def print_data_stats(df):
    print("Edge number: {}".format(len(df)))
    nodes = list(set(df["source"].tolist() + df["target"].to_list()))
    df["source_type"] = df["source"].str.split("::", expand=True)[0]
    df["target_type"] = df["target"].str.split("::", expand=True)[0]
    print("Node number: {}".format(len(nodes)))
    node_types = list(set(df["source_type"].tolist() + df["target_type"].to_list()))
    print("Node type number: {}".format(len(node_types)))

parser = argparse.ArgumentParser()
parser.add_argument("-result_name",help="prediction file name")
parser.add_argument("-savename", help="path to save new predictions")

args = parser.add_argument()


full_df = pd.read_csv("data/hetionet-v1.0-edges.sif", sep="\t")
pred_df = pd.read_csv("outputs/{}".format(args.result_name))

print("GRAPH STATS")
print_data_stats(full_df.copy())

new_links_q1 = pred_df[["source", "metaedge", "target_pred"]]
new_links_q1.rename({"target_pred": "target"}, axis=1, inplace=True)
new_links_q2 = pred_df[["source_pred", "metaedge", "target"]]
new_links_q2.rename({"source_pred": "source"}, axis=1, inplace=True)
new_links = pd.concat([new_links_q1, new_links_q2], ignore_index=True)
print("Before removing duplications: {}".format(len(new_links)))
new_links.drop_duplicates(inplace=True, keep="first")
new_links.reset_index(inplace=True, drop=True)
print("Number of links recontructed from ULTRA: {}".format(len(new_links)))

# Remove links from original graph
new_links["key"] = new_links["source"] + "-" + new_links["metaedge"] + "-" + new_links["target"]
df = test_df.copy()
df["key"] = df["source"] + "-" + df["metaedge"] + "-" + df["target"]

overlaps = list(set(new_links["key"].tolist()) & set(df["key"].tolist()))
print("Overlap: {}".format(len(overlaps)))
new_links = new_links[~new_links["key"].isin(overlaps)]
print("New links: {}".format(len(new_links)))

new_links[["source", "metaedge", "target"]].to_csv("./data/{}".format(args.savename), 
                                                   index=False)
