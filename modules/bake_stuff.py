import bpy

def setup_bake_constraints(context, rig_armature, original_armature, limbs_map):
    
    bpy.ops.object.mode_set(mode='OBJECT')  
      
    bpy.ops.object.select_all(action='DESELECT')
    rig_armature.select_set(True)
    context.view_layer.objects.active = rig_armature
    bpy.ops.object.mode_set(mode='POSE')
    
    pose_bones = rig_armature.pose.bones
    
    enabled_constraints = []
    for bone in pose_bones:
        for constraint in bone.constraints:
            if constraint.enabled:
                enabled_constraints.append(constraint)
                constraint.enabled = False
            
    temporary_constraints = []
    for index, (ik_bone_name, orig_bone_name) in enumerate(limbs_map.items()):
        if index == 4: # 4 is Hip bone
            break
            
        if ik_bone_name in pose_bones:
            ik_bone = pose_bones[ik_bone_name]
            
            ik_bone.keyframe_insert(data_path="location", group=ik_bone_name)
            if ik_bone.rotation_mode == 'QUATERNION':
                ik_bone.keyframe_insert(data_path="rotation_quaternion", group=ik_bone_name)
            else:
                ik_bone.keyframe_insert(data_path="rotation_euler", group=ik_bone_name)
            
            constraint = ik_bone.constraints.new(type='COPY_TRANSFORMS')
            constraint.target = rig_armature   
            constraint.subtarget = orig_bone_name   
            constraint.mix_mode = 'REPLACE'         
            constraint.target_space = 'WORLD'       
            constraint.owner_space = 'WORLD'        
            constraint.name = f"Bake_Temp_{orig_bone_name}"
            
            temporary_constraints.append((ik_bone, constraint))
            
    context.view_layer.update()
            
    for bone in pose_bones:
        bone.bone.select = False
        
    for ik_bone, constraint in temporary_constraints:
        ik_bone.bone.select = True
    
    frame_start = context.scene.frame_start
    frame_end = context.scene.frame_end
    
    bpy.ops.nla.bake(
        frame_start=frame_start, 
        frame_end=frame_end, 
        step=1, 
        only_selected=True,     
        visual_keying=True,     
        clear_constraints=False, 
        bake_types={'POSE'},
        use_current_action=True,
        channel_types={'LOCATION', 'ROTATION'} 
    )
    
    for ik_bone, constraint in temporary_constraints:
        ik_bone.constraints.remove(constraint)
        ik_bone.bone.select = False
        
    for constraint in enabled_constraints:
        constraint.enabled = True

    if limbs_map:
        first_ik_bone_name = list(limbs_map.keys())[0]
        
        if first_ik_bone_name in pose_bones:
            target_bone = pose_bones[first_ik_bone_name]
            # Insert keyframe to refresh viewport
            target_bone.keyframe_insert(data_path="location", group=first_ik_bone_name)     
            
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
