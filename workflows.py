import requests
from requests.exceptions import HTTPError, RequestException
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

# Retrieve email and password from environment variables
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

# Base URLs
url = "https://api-dev.formant.io/v1/"
wflow_url = "https://workflows-one.vercel.app/"

def auth():
    """
    Authenticate and retrieve the access token.
    """
    auth_url = url + "admin/auth/login"
    payload = {
        "email": email,
        "password": password,
        "tokenExpirationSeconds": 604800
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    try:
        response = requests.post(auth_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get('authentication').get('accessToken')
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    return None

def get_workflows(token):
    """
    Retrieve workflows using the provided token.
    """
    get_url = wflow_url + "api/workflows"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.get(get_url, headers=headers)
        response.raise_for_status()
        return response.json().get('items')
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    return None

def get_workspaces(token):
    """
    Retrieve workspaces using the provided token.
    """
    get_url = wflow_url + "api/workspaces"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.get(get_url, headers=headers)
        response.raise_for_status()
        return response.json()['items']
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    return None

def find_workflows(wspace):
    """
    Extract workflows from the workspace layout.
    """
    children = wspace['layout']['dockLayout']['dockbox']

    def flat_map_children(arr):
        workflows = []
        children = arr.get('children', [])
        for child in children:
            if 'children' in child:
                wfs = flat_map_children(child)
            else:
                wfs = [(wf['id'], wf['title']) for wf in child.get('tabs', []) if wf.get('type') == 'Workflow']
            workflows.extend(wfs)
        return workflows

    return flat_map_children(children)

def get_workflows_by_workspace(token):
    """
    Map workspace IDs to their respective workflows.
    """
    workspaces = get_workspaces(token)
    if workspaces:
        return {ws['id']: find_workflows(ws) for ws in workspaces}
    return {}

def get_workflows_from_url(url, token):
    """
    Retrieve workflows based on the provided workspace URL.
    """
    wspace_id = url.strip('/').split('/')[-1]
    ws_to_wf = get_workflows_by_workspace(token)
    return ws_to_wf.get(wspace_id, [])


def get_workflow_graph(token, workflow_id):
    workflows = get_workflows(token)
    workflow = [f for f in workflows if f['id'] == workflow_id]
    if workflow:
        return workflow[0]['workflow']
    else:
        return None

def get_group_subgraphs(graph_data):
    """
    Return a list of (group_node_id, group_node_name, group_node_workflow_dict).
    Each entry corresponds to a node with isGroup=True and a valid groupNodeData.workflow.
    """
    subgraphs = []
    nodes = graph_data.get("nodes", [])
    for node in nodes:
        if node["data"].get("isGroup") and "groupNodeData" in node["data"]:
            gdata = node["data"]["groupNodeData"].get("workflow")
            if gdata:
                subgraphs.append(
                    (
                        node["id"],
                        node["data"].get("name", "Untitled group"),
                        gdata
                    )
                )
    return subgraphs

def filter_graph_data(graph_data):
    # Extract and map nodes to the required fields
    filtered_nodes = [
        {
            "id": node["id"],
            "data": {
                "name": node.get("data", {}).get("name", ""),
                "handlers": [
                    {
                        "id": handler["id"],
                        "type": handler["type"],
                        "handlerType": handler["handlerType"],
                    }
                    for handler in node.get("data", {}).get("handlers", [])
                ],
            },
        }
        for node in graph_data.get("nodes", [])
    ]

    # Extract and map edges to the required fields
    filtered_edges = [
        {
            "source": edge["source"],
            "sourceHandle": edge.get("sourceHandle"),
            "target": edge["target"],
            "targetHandle": edge.get("targetHandle"),
        }
        for edge in graph_data.get("edges", [])
    ]

    # Create the filtered graph object
    filtered_graph_data = {
        "nodes": filtered_nodes,
        "edges": filtered_edges,
    }

    return filtered_graph_data


if __name__ == "__main__":
    token = auth()
    if token:
        url = input("Enter workspace URL: ").strip()
        workflows = get_workflows_from_url(url, token)
        if workflows:
            print("Workflows:")
            for i, wf in enumerate(workflows):
                print(f"{i + 1}. {wf[1]}")
            try:
                choice = int(input("Which one? "))
                if 1 <= choice <= len(workflows):
                    graph = get_workflow_graph(token, workflows[choice -1][0])
                    graph = filter_graph_data(graph)

                    print(json.dumps(graph, indent=2))
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Please enter a valid number.")
        else:
            print("No workflows found for the provided URL.")
    else:
        print("Authentication failed.")
