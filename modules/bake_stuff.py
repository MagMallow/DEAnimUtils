import bpy
from mathutils import Vector

CLEAR_BONES = [
    'ude2_r_n','ude2_l_n',
    'ude1_r_n','ude1_l_n',
    'asi1_r_n','asi1_l_n',
    'asi2_r_n','asi2_l_n'
]

def setup_bake_constraints(context, rig_armature, original_armature, limbs_map):

    if not rig_armature.animation_data or not rig_armature.animation_data.action:
        for bone in rig_armature.pose.bones: bone.matrix_basis.identity()
        return []
    
    bpy.ops.object.mode_set(mode='OBJECT')  
      
    bpy.ops.object.select_all(action='DESELECT')
    rig_armature.select_set(True)
    context.view_layer.objects.active = rig_armature
    bpy.ops.object.mode_set(mode='POSE')
    
    pose_bones = rig_armature.pose.bones
    obj = bpy.data.objects.get

    bake_list = []
    
    # Set IK constraints
    for ik_bone_name, (orig_bone_name, pole_bone_name) in limbs_map.items():
            
        if ik_bone_name in pose_bones:
            ik_bone = pose_bones[ik_bone_name]
            
            ik_bone.keyframe_insert(data_path="location", group=ik_bone_name)
            if ik_bone.rotation_mode == 'QUATERNION':
                ik_bone.keyframe_insert(data_path="rotation_quaternion", group=ik_bone_name)
            else:
                ik_bone.keyframe_insert(data_path="rotation_euler", group=ik_bone_name)
            
            constraint = ik_bone.constraints.new(type='COPY_TRANSFORMS')
            constraint.target = rig_armature   
            
            # FIXME: Needs a proper solution
            if "asi2" in orig_bone_name:   child_bone_name = orig_bone_name.replace("asi2", "asi3")
            elif "ude2" in orig_bone_name: child_bone_name = orig_bone_name.replace("ude2", "ude3")   

            constraint.subtarget = child_bone_name
            constraint.mix_mode = 'REPLACE'         
            constraint.target_space = 'WORLD'       
            constraint.owner_space = 'WORLD'        
            constraint.name = f"Bake_Temp_{orig_bone_name}"
            
            bake_list.append(ik_bone)

    # Set Pole constraints
    for ik_bone_name, (orig_bone_name, pole_bone_name) in limbs_map.items():
        if pole_bone_name in pose_bones:
            pole_bone = pose_bones[pole_bone_name]
            
            pole_bone.keyframe_insert(data_path="location", group=pole_bone_name)
            if pole_bone.rotation_mode == 'QUATERNION':
                pole_bone.keyframe_insert(data_path="rotation_quaternion", group=pole_bone_name)
            else:
                pole_bone.keyframe_insert(data_path="rotation_euler", group=pole_bone_name)
            
            constraint = pole_bone.constraints.new(type='COPY_LOCATION')
            constraint.target = obj(f"{orig_bone_name}_Child_(TEMP)")              
            constraint.target_space = 'WORLD'       
            constraint.owner_space = 'WORLD'        
            constraint.name = f"Bake_Temp_{pole_bone_name}"
            
            bake_list.append(pole_bone)
            
    context.view_layer.update()

    for bone in pose_bones:
        bone.bone.select = False
        
    for bake_bone in bake_list:
        bake_bone.bone.select = True
    
    frame_start = context.scene.frame_start
    frame_end = context.scene.frame_end
    
    # Bake
    bpy.ops.nla.bake(
        frame_start=frame_start, 
        frame_end=frame_end, 
        step=1, 
        only_selected=True,     
        visual_keying=True,     
        clear_constraints=True, 
        bake_types={'POSE'},
        use_current_action=True,
        channel_types={'LOCATION', 'ROTATION'} 
    )

    if limbs_map:
        first_ik_bone_name = list(limbs_map.keys())[0]
        
        if first_ik_bone_name in pose_bones:
            target_bone = pose_bones[first_ik_bone_name]
            # Insert keyframe to refresh viewport
            target_bone.keyframe_insert(data_path="location", group=first_ik_bone_name)     
    
    _clear_bones_data(rig_armature, CLEAR_BONES)
    
