import bpy
import math
import mathutils
from mathutils import Vector

BONES_TO_INSERT = [
'ude1_r_n', 'ude2_r_n', 'ude3_r_n',
'ude1_l_n', 'ude2_l_n', 'ude3_l_n',
'asi1_r_n', 'asi2_r_n', 'asi3_r_n',
'asi1_l_n', 'asi2_l_n', 'asi3_l_n',
'ketu_c_n', 'ketu_n',
'center_c_n', 'center_n'
]

RIG_BONES = {
    'Hand IK R': 'ude3_r_n',
    'Hand IK L': 'ude3_l_n',
    'Foot IK R': 'asi3_r_n',
    'Foot IK L': 'asi3_l_n',
    'ude1_Of_r_n': 'ude1_r_n',
    'ude2_Of_r_n': 'ude2_r_n',
    'ude1_Of_l_n': 'ude1_l_n',
    'ude2_Of_l_n': 'ude2_l_n',
    'Hip': 'ketu_c_n'
}

RIG_BONES_OE = {
    'Hand IK R': 'ude3_r_n',
    'Hand IK L': 'ude3_l_n',
    'Foot IK R': 'asi3_r_n',
    'Foot IK L': 'asi3_l_n',
    'ude1_Of_r_n': 'ude1_r_n',
    'ude2_Of_r_n': 'ude2_r_n',
    'ude1_Of_l_n': 'ude1_l_n',
    'ude2_Of_l_n': 'ude2_l_n'
}

RIG_BONES_OOE = {
    'Hand IK R': 'ude3_r_n',
    'Hand IK L': 'ude3_l_n',
    'Foot IK R': 'asi3_r_n',
    'Foot IK L': 'asi3_l_n',
    'ude1_Of_r_n': 'ude1_r_n',
    'ude2_Of_r_n': 'ude2_r_n',
    'ude1_Of_l_n': 'ude1_l_n',
    'ude2_Of_l_n': 'ude2_l_n'
}

IK_LIMBS = {
    'Hand IK R': ('ude2_r_n', 'Arm Pole R'),
    'Hand IK L': ('ude2_l_n', 'Arm Pole L'),
    'Foot IK R': ('asi2_r_n', 'Leg Pole R'),
    'Foot IK L': ('asi2_l_n', 'Leg Pole L')
}

ArmOff_BONES = {
    'ude1_Of_r_n': 'ude1_r_n',
    'ude2_Of_r_n': 'ude2_r_n',
    'ude1_Of_l_n': 'ude1_l_n',
    'ude2_Of_l_n': 'ude2_l_n'
}

HIP_BONES = [
    'Hip',
    'kosi_c_n',
    'ketu_c_n'
]

HIP_BONES_OE = [
    'Hip',
    'kosi_c_n',
    'ketu_c_n'
]

RENAME_BONES = {
    # OE/DE
    'pelvis': 'ketu_c_n', 
    'spine1': 'kosi_c_n',
    'spine2': 'mune_c_n',
    'neck' : 'kubi_c_n',
    'head' : 'face_c_n',
    
    'shoulder r' : 'kata_r_n', 
    'shoulder l' : 'kata_l_n',
    'arm1 r': 'ude1_r_n',
    'arm1 l': 'ude1_l_n',
    'arm2 r': 'ude2_r_n',
    'arm2 l': 'ude2_l_n',
    'hand r': 'ude3_r_n',
    'hand l': 'ude3_l_n',
    
    'leg1 r': 'asi1_r_n',
    'leg1 l': 'asi1_l_n',
    'leg2 r': 'asi2_r_n',
    'leg2 l': 'asi2_l_n',
    'leg3 r': 'asi3_r_n',
    'leg3 l': 'asi3_l_n',
    'toe r': 'asi4_r_n',
    'toe l': 'asi4_l_n',
}

