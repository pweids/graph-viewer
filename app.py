import streamlit as st
import json
from workflows import (
    auth,
    get_workflows_from_url,
    get_workflow_graph,
    filter_graph_data,
    get_group_subgraphs,  # <— our new helper
)
from make_node_graph import create_node_graph

def main():
    st.title("Workflows Graph Viewer")

    data_source = st.radio("Select data source:", ["Workspace URL", "Paste JSON"])

    if data_source == "Workspace URL":
        token = auth()
        if not token:
            st.error("Authentication failed. Check credentials.")
            st.stop()

        # Let user enter workspace URL, then fetch workflows
        workspace_url = st.text_input("Paste workspace URL")
        if not workspace_url:
            st.stop()
        workflows = get_workflows_from_url(workspace_url, token)
        if not workflows:
            st.warning("No workflows found for that URL.")
            st.stop()

        st.subheader("Workflows")

        # 1) Pick which workflow to render
        if "selected_workflow" not in st.session_state:
            st.session_state["selected_workflow"] = None

        for wf_id, wf_name in workflows:
            if st.button(f"Render: {wf_name}", key=f"wf_{wf_id}"):
                st.session_state["selected_workflow"] = (wf_id, wf_name)
                # Clear any previously selected subgraph
                st.session_state["selected_subgraph"] = None

        # 2) Render the selected workflow
        if st.session_state["selected_workflow"]:
            wf_id, wf_name = st.session_state["selected_workflow"]
            graph_data = get_workflow_graph(token, wf_id)
            if not graph_data:
                st.error("Failed to retrieve graph data.")
                st.stop()

            filtered_data = filter_graph_data(graph_data)
            png_path = create_node_graph(filtered_data)
            st.image(png_path, caption=wf_name)

            # 3) List subgraphs for this workflow
            subgraphs = get_group_subgraphs(graph_data)
            if "selected_subgraph" not in st.session_state:
                st.session_state["selected_subgraph"] = None

            for group_id, group_name, group_workflow in subgraphs:
                if st.button(f"Render group node: {group_name}", key=f"sub_{group_id}"):
                    st.session_state["selected_subgraph"] = (group_id, group_name, group_workflow)

            # 4) Render the selected subgraph (if any)
            if st.session_state["selected_subgraph"]:
                group_id, group_name, group_workflow = st.session_state["selected_subgraph"]
                sub_filtered = filter_graph_data(group_workflow)
                sub_png_path = create_node_graph(sub_filtered)
                st.image(sub_png_path, caption=f"{group_name} (subgraph)")

    else:
        # Paste JSON case
        js_input = st.text_area("Paste JSON here", height=300)
        if st.button("Render Graph", key="render_pasted"):
            if not js_input.strip():
                st.error("No JSON provided.")
                st.stop()

            try:
                data = json.loads(js_input)
                png_path = create_node_graph(data)
                st.image(png_path, caption="Pasted JSON Graph")

                # Same idea: show subgraphs
                subgraphs = get_group_subgraphs(data)
                if "selected_pasted_subgraph" not in st.session_state:
                    st.session_state["selected_pasted_subgraph"] = None

                for group_id, group_name, group_workflow in subgraphs:
                    if st.button(f"Render group node: {group_name}", key=f"pasted_sub_{group_id}"):
                        st.session_state["selected_pasted_subgraph"] = (group_id, group_name, group_workflow)

                if st.session_state["selected_pasted_subgraph"]:
                    group_id, group_name, group_workflow = st.session_state["selected_pasted_subgraph"]
                    sub_filtered = filter_graph_data(group_workflow)
                    sub_png_path = create_node_graph(sub_filtered)
                    st.image(sub_png_path, caption=f"{group_name} (subgraph)")
            except Exception as e:
                st.error(f"Failed to parse or render graph: {e}")

if __name__ == "__main__":
    main()
