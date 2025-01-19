import streamlit as st
import json
import tempfile
from graphviz import Digraph
from collections import defaultdict

def create_alt_node_graph_with_handles(data):
    """
    Renders a Graphviz diagram from the new data structure but uses ports/handles
    for edges (like your original node graph), so edges are unlabeled. Attributes
    show in the node body, and transitions are blue edges labeled with their method type.

    Example input format:
    {
      "graph": {
        "id": "...",
        "nodes": [
          {
            "id": "abc",
            "type": "workflow-constant",
            "attributes": [
              { "name": "value", "value": "someData" }
            ],
            "enabled": "always"
          },
          ...
        ],
        "edges": [
          {
            "from": { "node": "abc", "output": "value" },
            "to": { "node": "xyz", "input": "startTime" }
          },
          ...
        ]
      },
      "transitions": [
        {
          "from": "abc",
          "to": "xyz",
          "method": { "type": "immediately_after" }
        },
        ...
      ]
    }
    """

    dot = Digraph("alt_node_graph_handles", format="png")
    dot.attr(rankdir="LR", dpi="300", size="10,10!")
    
    graph = data.get("graph", {})
    transitions = data.get("transitions", [])

    # Collect input/output names from edges
    input_ports = defaultdict(set)   # node_id -> set of input port names
    output_ports = defaultdict(set)  # node_id -> set of output port names

    for edge in graph.get("edges", []):
        from_node = edge["from"]["node"]
        to_node = edge["to"]["node"]
        out_name = edge["from"].get("output", "")
        in_name  = edge["to"].get("input", "")
        if out_name:
            output_ports[from_node].add(out_name)
        if in_name:
            input_ports[to_node].add(in_name)

    # Create nodes with an HTML table label
    for node in graph.get("nodes", []):
        node_id = node["id"]
        node_type = node.get("type", "Untitled")
        attrs = node.get("attributes", [])
        # e.g. name: value
        attr_lines = [f"{a['name']}: {a['value']}" for a in attrs]

        # Build input rows
        in_rows = "".join(
            f'<tr><td port="{port}" align="left">{port}</td></tr>'
            for port in sorted(input_ports[node_id])
        ) or '<tr><td align="left">&nbsp;</td></tr>'
        
        # Build output rows
        out_rows = "".join(
            f'<tr><td port="{port}" align="right">{port}</td></tr>'
            for port in sorted(output_ports[node_id])
        ) or '<tr><td align="right">&nbsp;</td></tr>'

        # Middle cell for attributes (optional)
        # Combine them into a single string separated by <br/>
        attributes_str = "<br/>".join(attr_lines) if attr_lines else ""
        
        label = (
            f'<<table BORDER="1" CELLBORDER="0" CELLSPACING="0">'
            f'<tr><td colspan="2" align="center"><b>{node_type}</b></td></tr>'
            f'<tr><td colspan="2" align="left">{attributes_str}</td></tr>'
            f'<tr>'
            f'  <td valign="top"><table BORDER="0" CELLBORDER="0" CELLSPACING="0">{in_rows}</table></td>'
            f'  <td valign="top"><table BORDER="0" CELLBORDER="0" CELLSPACING="0">{out_rows}</table></td>'
            f'</tr>'
            f'</table>>'
        )

        dot.node(node_id, label=label, shape="plaintext")

    # Add normal edges (black, from port to port)
    for edge in graph.get("edges", []):
        from_node = edge["from"]["node"]
        to_node = edge["to"]["node"]
        out_name = edge["from"].get("output", "")
        in_name = edge["to"].get("input", "")

        # If we have valid ports, link them. Otherwise fall back to the node.
        source_port = f"{from_node}:{out_name}" if out_name in output_ports[from_node] else from_node
        target_port = f"{to_node}:{in_name}" if in_name in input_ports[to_node] else to_node
        
        dot.edge(source_port, target_port, color="black")

    # Add transitions (blue edges with label=method.type)
    for t in transitions:
        src = t["from"]
        dst = t["to"]
        method_type = t.get("method", {}).get("type", "")
        dot.edge(src, dst, label=method_type, color="blue")

    # Render
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
        dot.render(tmpfile.name, cleanup=True)
        return tmpfile.name + ".png"

def main():
    st.title("New Data Structure (Handles)")

    json_data = st.text_area("Paste JSON here:", height=300)
    if st.button("Render"):
        try:
            data = json.loads(json_data)
            png_path = create_alt_node_graph_with_handles(data)
            st.image(png_path, caption="Graph with Ports/Handles")
        except Exception as e:
            st.error(f"Failed to parse or render: {e}")

if __name__ == "__main__":
    main()