def _clear_bones_data(arm, bones):

    if arm.animation_data and (action := arm.animation_data.action):
        for fc in [
            fc
            for fc in action.fcurves
            if any(fc.data_path.startswith(f'pose.bones["{b}"]') for b in bones)
        ]:
            action.fcurves.remove(fc)

    for name in bones:
        if pb := arm.pose.bones.get(name):
            pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)
            if hasattr(pb, "rotation_quaternion"):
                pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.rotation_axis_angle = (0, 0, 1, 0)

# Bake Arm Offset empties      
def bake_offset_empties(original_armature, rig_armature, armoff_map):            
    context = bpy.context
    bpy.ops.object.mode_set(mode='OBJECT')
    
    temp_objects = []
    bpy.ops.object.select_all(action='DESELECT')  
    for bone_name, orig_bone_name in armoff_map.items(): 
        parent_dummy = bpy.data.objects.new(f"{bone_name}_(TEMP)", None)
        parent_dummy.empty_display_type = 'PLAIN_AXES'
        parent_dummy.location = Vector((0.0, 0.0, 0.0))
        bpy.context.collection.objects.link(parent_dummy)
        
        copy_loc = parent_dummy.constraints.new(type='COPY_LOCATION')
        copy_loc.target = original_armature
        copy_loc.subtarget = orig_bone_name
        copy_rot = parent_dummy.constraints.new(type='COPY_ROTATION')
        copy_rot.target = original_armature
        copy_rot.subtarget = orig_bone_name
        
        parent_dummy.select_set(True)
        temp_objects.append(parent_dummy)
    
    bpy.context.view_layer.update()

    if temp_objects:
        context.view_layer.objects.active = temp_objects[0]   
    
    bpy.ops.nla.bake(
        frame_start=bpy.context.scene.frame_start, 
        frame_end=bpy.context.scene.frame_end, 
        step=1, 
        only_selected=True, 
        visual_keying=True, 
        clear_constraints=True, 
        clear_parents=False,
        bake_types={'OBJECT'}
    )       

# Set Arm Offset constraints
def bake_offset_constraints(original_armature, rig_armature, armoff_map):  
          
    if not rig_armature.animation_data or not rig_armature.animation_data.action:
        return []
        
    context = bpy.context
    bpy.ops.object.mode_set(mode='OBJECT')   
    bpy.ops.object.select_all(action='DESELECT')
    rig_armature.select_set(True)
    context.view_layer.objects.active = rig_armature
    bpy.ops.object.mode_set(mode='POSE')
    
    pose_bones = rig_armature.pose.bones

    for bone in pose_bones:
        bone.bone.select = False

    for bone_name, orig_bone_name in armoff_map.items(): 
        if bone_name in pose_bones:
            off_bone = pose_bones[bone_name]
            
            off_bone.bone.select = True

            if off_bone.rotation_mode == 'QUATERNION':
                off_bone.keyframe_insert(data_path="rotation_quaternion", group=bone_name)
            else:
                off_bone.keyframe_insert(data_path="rotation_euler", group=bone_name)
            
            
            constraint = off_bone.constraints.new(type='COPY_ROTATION')
            constraint.target = bpy.data.objects.get(bone_name + "_(TEMP)")               
         
            constraint.name = f"Bake_Temp_{orig_bone_name} (OFF)"
   
    context.view_layer.update()

    frame_start = context.scene.frame_start
    frame_end = context.scene.frame_end

    bpy.ops.nla.bake(
        frame_start=frame_start, 
        frame_end=frame_end, 
        step=1, 
        only_selected=True,     
        visual_keying=True,     
        clear_constraints=True, 
        bake_types={'POSE'},
        use_current_action=True,
        channel_types={'ROTATION'} 
    )
    
    bpy.ops.object.mode_set(mode='OBJECT')
