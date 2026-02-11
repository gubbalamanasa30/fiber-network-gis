import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "Fiber Network Tools"
        self.alias = "FiberTools"
        # List of tool classes associated with this toolbox
        self.tools = [ExpandCable, ConnectEntities]

class ExpandCable(object):
    def __init__(self):
        self.label = "Expand Cable to Strands"
        self.description = "Creates strand records in the FiberStrand table for a selected cable based on its fiber count."
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Param 0: The Cable Feature (Input)
        in_cable = arcpy.Parameter(
            displayName="Input Fiber Cable",
            name="in_cable",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        in_cable.filter.list = ["Polyline"]

        # Param 1: The Strand Table (Target)
        target_table = arcpy.Parameter(
            displayName="Target Strand Table",
            name="target_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        return [in_cable, target_table]

    def execute(self, parameters, messages):
        in_cable = parameters[0].valueAsText
        target_table = parameters[1].valueAsText

        # Fields to read from Cable
        fields = ["OID@", "CableID", "FiberCount", "CableType"]
        
        with arcpy.da.SearchCursor(in_cable, fields) as cursor:
            for row in cursor:
                oid = row[0]
                cable_id = row[1]
                fiber_count = int(row[2]) if row[2] else 0
                cable_type = row[3]
                
                messages.addMessage(f"Processing Cable {cable_id} (OID: {oid})... Generating {fiber_count} strands.")
                
                if fiber_count > 0:
                    # Prepare inserts
                    insert_cursor = arcpy.da.InsertCursor(target_table, ["ParentCableID", "StrandID", "Status", "StrandColor"])
                    
                    # TIA-598 Color Code (12 standard colors)
                    colors = ["Blue", "Orange", "Green", "Brown", "Slate", "White", "Red", "Black", "Yellow", "Violet", "Rose", "Aqua"]
                    
                    for i in range(1, fiber_count + 1):
                        strand_id = f"{cable_id}-S{i:03d}"
                        color = colors[(i - 1) % 12]
                        # Insert row
                        insert_cursor.insertRow([cable_id, strand_id, "Dark", color])
                    
                    del insert_cursor
        return

class ConnectEntities(object):
    def __init__(self):
        self.label = "Connect Entities (Splice/Patch)"
        self.description = "Creates a connection record between two entities (Strand-to-Strand or Strand-to-Port)."
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Connection Table
        conn_table = arcpy.Parameter(
            displayName="Fiber Connection Table",
            name="conn_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")

        # From ID
        from_id = arcpy.Parameter(
            displayName="From ID (Strand or Port)",
            name="from_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        # To ID
        to_id = arcpy.Parameter(
            displayName="To ID (Strand or Port)",
            name="to_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
            
        # Type
        conn_type = arcpy.Parameter(
            displayName="Connection Type",
            name="conn_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        conn_type.filter.type = "ValueList"
        conn_type.filter.list = ["Splice", "Patch", "CrossConnect"]

        return [conn_table, from_id, to_id, conn_type]

    def execute(self, parameters, messages):
        table = parameters[0].valueAsText
        f_id = parameters[1].valueAsText
        t_id = parameters[2].valueAsText
        c_type = parameters[3].valueAsText

        messages.addMessage(f"Connecting {f_id} to {t_id} as {c_type}...")
        
        with arcpy.da.InsertCursor(table, ["FromObjectID", "ToObjectID", "Type"]) as cursor:
            cursor.insertRow([f_id, t_id, c_type])
            
        messages.addMessage("Connection created successfully.")
        return
