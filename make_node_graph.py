import streamlit as st
import json
import tempfile
from collections import Counter
from graphviz import Digraph

def create_node_graph(json_data):
    dot = Digraph("node_graph", format="png")
    dot.attr(rankdir="LR")

    # Count duplicates
    node_ids = [n["id"] for n in json_data["nodes"]]
    handle_ids = []
    for n in json_data["nodes"]:
        handle_ids.extend(h["id"] for h in n["data"].get("handlers", []))

    node_id_count = Counter(node_ids)
    handle_id_count = Counter(handle_ids)

    valid_handles = {}
    valid_node_ids = set(node_ids)

    for node in json_data["nodes"]:
        node_id = node["id"]
        short_id = node_id.split("-")[0]
        name = node["data"].get("name", "")

        # Color node label red if its ID is duplicated
        node_color = "red" if node_id_count[node_id] > 1 else "black"

        # Build rows for handles, coloring duplicates red
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
            f'<tr><td colspan="2" align="center"><font color="{node_color}">{name}</font><br/><font face="monospace" color="{node_color}">{short_id}</font></td></tr>'
            f'<tr>'
            f'  <td valign="top"><table BORDER="0" CELLBORDER="0" CELLSPACING="0">{in_rows}</table></td>'
            f'  <td valign="top"><table BORDER="0" CELLBORDER="0" CELLSPACING="0">{out_rows}</table></td>'
            f'</tr>'
            f'</table>>'
        )

        dot.node(node_id, label=label, shape="plaintext")

    # Add edges, color them red if target handle doesn't exist
    for edge in json_data["edges"]:
        s_node = edge["source"]
        s_handle = edge["sourceHandle"]
        t_node = edge["target"]
        t_handle = edge["targetHandle"]

        from_port = f'{s_node}:{s_handle}' if (s_node in valid_node_ids and s_handle in valid_handles[s_node]) else s_node
        to_port = f'{t_node}:{t_handle}' if (t_node in valid_node_ids and t_handle in valid_handles[t_node]) else t_node

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
