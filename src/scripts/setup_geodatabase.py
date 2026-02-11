import arcpy
import os

def setup_geodatabase(output_folder, gdb_name="FiberNetwork.gdb"):
    """
    Creates a File Geodatabase for Fiber Optic Asset Management.
    Includes Feature Datasets for Structure and Telecom networks,
    plus non-spatial tables for Strands and Ports.
    """
    print(f"Creating Geodatabase in {output_folder}...")
    
    # Create GDB
    if not arcpy.Exists(os.path.join(output_folder, gdb_name)):
        arcpy.management.CreateFileGDB(output_folder, gdb_name)
    gdb_path = os.path.join(output_folder, gdb_name)
    arcpy.env.workspace = gdb_path
    arcpy.env.overwriteOutput = True

    # -------------------------------------------------------------------------
    # 1. Domains (Drop-down lists)
    # -------------------------------------------------------------------------
    print("Creating Domains...")
    domains = {
        "FiberCount": {"12": "12 Strand", "24": "24 Strand", "48": "48 Strand", "72": "72 Strand", "144": "144 Strand"},
        "StructureType": {"Pole": "Utility Pole", "Manhole": "Manhole", "Handhole": "Handhole", "Cabinet": "Street Cabinet"},
        "CableType": {"Distribution": "Distribution Cable", "Drop": "Drop Cable", "Feeder": "Feeder Cable"},
        "AssetStatus": {"Proposed": "Proposed", "InService": "In Service", "Retired": "Retired", "Abandoned": "Abandoned"},
        "PortType": {"LC": "LC Connector", "SC": "SC Connector", "Splice": "Fusion Splice"},
        "Owner": {"Self": "My Company", "City": "City Infrastructure", "3rdParty": "Third Party Lease"}
    }

    for dom_name, values in domains.items():
        try:
            arcpy.management.CreateDomain(gdb_path, dom_name, f"{dom_name} Domain", "TEXT", "CODED")
            for code, desc in values.items():
                arcpy.management.AddCodedValueToDomain(gdb_path, dom_name, code, desc)
        except:
            print(f"Domain {dom_name} might already exist or error creating.")

    # -------------------------------------------------------------------------
    # 2. Feature Datasets (Spatial Groups)
    # -------------------------------------------------------------------------
    print("Creating Feature Datasets...")
    sr = arcpy.SpatialReference(3857) # Web Mercator (Standard for web GIS)
    
    fds_list = ["StructureNetwork", "TelecomNetwork"]
    for fds in fds_list:
        if not arcpy.Exists(fds):
            arcpy.management.CreateFeatureDataset(gdb_path, fds, sr)

    # -------------------------------------------------------------------------
    # 3. Feature Classes: Structure Network (Civil)
    # -------------------------------------------------------------------------
    print("Creating Structure Features...")
    
    # Structure Junctions (Poles, Manholes)
    struc_pt = "StructureJunction"
    if not arcpy.Exists(os.path.join(gdb_path, "StructureNetwork", struc_pt)):
        arcpy.management.CreateFeatureClass(os.path.join(gdb_path, "StructureNetwork"), struc_pt, "POINT")
        arcpy.management.AddField(struc_pt, "AssetID", "TEXT", field_length=50)
        arcpy.management.AddField(struc_pt, "Type", "TEXT", field_length=50, field_domain="StructureType")
        arcpy.management.AddField(struc_pt, "Status", "TEXT", field_length=20, field_domain="AssetStatus")
        arcpy.management.AddField(struc_pt, "Owner", "TEXT", field_length=50, field_domain="Owner")

    # Structure Lines (Trenches, Ducts)
    struc_line = "StructureLine"
    if not arcpy.Exists(os.path.join(gdb_path, "StructureNetwork", struc_line)):
        arcpy.management.CreateFeatureClass(os.path.join(gdb_path, "StructureNetwork"), struc_line, "POLYLINE")
        arcpy.management.AddField(struc_line, "AssetID", "TEXT", field_length=50)
        arcpy.management.AddField(struc_line, "Type", "TEXT", field_length=50) # Trench, DuctBank
        arcpy.management.AddField(struc_line, "DuctCount", "SHORT")

    # -------------------------------------------------------------------------
    # 4. Feature Classes: Telecom Network (Fiber)
    # -------------------------------------------------------------------------
    print("Creating Telecom Features...")

    # Fiber Cable (Line)
    cable = "FiberCable"
    if not arcpy.Exists(os.path.join(gdb_path, "TelecomNetwork", cable)):
        arcpy.management.CreateFeatureClass(os.path.join(gdb_path, "TelecomNetwork"), cable, "POLYLINE")
        arcpy.management.AddField(cable, "CableID", "TEXT", field_length=50)
        arcpy.management.AddField(cable, "FiberCount", "TEXT", field_length=10, field_domain="FiberCount")
        arcpy.management.AddField(cable, "CableType", "TEXT", field_length=20, field_domain="CableType")
        arcpy.management.AddField(cable, "InstallDate", "DATE")

    # Network Device (Splice Closures, OLTs, Splitters)
    device = "TelecomDevice"
    if not arcpy.Exists(os.path.join(gdb_path, "TelecomNetwork", device)):
        arcpy.management.CreateFeatureClass(os.path.join(gdb_path, "TelecomNetwork"), device, "POINT")
        arcpy.management.AddField(device, "DeviceID", "TEXT", field_length=50)
        arcpy.management.AddField(device, "Type", "TEXT", field_length=50) # OLT, SpliceClosure, Splitter
        arcpy.management.AddField(device, "Model", "TEXT", field_length=50)

    # -------------------------------------------------------------------------
    # 5. Non-Spatial Objects (Tables)
    # -------------------------------------------------------------------------
    print("Creating Non-Spatial Tables...")

    # Fiber Strands (The individual glass)
    strand_table = "FiberStrand"
    if not arcpy.Exists(strand_table):
        arcpy.management.CreateTable(gdb_path, strand_table)
        arcpy.management.AddField(strand_table, "StrandID", "TEXT", field_length=50)
        arcpy.management.AddField(strand_table, "ParentCableID", "TEXT", field_length=50) # Configured as foreign key logic
        arcpy.management.AddField(strand_table, "TubeColor", "TEXT", field_length=20)
        arcpy.management.AddField(strand_table, "StrandColor", "TEXT", field_length=20)
        arcpy.management.AddField(strand_table, "Status", "TEXT", field_length=20) # Dark, Lit, Broken

    # Device Ports (Input/Output ports on equipment)
    port_table = "DevicePort"
    if not arcpy.Exists(port_table):
        arcpy.management.CreateTable(gdb_path, port_table)
        arcpy.management.AddField(port_table, "PortID", "TEXT", field_length=50)
        arcpy.management.AddField(port_table, "ParentDeviceID", "TEXT", field_length=50)
        arcpy.management.AddField(port_table, "PortNumber", "SHORT")
        arcpy.management.AddField(port_table, "PortType", "TEXT", field_length=20, field_domain="PortType")

    # Connectivity Table (Many-to-Many Connections: Strand A <-> Strand B or Strand <-> Port)
    conn_table = "FiberConnection"
    if not arcpy.Exists(conn_table):
        arcpy.management.CreateTable(gdb_path, conn_table)
        arcpy.management.AddField(conn_table, "FromObjectID", "TEXT", field_length=50)
        arcpy.management.AddField(conn_table, "FromObjectType", "TEXT", field_length=20) # Strand, Port
        arcpy.management.AddField(conn_table, "ToObjectID", "TEXT", field_length=50)
        arcpy.management.AddField(conn_table, "ToObjectType", "TEXT", field_length=20) # Strand, Port
        arcpy.management.AddField(conn_table, "Type", "TEXT", field_length=20) # Splice, Patch

    print(f"Success! Geodatabase created at: {gdb_path}")

if __name__ == "__main__":
    # Get the directory of the current script
    current_folder = os.path.dirname(os.path.abspath(__file__))
    setup_geodatabase(current_folder)
