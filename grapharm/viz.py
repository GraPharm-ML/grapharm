"""
Visualization
"""

import os
import pandas as pd

import networkx as nx

from IPython.display import display, Javascript, HTML, clear_output, IFrame
from ipywidgets import interact, interactive, fixed, interact_manual, AppLayout, GridspecLayout
import ipywidgets as widgets


#######################
# GRAPH VISUALIZATION #
#######################

# Aesthetics
def get_logo(logo_path):
    """Get GraPharm logo

    Args:
        logo_path (str): path to logo

    Returns:
        widgets.Image: Logo
    """
    im = widgets.Image(
        value=open(logo_path, "rb").read(),
        format='png',
        width="150px",
        height="150px",
        ha="right",
        va="center",
    )
    
    return im

# header
gra = '<font color="#012C39" face="sans-serif" size="12">Gra</font>'
pharm = '<font color="#72BD69" face="sans-serif" size="12">Pharm</font>'
lines = '<font color="#616161" face="sans-serif">{}</font>'.format("-"*53)
slogan = ('<font color="#012C39" face="sans-serif">Gra</font>' +
          '<font color="#40B6CB" face="sans-serif">ph Neural Networks for discovery of </font>' +
          '<font color="#72BD69" face="sans-serif">Pharm</font>' +
          '<font color="#40B6CB" face="sans-serif">aceutical compounds</font>'
          )
header = widgets.HTML(f'<br><b>{gra}{pharm}<b><br>{lines}<br>{slogan}',
                      layout=widgets.Layout(height='auto'))

# Setting for Pyvis
pyvis_opts = """
var options = {
  "nodes": {
    "font": {
      "face": "verdana"
    },
    "size": 15
  },
  "edges": {
    "color": {
      "inherit": true
    },
    "font": {
      "size": 10,
      "face": "verdana"
    },
    "smooth": false,
    "width": 2
  },
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -2000,
      "centralGravity": 0,
      "springLength": 200
    },
    "minVelocity": 0.25
  }
}
"""

def networkx2pyvis(G, **options):
    """From networkx to pyvis graph

    Args:
        G (nx graph): networkx graph
        node_df (pd.DataFrame): df load from this file hetionet-v1.0-nodes.tsv

    Returns:
        pyvis graph: corresponding pyvis graph
    """
  
    from pyvis.network import Network
    
    H = Network(directed=True, **options)

    # Add nodes
    for node, data in G.nodes(data=True):
        H.add_node(node,
                   font={"color": data['color']},
                   **data)

    # Add edges
    for node1, node2, data in G.edges(data=True):
        H.add_edge(node1, node2, **data)

    return H


# Subgraphs (for EDA)
def select_entities_for_display(drkg, upper_cutoff=25, lower_cutoff=15, num=5):
    all_entities = pd.concat([drkg["h"], drkg["t"]], ignore_index=True).value_counts()
    few_connection_entities = all_entities[(all_entities <= upper_cutoff) & (all_entities > lower_cutoff)]

    few_connection_entities = pd.DataFrame({
        "entity_name": few_connection_entities.index,
        "no_links": few_connection_entities.values
    })

    few_connection_entities["entity_type"] = few_connection_entities["entity_name"].str.split("::", expand=True)[0]

    print("There are {} entities with [{}, {}] connections, belonging to {} entity types".format(
        len(few_connection_entities),
        lower_cutoff,
        upper_cutoff,
        len(few_connection_entities["entity_type"].unique())
    ))
    print("-"*50)
    print("Entity type statistics:")
    print("---")
    print(few_connection_entities["entity_type"].value_counts())
    
    num = min([num, few_connection_entities["no_links"].min()])
    selected_entities = []
    for entity_type in few_connection_entities["entity_type"].unique():
        selected_entities += few_connection_entities[few_connection_entities["entity_type"]==entity_type]["entity_name"].tolist()[:num]

    selected_entities = few_connection_entities[few_connection_entities["entity_name"].isin(selected_entities)].reset_index(drop=True)
    print("-"*50)
    print(f"For every entity type, choose {num} entities")
    print("---")
    
    return selected_entities


def draw_subgraph_widget(G, selected_entities, drkg, outdir, logo_path):
    
    im = get_logo(logo_path)

    def draw_entity_subgraph(graph, entity_name, outdir):
        if entity_name != "--Select":
            entity = drkg[(drkg["h"] == entity_name) |
                          (drkg["t"] == entity_name)]
            nodes = list(set(entity["h"].tolist() + entity["t"].tolist()))
            print("Subgraph of {} has {} nodes".format(entity_name, len(nodes)))

            entity_graph = graph.subgraph(nodes)

            options = {
                "notebook": True,
                "height": "750px",
                "width": "100%",
                "cdn_resources": "in_line"
            }

            H = networkx2pyvis(entity_graph, **options)
            H.set_options(pyvis_opts)
            H.show(f"{outdir}/entity_subgraph.html")

            display(
                IFrame(src=f"{outdir}/entity_subgraph.html", width=1000, height=750))

    # Inputs
    entity_names = ["--Select"]
    entity_type = widgets.Dropdown(options=["--Select"] + list(selected_entities["entity_type"].unique()),
                                   description="Entity type",
                                   layout={"width": "auto"},
                                   disabled=False)
    entity_name = widgets.Dropdown(options=entity_names,
                                   description="Entity name: ",
                                   layout={"width": "auto"},
                                   disabled=False)

    # Changes
    def on_change_entity_type(change):
        if change["type"] == "change" and change["name"] == "value":
            chosen_entity_type = change["new"]
            if chosen_entity_type == "--Select":
                entity_names = ["--Select"]
            else:
                entity_name.options = selected_entities[selected_entities["entity_type"]
                                                        == chosen_entity_type]["entity_name"].tolist()

    # Layouts
    grid = GridspecLayout(4, 4, height="200px")
    grid[0, 0] = entity_type
    grid[1:, :] = widgets.HBox([im, header])
    display(grid)

    entity_type.observe(on_change_entity_type)
    interact(draw_entity_subgraph, graph=fixed(G), entity_name=entity_name, outdir=fixed(outdir))
    

def draw_connected_components(G, connected_components, outdir):
    subgraph_num_nodes = {}
    for i, subgraph in enumerate(connected_components):
        subgraph_num_nodes[i] = subgraph.number_of_nodes()
        
    subgraph_idx = [k for k in subgraph_num_nodes.keys() 
                if (subgraph_num_nodes[k] >= 10) & (subgraph_num_nodes[k] < 30)]

    nodes = []
    for id in subgraph_idx:
        subgraph = connected_components[id]
        nodes += list(subgraph.nodes.keys())
        
    print("Number of nodes to display: {}".format(len(nodes)))
    subgraph = G.subgraph(nodes=nodes)
    options = {
        "notebook": True,
        "height": "750px",
        "width": "100%",
        "cdn_resources": "in_line"
                } 
    H = networkx2pyvis(subgraph, **options)
    H.set_options(pyvis_opts)
    H.show(f"{outdir}/subgraph.html")
    display(IFrame(src=f"{outdir}/subgraph.html", width=1000, height=750))
    