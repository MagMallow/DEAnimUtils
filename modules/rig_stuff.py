import bpy

RIG_BONES = {
    'Hand IK R': 'ude3_r_n',
    'Hand IK L': 'ude3_l_n',
    'Foot IK R': 'asi3_r_n',
    'Foot IK L': 'asi3_l_n',
    'Hip': 'ketu_c_n'  
}

IK_LIMBS = {
    'Hand IK R': 'ude2_r_n',
    'Hand IK L': 'ude2_l_n',
    'Foot IK R': 'asi2_r_n',
    'Foot IK L': 'asi2_l_n',
}

HIP_BONES = [
    'Hip',
    'kosi_c_n',
    'ketu_c_n'
]

def duplicate_armature(context, active_obj):
    
    bpy.ops.object.mode_set(mode='OBJECT')    
    bpy.ops.object.select_all(action='DESELECT')
    active_obj.select_set(True)
    context.view_layer.objects.active = active_obj
    
    bpy.ops.object.duplicate()
    ik_armature = context.active_object
    ik_armature.name = f"{active_obj.name} (RIG)"
    return ik_armature

def copy_bones_by_dict(armature, bones_dict):
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones
    
    for new_name, source_bone_name in bones_dict.items():
        if source_bone_name in edit_bones:
            source_bone = edit_bones[source_bone_name]
            
            new_bone = edit_bones.new(new_name)
            new_bone.head = source_bone.head.copy()
            new_bone.tail = source_bone.tail.copy()
            new_bone.roll = source_bone.roll
            new_bone.use_connect = source_bone.use_connect
            new_bone.use_deform = False 
            new_bone.parent = edit_bones["center_c_n"]
            new_bone.color.palette = 'THEME03'
        else:
            print(f"Bone '{source_bone_name}' not found!")
            
    bpy.ops.object.mode_set(mode='OBJECT')

def add_rot_constraints(ik_armature, bones_map):

    bpy.ops.object.select_all(action='DESELECT')
    ik_armature.select_set(True)
    bpy.context.view_layer.objects.active = ik_armature
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = ik_armature.pose.bones
    
    for index, (new_name, source_bone_name) in enumerate(bones_map.items()):
        
        if index == 4:
            continue
        
        if source_bone_name in pose_bones:
            p_bone = pose_bones[source_bone_name]
            constraint = p_bone.constraints.new(type='COPY_ROTATION')
            constraint.target = ik_armature
            constraint.subtarget = new_name      
            constraint.target_space = 'WORLD'
            constraint.owner_space = 'WORLD'
            constraint.name = f"Copy Rot from {new_name}"
        else:
            print(f"Bone '{source_bone_name}' not found!")  
            
    bpy.ops.object.mode_set(mode='OBJECT')

def add_ik_constraints(ik_armature, limbs_map):
    bpy.ops.object.select_all(action='DESELECT')
    ik_armature.select_set(True)
    bpy.context.view_layer.objects.active = ik_armature
    bpy.ops.object.mode_set(mode='POSE')
    
    pose_bones = ik_armature.pose.bones
    
    for new_name, source_bone_name in limbs_map.items():
        if source_bone_name in pose_bones:
            p_bone = pose_bones[source_bone_name]
            
            constraint = p_bone.constraints.new(type='IK')
            constraint.target = ik_armature         
            constraint.subtarget = new_name         
            constraint.iterations = 500             
            constraint.chain_count = 2              
            constraint.use_tail = True          
            constraint.use_stretch = True         
            constraint.weight = 1.0                 
            constraint.use_rotation = False  
            constraint.name = f"IK to {new_name}"
        else:
            print(f"Bone '{source_bone_name}' not found!")  
            
    bpy.ops.object.mode_set(mode='OBJECT')
    
def apply_joints_offset(context, ik_armature, limbs_map):
    
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = ik_armature.data.edit_bones
    
    elbow_offset = context.scene.elbow_offset
    knee_offset = context.scene.knee_offset
    
    limbs_list = list(limbs_map.items())
    
    for index, (new_name, source_bone_name) in enumerate(limbs_list):
        if source_bone_name in edit_bones:
            bone = edit_bones[source_bone_name]
            
            offset_y = elbow_offset if index < 2 else knee_offset
            bone.head.y += offset_y

            if bone.parent:
                bone.parent.tail.y += offset_y
                
    bpy.ops.object.mode_set(mode='OBJECT')    

def setup_hip_bone(ik_armature, hip_bones_list):

    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = ik_armature.data.edit_bones
    
    parent_bone_name = hip_bones_list[0]
    
    if parent_bone_name in edit_bones:
        parent_bone = edit_bones[parent_bone_name]
        
        for bone_name in hip_bones_list[1:]:
            if bone_name in edit_bones:
                child_bone = edit_bones[bone_name]
                child_bone.parent = parent_bone
                child_bone.use_connect = False
            else:
                print(f"Bone '{bone_name}' not found!")
    else:
        print(f"Bone '{parent_bone_name}' not found!")
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
### Transfer keyframes to Hip

def transfer_bone_animation(ik_armature, bones_map):
    
    source_bone_name = bones_map[2]
    target_bone_name = bones_map[0] 

    if not ik_armature.animation_data or not ik_armature.animation_data.action:
        return

    action = ik_armature.animation_data.action
    
    source_path_prefix = f'pose.bones["{source_bone_name}"].'
    target_path_prefix = f'pose.bones["{target_bone_name}"].'
    
    for curve in action.fcurves:
        if curve.data_path.startswith(source_path_prefix):
            new_path = curve.data_path.replace(source_path_prefix, target_path_prefix)
            
            existing_curve = action.fcurves.find(new_path, index=curve.array_index)
            if existing_curve:
                action.fcurves.remove(existing_curve)
                
            curve.data_path = new_path
            
    action.fcurves.update()

    # Reset the original bone
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = ik_armature.pose.bones
    
    if source_bone_name in pose_bones:
        p_bone = pose_bones[source_bone_name]
        p_bone.location = (0.0, 0.0, 0.0)
        if p_bone.rotation_mode == 'QUATERNION':
            p_bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        else:
            p_bone.rotation_euler = (0.0, 0.0, 0.0)
        p_bone.scale = (1.0, 1.0, 1.0)
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
### Link original armature   
def link_armatures_by_transforms(original_armature, ik_armature):
    
    bpy.ops.object.select_all(action='DESELECT')
    original_armature.select_set(True)
    bpy.context.view_layer.objects.active = original_armature
    bpy.ops.object.mode_set(mode='POSE')
    
    orig_pose_bones = original_armature.pose.bones
    ik_pose_bones = ik_armature.pose.bones
    
    for bone in orig_pose_bones:
        if bone.name in ik_pose_bones:
            
            constraint = bone.constraints.new(type='COPY_TRANSFORMS')
            constraint.target = ik_armature    
            constraint.subtarget = bone.name  
            constraint.mix_mode = 'REPLACE'   
            constraint.target_space = 'WORLD'
            constraint.owner_space = 'WORLD' 
            constraint.name = "CopyTransforms_QR"
            
    bpy.ops.object.mode_set(mode='OBJECT')
