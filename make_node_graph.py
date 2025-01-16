import streamlit as st
import json
import tempfile
from graphviz import Digraph
from collections import Counter

def create_node_graph(json_data):
    dot = Digraph("node_graph", format="png")
    dot.attr(rankdir="LR")

    # Collect IDs for duplicates
    node_ids = [node["id"] for node in json_data["nodes"]]
    handle_ids = []
    for node in json_data["nodes"]:
        handle_ids.extend(h["id"] for h in node["data"].get("handlers", []))

    node_id_count = Counter(node_ids)
    handle_id_count = Counter(handle_ids)

    valid_handles = {}
    valid_node_ids = set(node_ids)
    dotted_nodes_created = set()

    def ensure_dotted_node(node_id):
        if node_id not in dotted_nodes_created:
            dot.node(node_id, label=node_id, shape="box", style="dotted")
            dotted_nodes_created.add(node_id)

    # Create normal nodes
    for node in json_data["nodes"]:
        node_id = node["id"]
        short_id = node_id.split("-")[0]
        name = node["data"].get("name", "")

        # Color node label red if its ID is a duplicate
        node_color = "red" if node_id_count[node_id] > 1 else "black"

        # Build handle rows, coloring handles red if duplicates
        inputs, outputs = [], []
        for h in node["data"].get("handlers", []):
            h_id = h["id"]
            h_type = h["type"].split('.')[-1].lower()
            color = "red" if handle_id_count[h_id] > 1 else "black"
            label_str = f'<font face="monospace" color="{color}">{h_id.split("-")[0]} ({h_type})</font>'
            if h["handlerType"].lower() == "input":
                inputs.append((h_id, label_str))
            else:
                outputs.append((h_id, label_str))

        valid_handles[node_id] = [h[0] for h in inputs + outputs]

        in_rows = "".join(
            f'<tr><td port="{h_id}" align="left">{label}</td></tr>'
            for (h_id, label) in inputs
        ) or '<tr><td align="left">&nbsp;</td></tr>'

        out_rows = "".join(
            f'<tr><td port="{h_id}" align="left">{label}</td></tr>'
            for (h_id, label) in outputs
        ) or '<tr><td align="left">&nbsp;</td></tr>'

        label = (
            f'<<table BORDER="1" CELLBORDER="0" CELLSPACING="0">'
            f'<tr><td colspan="2" align="center">'
            f'<font color="{node_color}">{name}</font><br/>'
            f'<font face="monospace" color="{node_color}">{short_id}</font></td></tr>'
            f'<tr>'
            f'  <td valign="top"><table BORDER="0" CELLBORDER="0" CELLSPACING="0">{in_rows}</table></td>'
            f'  <td valign="top"><table BORDER="0" CELLBORDER="0" CELLSPACING="0">{out_rows}</table></td>'
            f'</tr>'
            f'</table>>'
        )

        dot.node(node_id, label=label, shape="plaintext")

    # Add edges
    for edge in json_data["edges"]:
        s_node = edge["source"]
        s_handle = edge["sourceHandle"]
        t_node = edge["target"]
        t_handle = edge["targetHandle"]

        # Ensure dotted node if source/target node is missing from JSON
        if s_node not in valid_node_ids:
            ensure_dotted_node(s_node)
        if t_node not in valid_node_ids:
            ensure_dotted_node(t_node)

        # Figure out source port
        if s_node in valid_node_ids and s_handle in valid_handles[s_node]:
            from_port = f'{s_node}:{s_handle}'
        else:
            from_port = s_node

        # Figure out target port
        if t_node in valid_node_ids and t_handle in valid_handles[t_node]:
            to_port = f'{t_node}:{t_handle}'
        else:
            to_port = t_node

        # Color edge red if the node is valid but the target handle doesn't exist
        edge_color = "red" if (t_node in valid_node_ids and t_handle not in valid_handles[t_node]) else "black"

        dot.edge(from_port, to_port, color=edge_color)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
        dot.render(tmpfile.name, cleanup=True)
        return tmpfile.name + ".png"

st.title("Node Graph Generator")

js_input = st.text_area("Paste JSON here", height=300)
if st.button("Render Graph"):
    if not js_input.strip():
        st.error("No JSON provided.")
    else:
        try:
            data = json.loads(js_input)
            png_path = create_node_graph(data)
            st.image(png_path)
        except Exception as e:
            st.error(f"Failed to parse or render graph: {e}")
