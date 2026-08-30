import bpy

CONNECT_BONES = {
# Spine
'ketu_c_n': 'asi1_r_n',
'kosi_c_n': 'mune_c_n',
'mune_c_n': 'kubi_c_n',
'kubi_c_n': 'face_c_n',
'face_c_n': 'brow_c_n',
# Right Leg
'asi1_r_n': 'asi2_r_n',
'asi2_r_n': 'asi3_r_n',
'asi3_r_n': 'asi4_r_n',
# Left Leg
'asi1_l_n': 'asi2_l_n',
'asi2_l_n': 'asi3_l_n',
'asi3_l_n': 'asi4_l_n',
# Right Arm
'kata_r_n': 'ude1_r_n',
'ude1_r_n': 'ude2_r_n',
'ude2_r_n': 'ude3_r_n',
'ude3_r_n': 'koyu0_r_n',
# Left Arm
'kata_l_n': 'ude1_l_n',
'ude1_l_n': 'ude2_l_n',
'ude2_l_n': 'ude3_l_n',
'ude3_l_n': 'koyu0_l_n',
# Right Hand
'koyu0_r_n': 'koyu1_r_n',
'koyu1_r_n': 'koyu2_r_n',
'koyu2_r_n': 'koyu3_r_n',
'kusu0_r_n': 'kusu1_r_n',
'kusu1_r_n': 'kusu2_r_n',
'kusu2_r_n': 'kusu3_r_n',
'naka0_r_n': 'naka1_r_n',
'naka1_r_n': 'naka2_r_n',
'naka2_r_n': 'naka3_r_n',
'hito0_r_n': 'hito1_r_n',
'hito1_r_n': 'hito2_r_n',
'hito2_r_n': 'hito3_r_n',
'oya0_r_n': 'oya1_r_n',
'oya1_r_n': 'oya2_r_n',
'oya2_r_n': 'oya3_r_n',
# Left Hand
'koyu0_l_n': 'koyu1_l_n',
'koyu1_l_n': 'koyu2_l_n',
'koyu2_l_n': 'koyu3_l_n',
'kusu0_l_n': 'kusu1_l_n',
'kusu1_l_n': 'kusu2_l_n',
'kusu2_l_n': 'kusu3_l_n',
'naka0_l_n': 'naka1_l_n',
'naka1_l_n': 'naka2_l_n',
'naka2_l_n': 'naka3_l_n',
'hito0_l_n': 'hito1_l_n',
'hito1_l_n': 'hito2_l_n',
'hito2_l_n': 'hito3_l_n',
'oya0_l_n': 'oya1_l_n',
'oya1_l_n': 'oya2_l_n',
'oya2_l_n': 'oya3_l_n'
}

FLAT_BONES = [
'koyu3_r_n', 'kusu3_r_n', 'naka3_r_n', 'hito3_r_n', 'oya3_r_n', 
'koyu3_l_n', 'kusu3_l_n', 'naka3_l_n', 'hito3_l_n', 'oya3_l_n'
]

def prepare_armature(armature_obj):

    bpy.ops.object.mode_set(mode='OBJECT')  
    
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return
        
    original_mode = armature_obj.mode
    
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    edit_bones = armature_obj.data.edit_bones
    
    # Connect bone tails (CONNECT_BONES)
    if CONNECT_BONES:
        for parent_name, child_name in CONNECT_BONES.items():
            parent_bone = edit_bones.get(parent_name)
            child_bone = edit_bones.get(child_name)
            
            if not parent_bone:
                print(f"Parent bone '{parent_name}' not found!")
                continue
            if not child_bone:
                print(f"Child bone '{child_name}' not found!")
                continue

            if child_bone.parent != parent_bone:
                continue

            parent_bone.tail = child_bone.head.copy()

            for child in parent_bone.children:
                child.use_connect = False

    # Flatten X, Y (FLAT_BONES)
    if FLAT_BONES:
        for bone_name in FLAT_BONES:
            bone = edit_bones.get(bone_name)
            if not bone:
                print(f"Bone '{bone_name}' not found!")
                continue
                
            bone.tail.x = bone.head.x
            bone.tail.y = bone.head.y
            bone.tail.z = bone.head.z + 0.0001

    bpy.ops.object.mode_set(mode=original_mode)
