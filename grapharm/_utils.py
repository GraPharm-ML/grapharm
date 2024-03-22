"""
Utility functions for GraPharm 
"""

import os
import tarfile
import pandas as pd

####################
# DATA DOWNLOADING #
####################


def download_and_extract(path="../data"):
    """
    Adapted from https://github.com/gnn4dr/DRKG/blob/master/utils/utils.py with some modifications
    """
    import shutil
    import requests

    url = "https://s3.us-west-2.amazonaws.com/dgl-data/dataset/DRKG/drkg.tar.gz"
    filename = "drkg.tar.gz"
    fn = os.path.join(path, filename)
    if os.path.exists(f"{path}/drkg.tsv"):
        return

    # Make directory in case not exisiting
    os.makedirs(path, exist_ok=True)

    opener, mode = tarfile.open, 'r:gz'
    os.makedirs(path, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(path)
    while True:
        try:
            file = opener(filename, mode)
            try:
                file.extractall()
            finally:
                file.close()
            break
        except Exception:
            f_remote = requests.get(url, stream=True)
            sz = f_remote.headers.get('content-length')
            assert f_remote.status_code == 200, 'fail to open {}'.format(url)
            with open(filename, 'wb') as writer:
                for chunk in f_remote.iter_content(chunk_size=1024*1024):
                    writer.write(chunk)
            print('Downloadwgkkgk finished. Unzipping the file...')

    print("Delete zip file")
    os.remove(os.path.join(path, "drkg.tar.gz"))
    os.chdir(cwd)


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


def load_edge_colors():
    """Load dictionary of edge colors

    Returns:
        dict: edge colors
    """
    import json

    with open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "edge_colors.json"
    )) as f:
        edge_colors = json.load(f)

    return edge_colors


def tsv2networkx(drkg, re_gloss):

    import networkx as nx

    interaction_types = re_gloss.set_index(
        "Relation-name").to_dict()["Interaction-type"]
    edge_colors = load_edge_colors()
    # Entities
    entities = list(set(drkg["h"].tolist() + drkg["t"].tolist()))
    entity_df = pd.DataFrame({"name": entities})
    entity_df["type"] = entity_df["name"].str.split("::", expand=True)[0]

    g_nx = nx.Graph()

    for entity_type in entity_df["type"].unique():
        entities = entity_df[entity_df["type"] == entity_type]["name"].tolist()
        g_nx.add_nodes_from(entities, entity=entity_type,
                            color=node_colors[entity_type])

    for link_type in drkg["r"].unique():
        links = drkg[drkg["r"] == link_type][["h", "t"]
                                             ].itertuples(index=False, name=None)
        g_nx.add_edges_from(
            links, label=interaction_types[link_type], color=edge_colors[link_type], dashes=False)

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
