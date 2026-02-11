import arcpy

def trace_fiber_path(start_id, connection_table_path):
    """
    Traces the fiber path from a starting entity ID (Strand or Port)
    by recursively searching the FiberConnection table.
    """
    print(f"Tracing path starting from: {start_id}")
    
    visited = set()
    queue = [start_id]
    path = []
    
    # Pre-load connections into a dictionary for performance (Adjacency List)
    # Graph: { NodeID: [ConnectedNodeID, ...], ... }
    graph = {}
    
    fields = ["FromObjectID", "ToObjectID", "Type"]
    with arcpy.da.SearchCursor(connection_table_path, fields) as cursor:
        for row in cursor:
            u, v, c_type = row[0], row[1], row[2]
            
            if u not in graph: graph[u] = []
            if v not in graph: graph[v] = []
            
            graph[u].append(v)
            graph[v].append(u) # Undirected graph assumption for continuity

    # BFS Trace
    while queue:
        current_node = queue.pop(0)
        
        if current_node in visited:
            continue
        visited.add(current_node)
        path.append(current_node)
        
        # Find neighbors
        if current_node in graph:
            connections = graph[current_node]
            for neighbor in connections:
                if neighbor not in visited:
                    queue.append(neighbor)
    
    print("\n--- Trace Result ---")
    print(f"Total Hops: {len(path)}")
    print(" -> ".join(path))
    return path

if __name__ == "__main__":
    # Test execution
    # Replace this path with your actual GDB path
    gdb_path = r"C:\Users\manas\.gemini\antigravity\scratch\FiberNetwork.gdb"
    conn_table = f"{gdb_path}\\FiberConnection"
    
    # Example ID (This would need to exist in your data)
    start_entity = "CABLE-001-S001" 
    
    if arcpy.Exists(conn_table):
        try:
            trace_fiber_path(start_entity, conn_table)
        except Exception as e:
            print(f"Error during trace: {e}")
    else:
        print("Connection table not found. Run setup_geodatabase.py first.")
