"""
Utility functions for GraPharm 
"""

import os
import tarfile
import pandas as pd

###############
# DATA LOADER #
###############

# Constants
node_colors = {
    "Biological Process": "#1D8348",
    "Molecular Function": "#F0A30A",
    "Tax": "#B9770E",
    "Atc": "#F4B1AE",
    "Compound": "#1BA1E2",
    "Pharmacologic Class": "#BAC8D3",
    "Symptom": "#E3C800",
    "Cellular Component": "#FFF2CC",
    "Side Effect": "#424949",
    "Disease": "#512E5F",
    "Gene": "#1B4F72",
    "Anatomy": "#F8CECC",
    "Pathway": "#60A917"
}

edge_colors = {
    "downregulates": "#E74C3C",
    "expresses": "#1F618D",
    "upregulates": "#229954",
    "binds": "#6C3483",
    "causes": "#BA4A00",
    "palliates": "#9FE2BF",
    "resembles": "#2E86C1",
    "treats": "#40E0D0",
    "associates": "#FF7F50",
    "localizes": "#CCCCFF",
    "presents": "#DFFF00",
    "covaries": "#27AE60",
    "interacts": "#A04000",
    "participates": "#1F618D",
    "regulates": "#138D75",
    "includes": "#4D5656"
}


def tsv2networkx(edge_df, node_df, edge_type_df):

    import networkx as nx

    g_nx = nx.Graph()

    # nodes (add node ids)
    node_name_dict = node_df.set_index("id").to_dict()["name"]
    node_type_dict = node_df.set_index("id").to_dict()["kind"]
    for node in node_df["id"].tolist():
        node_type = node_type_dict[node]
        g_nx.add_node(node,
                      label=node_name_dict[node],
                      entity=node_type,
                      color=node_colors[node_type])

    # edges
    edge_type_df["edge_type"] = edge_type_df["metaedge"].str.split(
        " - ", expand=True)[1].fillna("regulates")

    link_dict = edge_type_df.set_index("abbreviation").to_dict()["edge_type"]
    for abrv in edge_type_df["abbreviation"].unique():
        links = edge_df[edge_df["metaedge"] == abrv][[
            "source", "target"]].itertuples(index=False, name=None)
        link_type = link_dict[abrv]
        g_nx.add_edges_from(links,
                            label=link_type,
                            color=edge_colors[link_type],
                            dashes=False)

    return g_nx


def print_graph_stats(G, drkg, connected_components=None):

    import networkx as nx

    if connected_components is None:
        connected_components = list((G.subgraph(c).copy()
                                    for c in nx.connected_components(G)))

    print("Number of nodes: {}".format(G.number_of_nodes()))
    entities = list(set(drkg["h"].tolist() + drkg["t"].tolist()))
    print("Number of node types: {}".format(len(entities)))
    print("Number of edges: {}".format(G.number_of_edges()))
    print("Number of edge types: {}".format(len(drkg["r"].unique())))
    print("Average edges per node: {}".format(
        G.number_of_edges()/G.number_of_nodes()))
    print("Number of subgraphs: {}".format(len(connected_components)))

    subgraph_num_nodes = {}
    for i, subgraph in enumerate(connected_components):
        subgraph_num_nodes[i] = subgraph.number_of_nodes()

    id = max(subgraph_num_nodes, key=subgraph_num_nodes.get)
    subgraph = connected_components[id]
    nodes = list(subgraph.nodes)
    entity_types = set([n.split("::")[0] for n in nodes])
    print("The largest subgraph has {} nodes ({} types) and {} edges.".format(
        subgraph.number_of_nodes(),
        len(entity_types),
        subgraph.number_of_edges()
    ))
    id = sorted(((v, k) for k, v in subgraph_num_nodes.items()))[-2][1]
    subgraph = connected_components[id]
    print("The second largest subgraph has {} nodes and {} edges.".format(
        subgraph.number_of_nodes(),
        subgraph.number_of_edges()
    ))
    print("Number of subgraphs with less than 10 nodes: {}".format(
        sum(value < 10 for value in subgraph_num_nodes.values())
    ))
