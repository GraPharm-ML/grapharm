import streamlit as st
import pandas as pd
from PIL import Image 
import networkx as nx
import os
import streamlit.components.v1 as components
import requests
from io import BytesIO
import random
from pyvis.network import Network
from datetime import datetime
# Print the current date and time
print(datetime.now())
st.set_page_config(layout="wide")
# Create a placeholder

@st.cache_data
def logo():
    image = Image.open("assets/Logo_hori@33.33x.png")
    st.image(image, use_column_width=True)
    st.title("A Graph-based AI Platform to Uncover Novel Pharmacological Links")
    st.markdown("[For further details, visit our website.](https://grapharm-ml.github.io/)")
logo()
placeholder = st.empty()
# Write to the placeholder
placeholder.write("Loading data...")
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

@st.cache_data
def import_data():
    dir = "data/"  # Replace with the base dir of your raw files on GitHub
    node_df = pd.read_csv(f"{dir}hetionet-v1.0-nodes.tsv", sep="\t")
    edge_type_df = pd.read_csv(f"{dir}metaedges.tsv", sep="\t")
    edge_df = pd.read_csv(f"{dir}hetionet-v1.0-edges.sif", sep="\t")
    new_links = pd.read_csv(f"{dir}new_links_v0.csv", sep=",")
    return node_df, edge_type_df, edge_df,new_links
node_df, edge_type_df, edge_df,new_links = import_data()
# Clear the placeholder
placeholder.empty()


@st.cache_data
def extract_entities_name(entities):
    _ = entities["name"].tolist()
    entities_names = sorted(list(set(_)))
    return entities_names
entities_names = extract_entities_name(node_df)

def extract_edge_types(edge_colors):
    edge_types = edge_colors.keys()
    return edge_types
edge_types = extract_edge_types(edge_colors)



st.sidebar.markdown("## Node Types")
for node_type, color in node_colors.items():
    st.sidebar.markdown(f'<div style="display: inline-block; vertical-align: middle; margin-right: 10px; width: 20px; height: 20px; background-color: {color};"></div> {node_type}', unsafe_allow_html=True)
st.sidebar.markdown("## Relation Types")
for edge_type, color in edge_colors.items():
    st.sidebar.markdown(f'<div style="display: inline-block; vertical-align: middle; margin-right: 10px; width: 20px; height: 20px; background-color: {color};"></div> {edge_type}', unsafe_allow_html=True)



        
@st.cache_data
def tsv2networkx(edge_df, node_df, edge_type_df,new_links=None):

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
        # new edges if available
    if new_links is not None:
        for abrv in new_links["metaedge"].unique():
            links = new_links[new_links["metaedge"]==abrv][[
                "source", "target"]].itertuples(index=False, name=None)
            link_type = link_dict[abrv]
            g_nx.add_edges_from(links,
                                label=link_type,
                                color=edge_colors[link_type],
                                dashes=True)

    return g_nx
g = tsv2networkx(edge_df,node_df, edge_type_df,new_links)

def select_entities_for_display(network,edge_df,node_df,selected_entities,
                                selected_edges,prediction=False):
        # Create a subgraph with the selected entities and all entities connected to them
    list_entities_id = []
    for entity in selected_entities:
        entity =node_df.loc[node_df['name'] == entity, 'id'].values[0]
        # entity = edge_df[(edge_df["source"] == entity) |
        #                 (edge_df["target"] == entity)]
        list_entities_id.append(entity)
    nodes = list(set(list_entities_id))
    entity_graph = network.__class__()
    #edges_of_interest = [(u, v,data) for u, v,data in network.edges(data=True) if u in nodes or v in nodes]
    for source, target, data in network.edges(nodes, data=True):
        if network.nodes[source] and network.nodes[target]:
            entity_graph.add_edge(source, target, **data)
            entity_graph.add_node(source, **network.nodes[source])
            entity_graph.add_node(target, **network.nodes[target])  
    # Create a subgraph with the selected entities and all entities connected to them
    #filter out the edge by graph
    
    edge_filter_graph = entity_graph.__class__()
    for source, target, data in entity_graph.edges(data=True):
        # add prediction label to the edge
        if data.get('dashes') == True:
            data.update({'prediction':"yes"})
        # add the edge to the filtered graph if it is in the selected edges
        if data.get('label') in selected_edges:
            edge_filter_graph.add_edge(source, target, **data)
            edge_filter_graph.add_node(source, **entity_graph.nodes[source])
            edge_filter_graph.add_node(target, **entity_graph.nodes[target])

       
    entity_graph = edge_filter_graph 
    #plot only the predicted edges if checked
    if prediction == True:
        prediction_only_graph = entity_graph.__class__()
        for source, target, data in edge_filter_graph.edges(data=True):
            if data.get('dashes') == True:
                prediction_only_graph.add_edge(source, target, **data)
                prediction_only_graph.add_node(source, **entity_graph.nodes[source])
                prediction_only_graph.add_node(target, **entity_graph.nodes[target])
                
        entity_graph = prediction_only_graph 
    print("This graph has ",entity_graph.number_of_nodes()," nodes and ",entity_graph.number_of_edges()," edges")
    return entity_graph



