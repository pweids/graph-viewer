import streamlit as st
import json
import tempfile
from graphviz import Digraph

def create_node_graph(json_data):
    dot = Digraph("node_graph", format="png")
    dot.attr(rankdir="LR")

    valid_handles = {}
    valid_node_ids = set(node["id"] for node in json_data["nodes"])
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

        inputs, outputs = [], []
        for h in node["data"].get("handlers", []):
            h_id = h["id"]
            h_type = h["type"].split('.')[-1].lower()
            label_str = f'<font face="monospace">{h_id.split("-")[0]} ({h_type})</font>'
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
            f'<tr><td colspan="2" align="center">{name}<br/><font face="monospace">{short_id}</font></td></tr>'
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

        if s_node in valid_node_ids:
            if s_handle in valid_handles[s_node]:
                from_port = f'{s_node}:{s_handle}'
            else:
                from_port = s_node
        else:
            ensure_dotted_node(s_node)
            from_port = s_node

        if t_node in valid_node_ids:
            if t_handle in valid_handles[t_node]:
                to_port = f'{t_node}:{t_handle}'
            else:
                to_port = t_node
        else:
            ensure_dotted_node(t_node)
            to_port = t_node

        dot.edge(from_port, to_port)

    # Render to temp file
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
