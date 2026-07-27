"""
Graphify to Mermaid Exporter

Reads graphify-out/graph.json and generates clean, standard Mermaid.js diagrams
representing communities, god node networks, and import cycles.
"""

import json
import os
import re
from typing import Dict, List, Any


def sanitize_id(node_id: str) -> str:
    """Sanitize node IDs for Mermaid compatibility."""
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', str(node_id))
    if clean and clean[0].isdigit():
        clean = 'n_' + clean
    return clean or "node_unknown"


def sanitize_label(label: str) -> str:
    """Sanitize labels for Mermaid node boxes."""
    clean = str(label).replace('"', "'").replace('[', '(').replace(']', ')').replace('\n', ' ').strip()
    if len(clean) > 45:
        clean = clean[:42] + "..."
    return clean


def generate_community_mermaid(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], max_nodes: int = 80) -> str:
    """Generate Mermaid flowchart grouped by communities (filtering to code nodes only)."""
    # Filter to code nodes for concise system representation
    code_nodes = [n for n in nodes if n.get("file_type") == "code"][:max_nodes]
    node_id_set = {n["id"] for n in code_nodes}
    
    communities: Dict[str, List[Dict[str, Any]]] = {}
    for node in code_nodes:
        comm_name = node.get("community_name", f"Community {node.get('community', 'Other')}")
        if comm_name not in communities:
            communities[comm_name] = []
        communities[comm_name].append(node)
        
    mermaid_lines = ["```mermaid", "flowchart TB"]
    
    for idx, (comm_name, comm_nodes) in enumerate(communities.items()):
        sub_id = f"sub_{idx}"
        clean_comm_title = sanitize_label(comm_name)
        mermaid_lines.append(f'    subgraph {sub_id} ["{clean_comm_title}"]')
        for node in comm_nodes:
            nid = sanitize_id(node["id"])
            lbl = sanitize_label(node.get("label", node["id"]))
            mermaid_lines.append(f'        {nid}["{lbl}"]')
        mermaid_lines.append("    end")
        
    # Edge rendering for included code nodes
    edge_count = 0
    for edge in edges:
        src = edge.get("source") or edge.get("u")
        tgt = edge.get("target") or edge.get("v")
        if src in node_id_set and tgt in node_id_set:
            s_id = sanitize_id(src)
            t_id = sanitize_id(tgt)
            rel = edge.get("relation") or edge.get("type", "")
            if rel:
                mermaid_lines.append(f'    {s_id} -->|"{sanitize_label(rel)}"| {t_id}')
            else:
                mermaid_lines.append(f'    {s_id} --> {t_id}')
            edge_count += 1
            if edge_count >= 80:
                break
                
    mermaid_lines.append("```")
    return "\n".join(mermaid_lines)


def generate_god_nodes_mermaid(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """Generate Mermaid graph for the top most-connected god nodes."""
    node_degree: Dict[str, int] = {}
    node_map = {n["id"]: n for n in nodes if n.get("file_type") == "code"}
    
    for edge in edges:
        src = edge.get("source") or edge.get("u")
        tgt = edge.get("target") or edge.get("v")
        if src in node_map:
            node_degree[src] = node_degree.get(src, 0) + 1
        if tgt in node_map:
            node_degree[tgt] = node_degree.get(tgt, 0) + 1
            
    # Get top 8 god nodes
    top_gods = sorted(node_degree.keys(), key=lambda k: node_degree[k], reverse=True)[:8]
    god_set = set(top_gods)
    
    # Also find immediate code neighbors of top gods
    neighbor_set = set(god_set)
    for edge in edges:
        src = edge.get("source") or edge.get("u")
        tgt = edge.get("target") or edge.get("v")
        if src in god_set and tgt in node_map:
            neighbor_set.add(tgt)
        elif tgt in god_set and src in node_map:
            neighbor_set.add(src)
            
    mermaid_lines = ["```mermaid", "graph TD"]
    for nid in neighbor_set:
        node = node_map[nid]
        lbl = sanitize_label(node.get("label", nid))
        clean_id = sanitize_id(nid)
        if nid in god_set:
            mermaid_lines.append(f'    {clean_id}{{"⭐ {lbl}"}}')
        else:
            mermaid_lines.append(f'    {clean_id}["{lbl}"]')
            
    edge_count = 0
    for edge in edges:
        src = edge.get("source") or edge.get("u")
        tgt = edge.get("target") or edge.get("v")
        if src in neighbor_set and tgt in neighbor_set:
            mermaid_lines.append(f'    {sanitize_id(src)} --> {sanitize_id(tgt)}')
            edge_count += 1
            if edge_count >= 60:
                break
                
    mermaid_lines.append("```")
    return "\n".join(mermaid_lines)


def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    graph_json_path = os.path.join(workspace_dir, "graphify-out", "graph.json")
    
    if not os.path.exists(graph_json_path):
        print(f"Error: {graph_json_path} does not exist.")
        return

    with open(graph_json_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("links", []) or graph_data.get("edges", [])

    print(f"Loaded graph with {len(nodes)} nodes and {len(edges)} edges.")

    # Generate Mermaid Community & God Node Output
    mermaid_content = f"# 📊 WebAI Codebase Knowledge Graph (Mermaid)\n\n"
    mermaid_content += "Generated automatically from `graphify-out/graph.json` via `scripts/graphify_to_mermaid.py`.\n\n"
    mermaid_content += "## 1. Codebase Community Architecture\n\n"
    mermaid_content += generate_community_mermaid(nodes, edges, max_nodes=70)
    mermaid_content += "\n\n## 2. God Nodes & High-Centrality Abstractions Network\n\n"
    mermaid_content += generate_god_nodes_mermaid(nodes, edges)

    out_path = os.path.join(workspace_dir, "graphify-out", "MERMAID_GRAPH.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(mermaid_content)

    print(f"Successfully exported clean Mermaid graph to: {out_path}")

    # Also generate standalone HTML viewer
    comm_code = generate_community_mermaid(nodes, edges, max_nodes=70).replace("```mermaid\n", "").replace("\n```", "")
    god_code = generate_god_nodes_mermaid(nodes, edges).replace("```mermaid\n", "").replace("\n```", "")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>WebAI Mermaid Knowledge Graph Viewer</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 2rem;
            margin: 0;
        }}
        h1, h2 {{ color: #58a6ff; font-weight: 600; }}
        .card {{
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <h1>📊 WebAI Codebase Knowledge Graph Viewer</h1>
    <p>Rendered automatically using <code>mermaid.js</code> from <code>graphify-out/graph.json</code>.</p>
    
    <h2>1. Codebase Community Architecture</h2>
    <div class="card">
        <pre class="mermaid">
{comm_code}
        </pre>
    </div>

    <h2>2. God Nodes & High-Centrality Abstractions</h2>
    <div class="card">
        <pre class="mermaid">
{god_code}
        </pre>
    </div>
</body>
</html>"""

    html_path = os.path.join(workspace_dir, "graphify-out", "mermaid_viewer.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Successfully generated HTML Mermaid viewer: {html_path}")


if __name__ == "__main__":
    main()