RENAME_BONES_OOE = {
    'pelvis': 'ketu_n', 
    'spine1': 'kosi_n',
    'spine2': 'mune_n',
    'neck' : 'kubi_n',
    'head' : 'face'  
}

RENAME_PATTERNS = {
    '_r_n': ' r',
    '_l_n': ' l',
    '_r_sup': '_sup r',
    '_l_sup': '_sup l',    
    '_r': ' r',
    '_l': ' l',
}

RENAME_PATTERNS_FING = {
    'koyu0': 'carpal4',
    'kou': 'carpal',    
    'naka0': 'carpal3',    
    'kusu0': 'carpal2', 
    'hito0': 'carpal1',    
    'koyu': 'pinky',
    'naka': 'middle',
    'kusu': 'ring',
    'hito': 'index',
    'oya': 'thumb'   
}

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

    # Create Root bone for OE/OOE
    engine = armature.data.get("derig_eng", 0)
    if engine != 1:
        root_bone = edit_bones.new(name="Root")
        root_bone.head, root_bone.tail = (0, 0, 0), (0, 0, 0.0001)
        
        hip_name = "center_n" if engine == 3 else "center_c_n"
        edit_bones[hip_name].parent = root_bone
    
    for new_name, source_bone_name in bones_dict.items():
        if source_bone_name in edit_bones:           
            source_bone = edit_bones[source_bone_name]
            
            new_bone = edit_bones.new(new_name)
            new_bone.head = source_bone.head.copy()
            new_bone.tail = source_bone.tail.copy()
            new_bone.roll = source_bone.roll
            new_bone.use_connect = source_bone.use_connect
            new_bone.use_deform = False 
            new_bone.parent = edit_bones["center_c_n"] if engine == 1 else root_bone
        else:
            print(f"Bone '{source_bone_name}' not found!")

    # Parent Arm Offset bones
    edit_bones['ude1_Of_r_n'].parent = edit_bones['ude1_r_n']
    edit_bones['ude2_Of_r_n'].parent = edit_bones['ude2_r_n']
    edit_bones['ude1_Of_l_n'].parent = edit_bones['ude1_l_n']
    edit_bones['ude2_Of_l_n'].parent = edit_bones['ude2_l_n'] 
            
    bpy.ops.object.mode_set(mode='OBJECT')

    # Create Pole bones
    _create_pole_bone(armature, "asi2_r_n", "Leg Pole R")     
    _create_pole_bone(armature, "asi2_l_n", "Leg Pole L")  
    _create_pole_bone(armature, "ude2_r_n", "Arm Pole R")  
    _create_pole_bone(armature, "ude2_l_n", "Arm Pole L")
    
    

def add_rot_constraints(ik_armature, bones_map):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    ik_armature.select_set(True)
    bpy.context.view_layer.objects.active = ik_armature
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = ik_armature.pose.bones
    
    for index, (new_name, source_bone_name) in enumerate(bones_map.items()):
        
        if not " IK " in new_name:
            break
        
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
    
    for new_name, (source_bone_name, pole_name) in limbs_map.items():
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
            
            constraint.pole_target = ik_armature
            constraint.pole_subtarget = pole_name
            constraint.pole_angle = math.radians(-90)
            
        else:
            print(f"Bone '{source_bone_name}' not found!")  

    # Calculate Pole angles
    _calculate_pole_angle(ik_armature, "asi2_r_n")
    _calculate_pole_angle(ik_armature, "asi2_l_n")
    _calculate_pole_angle(ik_armature, "ude2_r_n")
    _calculate_pole_angle(ik_armature, "ude2_l_n")        
    bpy.ops.object.mode_set(mode='OBJECT')
    
def apply_joints_offset(context, ik_armature, limbs_map):
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = ik_armature.data.edit_bones
    
    elbow_offset = context.scene.elbow_offset
    knee_offset = context.scene.knee_offset
    
    limbs_list = list(limbs_map.items())
    
    for index, (new_name, (source_bone_name, _)) in enumerate(limbs_list):
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
    
