import streamlit as st
import json
from workflows import auth, get_workflows_from_url, get_workflow_graph, filter_graph_data
from make_node_graph import create_node_graph

def main():
    st.title("My Workflow Graph App")

    # Choose data source
    data_source = st.radio("Select data source:", ["Workspace URL", "Paste JSON"])

    if data_source == "Workspace URL":
        token = auth()
        if not token:
            st.error("Authentication failed. Check credentials.")
            st.stop()

        workspace_url = st.text_input("Paste workspace URL")
        if not workspace_url:
            st.stop()

        # Fetch list of workflows
        workflows = get_workflows_from_url(workspace_url, token)
        if not workflows:
            st.warning("No workflows found for that URL.")
            st.stop()

        st.subheader("Workflows")
        for wf_id, wf_name in workflows:
            if st.button(f"Render: {wf_name}"):
                graph_data = get_workflow_graph(token, wf_id)
                if not graph_data:
                    st.error("Failed to retrieve graph data.")
                    st.stop()

                filtered_data = filter_graph_data(graph_data)
                png_path = create_node_graph(filtered_data)
                st.image(png_path, caption=wf_name)

    else:
        # Paste JSON
        js_input = st.text_area("Paste JSON here", height=300)
        if st.button("Render Graph"):
            if not js_input.strip():
                st.error("No JSON provided.")
                st.stop()

            try:
                data = json.loads(js_input)
                png_path = create_node_graph(data)
                st.image(png_path, caption="Pasted JSON Graph")
            except Exception as e:
                st.error(f"Failed to parse or render graph: {e}")

if __name__ == "__main__":
    main()
