import bpy

def get_pib_transform(pib_coll, pib_obj):
    pib_collection = bpy.data.collections.get(pib_coll)
    target_obj = pib_collection.objects.get(pib_obj)
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = target_obj.evaluated_get(depsgraph)

    final_matrix = eval_obj.matrix_world.copy()
    source_info = f"of the object {target_obj.name} (Global Space)"
    
    pib_constraint = target_obj.constraints.get("Pib Parent")
    
    if pib_constraint and pib_constraint.enabled and pib_constraint.target:
        if pib_constraint.target.type == 'ARMATURE' and pib_constraint.subtarget:
            armature = pib_constraint.target
            bone_name = pib_constraint.subtarget
            
            eval_armature = armature.evaluated_get(depsgraph)
            
            if bone_name in eval_armature.pose.bones:
                pose_bone = eval_armature.pose.bones[bone_name]
                
                bone_world_matrix = eval_armature.matrix_world @ pose_bone.matrix
                
                final_matrix = bone_world_matrix.inverted() @ eval_obj.matrix_world
                source_info = f"of the object '{target_obj.name}' LOCAL to the bone '{bone_name}' (from Head)"

    location = final_matrix.to_translation()
    matrix_3x3 = final_matrix.to_3x3()

    blender_x = matrix_3x3.col[0]
    blender_y = matrix_3x3.col[1]
    blender_z = matrix_3x3.col[2]

    # (x -> -x, y -> z, z -> y)
    engine_left = (blender_x[0], blender_x[2], blender_x[1])
    engine_up = (-blender_z[0], blender_z[2], blender_z[1])
    engine_forward = (-blender_y[0], blender_y[2], blender_y[1])
    engine_coords = (-location[0], location[2], location[1])

    print("\n" + "="*60)
    print("CALCULATED PIB MATRICES")
    print(f"Transform space: {source_info}")
    print("="*60)
    print("DIRECTIONS:")
    print(f"Left Direction X:  {engine_left[0]:.7f}")
    print(f"Left Direction Y:  {engine_left[1]:.7f}")
    print(f"Left Direction Z:  {engine_left[2]:.7f}")
    print("-" * 30)
    print(f"Up Direction X:    {engine_up[0]:.7f}")
    print(f"Up Direction Y:    {engine_up[1]:.7f}")
    print(f"Up Direction Z:    {engine_up[2]:.7f}")
    print("-" * 30)
    print(f"Forward Direction X: {engine_forward[0]:.7f}")
    print(f"Forward Direction Y: {engine_forward[1]:.7f}")
    print(f"Forward Direction Z: {engine_forward[2]:.7f}")
    print("="*50)
    print("COORDINATES:")
    print(f"Coordinate X (Left):    {engine_coords[0]:.4f}")
    print(f"Coordinate Y (Up):      {engine_coords[1]:.4f}")
    print(f"Coordinate Z (Forward): {engine_coords[2]:.4f}")
    print("="*60)

def set_pib_parent_bone(context, operator, pib_coll, pib_obj):
    pib_collection = bpy.data.collections.get(pib_coll)
    target_obj = pib_collection.objects.get(pib_obj)    
    
    active_obj = context.active_object
    if not active_obj or active_obj.type != 'ARMATURE':
        operator.report({'WARNING'}, "Enter Pose Mode!")
        return
        
    active_bone = context.active_pose_bone
    if not active_bone:
        operator.report({'WARNING'}, "Select a bone in Pose Mode!")
        return

    pib_constraint = target_obj.constraints.get("Pib Parent")
    if not pib_constraint:
        operator.report({'ERROR'}, "Constraint 'Pib Parent' not found on 'Lil_Pib'!")
        return

    pib_constraint.target = active_obj
    pib_constraint.subtarget = active_bone.name

    context.view_layer.update()
    
    operator.report({'INFO'}, f"'Lil_Pib' parented to '{active_bone.name}'")

def set_pib_shape(context, operator, pib_coll, pib_obj):

    pib_collection = bpy.data.collections.get(pib_coll)
    pib_dummy_obj = pib_collection.objects.get(pib_obj)

    active_obj = context.active_object
    if not active_obj:
        operator.report({'WARNING'}, "Select target object!")
        return False
        
    if active_obj == pib_dummy_obj:
        operator.report({'WARNING'}, "Cannot select 'Lil_Pib' itself.  Select a different object!")
        return False

    if active_obj.type != 'MESH':
        operator.report({'ERROR'}, f"'{active_obj.name}' is a '{active_obj.type}'. Only MESH type is allowed!")
        return False
    
    constraint_name = "Pib Shape"
    constraint = active_obj.constraints.get(constraint_name)
    
    if not constraint:
        constraint = active_obj.constraints.new(type='COPY_TRANSFORMS')
        constraint.name = constraint_name
        constraint.mix_mode = 'BEFORE_FULL'        
        constraint.target = pib_dummy_obj
        constraint.enabled = True

    context.view_layer.update()
    
    operator.report({'INFO'}, f"'{active_obj.name}' is set as the shape for 'Lil_Pib'")

def create_pib_dummy(collection_name, object_name):

    coll = bpy.data.collections.get(collection_name) or bpy.data.collections.new(
        collection_name
    )
    
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)

    if object_name not in coll.objects:
        empty_data = bpy.data.objects.new(object_name, None)
        empty_data.empty_display_type = (
            "ARROWS"
        )
        
        coll.objects.link(empty_data)

    constraint_name = "Pib Parent"
    con = empty_data.constraints.get(constraint_name) or empty_data.constraints.new(
        type="COPY_LOCATION"
    )
    con.name = constraint_name  
    con.use_offset = True