# Transfer keyframes to Hip

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
    
# Link original armature   
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

    # Change constraint targets for Arm bones
    _set_constraint_subtarget(original_armature, 'ude1_r_n','ude1_Of_r_n')
    _set_constraint_subtarget(original_armature, 'ude2_r_n','ude2_Of_r_n')
    _set_constraint_subtarget(original_armature, 'ude1_l_n','ude1_Of_l_n')
    _set_constraint_subtarget(original_armature, 'ude2_l_n','ude2_Of_l_n')
    
    _delete_temp_objects()
    
    bpy.ops.object.mode_set(mode='OBJECT')
    ik_armature.data["derig_status"] = 2    
    
def rename_bones(obj):
    armature_data = obj.data
    
    active_renamer = RENAME_BONES.copy()    
    if armature_data.get("derig_eng", 0) == 3:
        active_renamer.update(RENAME_BONES_OOE)    
    
    # Rename center bone for OE/OOE
    if armature_data.get("derig_eng", 0) != 1:
        hip_bone = armature_data.bones.get("center_n") or armature_data.bones.get("center_c_n")
        hip_bone.name = "Hip" 
        
    # Main bones
    for new_name, old_name in active_renamer.items():
        bone = armature_data.bones.get(old_name)
        if bone:
            bone.name = new_name

    # Other bones
    for bone in armature_data.bones:
        for old_suffix, new_suffix in RENAME_PATTERNS.items():
            if bone.name.endswith(old_suffix):
                bone.name = bone.name[:-len(old_suffix)] + new_suffix
                break
    # Fingers            
        for old_fing, new_fing in RENAME_PATTERNS_FING.items():
            if old_fing in bone.name:
                bone.name = bone.name.replace(old_fing, new_fing)
                break
                
def _create_pole_bone(armature_obj, base_bone_name, bone_name, length=0.5):
    armature_obj.data.pose_position = 'REST'
    bpy.context.view_layer.update()


    # Setup temporary empties for tracking position and rotation
    parent_dummy = bpy.data.objects.new(f"{base_bone_name}_Parent_(TEMP)", None)
    parent_dummy.empty_display_type = 'PLAIN_AXES'
    parent_dummy.location = Vector((0.0, 0.0, 0.0))
    bpy.context.collection.objects.link(parent_dummy)

    child_dummy = bpy.data.objects.new(f"{base_bone_name}_Child_(TEMP)", None)
    child_dummy.empty_display_type = 'CUBE'
    
    name_lower = base_bone_name.lower()
    if name_lower.startswith("asi"):
        child_dummy.location = Vector((0.0, 0.0, -2.0))
    else:
        child_dummy.location = Vector((0.0, -2.0, 0.0))

    bpy.context.collection.objects.link(child_dummy)
    child_dummy.parent = parent_dummy
    
    copy_loc = parent_dummy.constraints.new(type='COPY_LOCATION')
    copy_loc.target = armature_obj
    copy_loc.subtarget = base_bone_name

    copy_rot = parent_dummy.constraints.new(type='COPY_ROTATION')
    copy_rot.target = armature_obj
    copy_rot.subtarget = base_bone_name

    bpy.context.view_layer.update()
    
    # Create the pole bone in edit mode
    world_parent_pos = parent_dummy.matrix_world.translation.copy()
    local_parent_center = armature_obj.matrix_world.inverted() @ world_parent_pos

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    edit_bones = armature_obj.data.edit_bones
    pole = edit_bones.new(bone_name)
    
    pole.head = (local_parent_center.x, local_parent_center.y - 1.0, local_parent_center.z)
    pole.tail = (pole.head.x, pole.head.y - length, pole.head.z)

    if armature_obj.data.get("derig_eng", 0) == 1:
        parent_bone = edit_bones.get("center_c_n")
    else:
        parent_bone = edit_bones.get("Root")            
        
    if parent_bone:
        pole.parent = parent_bone
        pole.use_connect = False 

    bpy.ops.armature.select_all(action='DESELECT')
    pole.select = True
    pole.select_head = True
    pole.select_tail = True
    edit_bones.active = pole
    
    bpy.ops.object.mode_set(mode='OBJECT')    
    armature_obj.data.pose_position = 'POSE'
    bpy.context.view_layer.update()

