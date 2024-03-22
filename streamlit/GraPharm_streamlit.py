import streamlit as st
import pandas as pd
from PIL import Image 
import networkx as nx
import os
import streamlit.components.v1 as components
datadir = "../data"
# Create a placeholder
placeholder = st.empty()
# Write to the placeholder
placeholder.write("Loading data...")


@st.cache_data
def import_data():
    drkg = pd.read_csv(f"{datadir}/drkg.tsv", sep="\t", header=None, names=["h", "r", "t"])
    re_gloss = pd.read_csv(f"{datadir}/relation_glossary.tsv", sep="\t")
    entities = pd.read_csv(f"{datadir}/embed/entities.tsv", sep="\t", header=None, names=["entity_name", "entity_id"])
    elations = pd.read_csv(f"{datadir}/embed/relations.tsv", sep="\t", header=None, names=["relation_name", "relation_id"])
    return drkg, re_gloss, entities, elations
drkg, re_gloss, entities, elations = import_data()
# Clear the placeholder
placeholder.empty()


@st.cache_data
def extract_entities_name(entities):
    """
    Extracts the names of entities from a given DataFrame.

    Args:
        entities (DataFrame): A DataFrame containing entity information.

    Returns:
        list: A list of entity names extracted from the DataFrame.
    """
    entity_names = entities["entity_name"].tolist()
    return entity_names

entities_names = extract_entities_name(entities)


# Implement multiselect dropdown menu for option selection (returns a list)
image = Image.open('../assets/logo@20x.png')
st.image(image, use_column_width=True)
st.title("GraPharm: A Graph-based Pharmacology Platform for Drug Repurposing")

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
st.sidebar.markdown("## Node Color Legend")
for node_type, color in node_colors.items():
    st.sidebar.markdown(f'<div style="display: inline-block; vertical-align: middle; margin-right: 10px; width: 20px; height: 20px; background-color: {color};"></div> {node_type}', unsafe_allow_html=True)

# Check if 'selected_entities' is already in the session state
if 'selected_entities' not in st.session_state or st.session_state.selected_entities == []:
    with st.form(key='entities_selection'):
        # Use the value from the session state in the multiselect widget
        st.session_state.selected_entities = st.multiselect('Select entity/entities to visualize', entities_names)
        submit_button_1 = st.form_submit_button(label='Submit')
        if not submit_button_1:
            st.write('Please select entities to visualize')
            st.stop()
elif st.button('Choose entities again'):
    with st.form(key='entities_selection'):
        # Use the value from the session state in the multiselect widget
        st.session_state.selected_entities = st.multiselect('Select entity/entities to visualize', entities_names)
        submit_button_2 = st.form_submit_button(label='Submit')
        if not submit_button_2:
            st.write('Please select entities to visualize')
            st.stop()
selected_entities = st.session_state.selected_entities
st.write('Selected entities:', str(selected_entities[:]))


@st.cache_data
def load_edge_colors():
    """Load dictionary of edge colors

    Returns:
        dict: edge colors
    """
    import json

    with open( "edge_colors.json") as f:
        edge_colors = json.load(f)

    return edge_colors
        
@st.cache_data
def tsv2networkx(drkg,re_gloss):
    """
    Convert a TSV file to a NetworkX graph.

    Parameters:
    - drkg (DataFrame): TSV file containing the data.

    Returns:
    - g_nx (Graph): NetworkX graph representing the data.
    """

    import networkx as nx

    # Define node colors for different entity types
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

    # Get interaction types from a glossary
    interaction_types = re_gloss.set_index("Relation-name").to_dict()["Interaction-type"]

    # Load edge colors
    edge_colors = load_edge_colors()

    # Extract unique entities from the TSV file
    entities = list(set(drkg["h"].tolist() + drkg["t"].tolist()))
    entity_df = pd.DataFrame({"name": entities})
    entity_df["type"] = entity_df["name"].str.split("::", expand=True)[0]

    # Create an empty NetworkX graph
    g_nx = nx.Graph()

    # Add nodes to the graph for each entity type
    for entity_type in entity_df["type"].unique():
        entities = entity_df[entity_df["type"] == entity_type]["name"].tolist()
        g_nx.add_nodes_from(entities, entity=entity_type, color=node_colors[entity_type])

    # Add edges to the graph for each link type
    for link_type in drkg["r"].unique():
        links = drkg[drkg["r"] == link_type][["h", "t"]].itertuples(index=False, name=None)
        g_nx.add_edges_from(links, label=interaction_types[link_type], color=edge_colors[link_type], dashes=False)
        g_nx.add_edges_from(
            links, label=interaction_types[link_type], color=edge_colors[link_type], dashes=False)

    return g_nx