#initiate the session state
with st.form(key='entities_selection'):
# Use the value from the session state in the multiselect widget
    selected_entities = st.multiselect('Select biological entities you want to visualize', entities_names)
    prediction = st.checkbox("Showing only the biological entities with the predicted relations from GraPharm",key='prediction')
    selected_edges = st.multiselect('Select biological relations to show', edge_types)
    all = st.checkbox("Select all biolgical relations",key='all')
    submit_button_1 = st.form_submit_button(label='Submit')
    if not submit_button_1:
        st.write('Please select biological entities for visualization.')
        st.stop()    
    if submit_button_1:
        if all:
            selected_edges = edge_types
    if not selected_entities:
        st.write('Please choose at least one biological entity for visualization.')
        st.stop()
    if not selected_edges:
        st.write('Please choose at least one relation for visualization.')
        st.stop()
    

subgraph_network= select_entities_for_display(g,edge_df, node_df,selected_entities,
                                              selected_edges,prediction)
num_nodes = subgraph_network.number_of_nodes()
st.write("Number of the biological entities in the graph: ", num_nodes)


def networkx2pyvis(networkx_graph):
    # Create a new Pyvis network
    pyvis_graph = Network(notebook=True, 
                            bgcolor="white",
                            select_menu=True,
                            filter_menu=True,
                            neighborhood_highlight=True,
                            cdn_resources='remote')
    pyvis_graph.repulsion()
    # Add nodes and edges to the Pyvis network
    for node, node_attrs in networkx_graph.nodes(data=True):
        node_attrs['size'] = 7
        node = node_attrs['label']
        pyvis_graph.add_node(node, **node_attrs)
    for source, target, edge_attrs in networkx_graph.edges(data=True):
        source = node_df.loc[node_df['id'] == source, 'name'].values[0]
        target = node_df.loc[node_df['id'] == target, 'name'].values[0]
        if "dashes" in edge_attrs and edge_attrs["dashes"] == True:
            edge_attrs["prediction"] = "yes"
        pyvis_graph.add_edge(source, target, **edge_attrs)

    return pyvis_graph
if num_nodes == 0:
    st.subheader("No new biological links were discovered. Please choose different biological entities/relations or disable the new prediction function to view all known biological links.")
    st.stop()
st.subheader("All the known links (solid lines) were extracted from Hetionet dataset, the new links (dash lines) were predicted using ULTRA foundation model. To shown only new links (if any), select the edge prediction option.")     
if num_nodes <= 50:

    
    graph = networkx2pyvis(subgraph_network)



if num_nodes > 50:
    st.write('The subgraph is too large to visualize quickly, and constructing it may take some time. Please be patient, or consider selecting fewer entities or relations.')
    graph = networkx2pyvis(subgraph_network)
graph.show(f"streamlit/graph_{selected_entities}.html")

# Read the HTML file
with open(f"streamlit/graph_{selected_entities}.html", "r") as f:
    graph_html = f.read()

# Display the Pyvis network
components.html(graph_html, height=1200, width=1200,scrolling=True)