def _calculate_pole_angle(armature_obj, ik_bone_name):
    bpy.context.view_layer.objects.active = armature_obj
    current_mode = armature_obj.mode
    bpy.ops.object.mode_set(mode='POSE')
    
    p_bones = armature_obj.pose.bones
    ik_bone = p_bones.get(ik_bone_name)
    
    ik_constraint = next((c for c in ik_bone.constraints if c.type == 'IK'), None)

    saved_transforms = {}
    for pb in p_bones:
        saved_transforms[pb.name] = {
            'loc': pb.location.copy(),
            'rot_e': pb.rotation_euler.copy(),
            'rot_q': pb.rotation_quaternion.copy(),
            'rot_a': pb.rotation_axis_angle[:],
            'scale': pb.scale.copy()
        }

    for pb in p_bones:
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)

    saved_pole_target = ik_constraint.pole_target
    ik_constraint.pole_target = None
    
    bpy.context.view_layer.update()
    initial_world_matrix = ik_bone.matrix.copy()

    ik_constraint.pole_target = saved_pole_target
    ik_constraint.pole_angle = 0.0
    
    bpy.context.view_layer.update()
    broken_world_matrix = ik_bone.matrix.copy()

    matrix_delta = broken_world_matrix.inverted() @ initial_world_matrix
    local_euler = matrix_delta.to_euler('YXZ') 
    calculated_angle = local_euler.y
    
    ik_constraint.pole_angle = calculated_angle

    for pb in p_bones:
        if pb.name in saved_transforms:
            tf = saved_transforms[pb.name]
            pb.location = tf['loc']
            pb.rotation_euler = tf['rot_e']
            pb.rotation_quaternion = tf['rot_q']
            pb.rotation_axis_angle = tf['rot_a']
            pb.scale = tf['scale']

    bpy.context.view_layer.update()
    
    bpy.ops.object.mode_set(mode=current_mode)
    return calculated_angle
    
def mirror_anim(armature_obj):

    bpy.ops.object.mode_set(mode='POSE')
    
    scene = bpy.context.scene
    start_frame = scene.frame_start
    end_frame = scene.frame_end
    current_frame = scene.frame_current

    if hasattr(armature_obj.data, "collections"):
        for coll in armature_obj.data.collections:
            coll.is_visible = True 
            coll.is_solo = False   

    for p_bone in armature_obj.pose.bones:
        p_bone.bone.hide = False

    bpy.ops.pose.select_all(action='SELECT')

    if not armature_obj.animation_data or not armature_obj.animation_data.action:
        print("Action not found!")
        return False

    animation_data_buffer = {}
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        
        frame_poses = {}
        for p_bone in armature_obj.pose.bones:
            frame_poses[p_bone.name] = p_bone.matrix_basis.copy()
            
        animation_data_buffer[frame] = frame_poses

    for frame, bones_matrices in animation_data_buffer.items():
        scene.frame_set(frame)

        for bone_name, matrix in bones_matrices.items():
            if bone_name in armature_obj.pose.bones:
                armature_obj.pose.bones[bone_name].matrix_basis = matrix
                
        bpy.context.view_layer.update()
        
        bpy.ops.pose.copy()
        bpy.ops.pose.paste(flipped=True)
        
        bpy.ops.anim.keyframe_insert(type='LocRotScale')

    scene.frame_set(current_frame)
    
    p_bone = bpy.context.active_pose_bone

    if p_bone and "pat1_left_hand" in p_bone and "pat1_right_hand" in p_bone:
        p_bone["pat1_left_hand"], p_bone["pat1_right_hand"] = p_bone["pat1_right_hand"], p_bone["pat1_left_hand"]
    
    bpy.context.view_layer.update()

    return True