network = tsv2networkx(drkg,re_gloss)

def select_entities_for_display(network,drkg,selected_entities):
    # Create a subgraph with the selected entities and all entities connected to them
    set_ = set()
    for entity in selected_entities:
        entity = drkg[(drkg["h"] == entity) |
                        (drkg["t"] == entity)]
        set_.update(set(entity["h"].tolist() + entity["t"].tolist()))
        print("Subgraph of {} has {} nodes".format(entity, len(set_)))   
    nodes = list(set_)
    entity_graph = network.subgraph(nodes)
    return entity_graph

subgraph_network= select_entities_for_display(network,drkg, selected_entities)
num_nodes = subgraph_network.number_of_nodes()
st.write("Number of nodes in the subgraph: ", num_nodes)


def networkx2pyvis(_networkx_graph):
    from pyvis.network import Network
    # Create a new Pyvis network
    pyvis_graph = Network(notebook=True, 
                            bgcolor="white",
                            select_menu=True,
                            filter_menu=True,
                            neighborhood_highlight=True,
                            cdn_resources='remote')
    pyvis_graph.repulsion()
    # Add nodes and edges to the Pyvis network
    for node, node_attrs in _networkx_graph.nodes(data=True):
        node_attrs['size'] = 7
        pyvis_graph.add_node(node, **node_attrs)
    for source, target, edge_attrs in _networkx_graph.edges(data=True):
        # Delete the key 'dashes' from the edge attributes
        del edge_attrs['dashes']
        pyvis_graph.add_edge(source, target, **edge_attrs)

    return pyvis_graph
       
if num_nodes <= 500:


    st.write("Plot the subgraph of the selected entities. Choose the edge types to filter out the node of interest.")


    graph = networkx2pyvis(subgraph_network)


    # Generate the HTML file
    graph.show("graph.html")

    # Read the HTML file
    with open("graph.html", "r") as f:
        graph_html = f.read()

    # Display the Pyvis network in the placeholder
    components.html(graph_html, height=1000, width=700,scrolling=True)


if num_nodes > 500:


    st.write('The subgraph is too large to visualize. Please select edge types to simplify the graph.')
    def extract_edge_labels(network):
        labels = [edge_attrs.get('label') for source, target, edge_attrs in network.edges(data=True)]
        return labels

    edges_labels = list(set(extract_edge_labels(subgraph_network)))
    
    
  
    if 'selected_edges' not in st.session_state or st.session_state.selected_edges == []:
        with st.form(key='selected_edges'):
            # Use the value from the session state in the multiselect widget
            selected_edges = st.multiselect('Select edges to visualize', edges_labels)
            submit_button_2 = st.form_submit_button(label='Submit edges')
            if not submit_button_2:
                st.write('Please select edges to visualize')
                st.stop()
    st.write('Selected edges:', str(selected_edges[:]))
    
    def filter_graph_by_edge_types(network, edge_types):
        filtered_graph = network.__class__()
        #filtered_graph.add_nodes_from(network.nodes(data=True))
        for u, v, data in network.edges(data=True):
            if data.get('label') in edge_types:
                filtered_graph.add_edge(u, v, **data)
        return filtered_graph

    # Use the function
    filtered_graph = filter_graph_by_edge_types(subgraph_network, selected_edges)
    # Get the nodes of the filtered graph
    filtered_nodes = list(filtered_graph.nodes)
    st.write('Number of nodes in the filtered subgraph:', len(filtered_nodes))
    filtered_graph = subgraph_network.subgraph(filtered_nodes)
    

    graph = networkx2pyvis(filtered_graph)

    # Generate the HTML file
    graph.show("sub_graph.html")

    # Read the HTML file
    with open("sub_graph.html", "r") as f:
        graph_html = f.read()
    col1,col2 = st.columns(2)
    with col1:
        # Display the Pyvis network in Streamlit
        components.html(graph_html, height=1000, width=700,scrolling=True)