def separate_ketu(arm, target="ketu_c_n", center="center_c_n"):
    scene = bpy.context.scene
    frames = {
        "frame_start": scene.frame_start, 
        "frame_end": scene.frame_end, 
        "step": 1, 
        "only_selected": True, 
        "visual_keying": True, 
        "clear_constraints": True, 
        "channel_types": {'LOCATION', 'ROTATION'}
    }

    mt = bpy.data.objects.new("Bake_MT", None)
    bpy.context.collection.objects.link(mt)
    mt.constraints.new('COPY_TRANSFORMS').target, mt.constraints.get("Copy Transforms").subtarget = arm, target
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    mt.select_set(True)
    bpy.context.view_layer.objects.active = mt
    bpy.ops.nla.bake(**frames, bake_types={'OBJECT'})
    
    if arm.animation_data and arm.animation_data.action:
        act = arm.animation_data.action
        for fc in [fc for fc in act.fcurves if any(fc.data_path.startswith(f'pose.bones["{b}"]') for b in [target, center])]:
            act.fcurves.remove(fc)

    b_k, b_c = arm.pose.bones.get(target), arm.pose.bones.get(center)
    if b_k:
        c_z = b_k.constraints.new('COPY_LOCATION')
        c_z.target, c_z.use_x, c_z.use_y = mt, False, False
        b_k.constraints.new('COPY_ROTATION').target = mt
    if b_c:
        c_xy = b_c.constraints.new('COPY_LOCATION')
        c_xy.target, c_xy.use_z = mt, False

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    
    for b in arm.pose.bones: 
        b.bone.select = b.name in [target, center]
        
    cur_f = scene.frame_current
    scene.frame_set(scene.frame_start)
    for b in [b_k, b_c]:
        if b:
            for p in ["location", "rotation_quaternion"]: b.keyframe_insert(data_path=p)
    scene.frame_set(cur_f)
        
    bpy.ops.nla.bake(**frames, bake_types={'POSE'}, use_current_action=True)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(mt, do_unlink=True)
    return True

def _set_constraint_subtarget(arm_obj, bone_name, target, constraint_name="CopyTransforms_QR"):
    bpy.ops.object.mode_set(mode='POSE')
    obj = bpy.context.active_object
    bone = arm_obj.pose.bones.get(bone_name)
    if bone:
        const = bone.constraints.get(constraint_name)
        if const and hasattr(const, "subtarget"):
            const.subtarget = target
    bpy.ops.object.mode_set(mode='OBJECT')
    
def _add_damped_track(bone_name, target):
    bpy.ops.object.mode_set(mode='POSE')
    obj = bpy.context.active_object
    bone = obj.pose.bones.get(bone_name)
    if bone and target in obj.pose.bones:
        const = bone.constraints.new(type='DAMPED_TRACK')
        const.target = obj
        const.subtarget = target
    bpy.ops.object.mode_set(mode='OBJECT')

def _delete_temp_objects():
    bpy.ops.object.mode_set(mode='OBJECT')
    temp_objects = [obj for obj in bpy.data.objects if obj.name.endswith("(TEMP)")]
    for obj in temp_objects:
        bpy.data.objects.remove(obj, do_unlink=True)

def add_keys_if_empty(arm_obj, bone_map):
    if not arm_obj.animation_data or not arm_obj.animation_data.action:
        return []

    action = arm_obj.animation_data.action
    fcurves_paths = {fc.data_path for fc in action.fcurves} if action else set()

    for name in bone_map:
        p_bone = arm_obj.pose.bones.get(name)
        if p_bone and not any(f'pose.bones["{name}"]' in path for path in fcurves_paths):
            for transform in ('location', 'rotation_quaternion', 'scale'):
                p_bone.keyframe_insert(data_path=transform, frame=1)
