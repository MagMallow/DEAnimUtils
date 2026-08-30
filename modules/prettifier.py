import bpy
import os

MAIN = [
'ketu_c_n', 'asi1_r_n', 'asi1_l_n', 'kosi_c_n', 'mune_c_n', 'kata_r_n', 
'ude1_r_n', 'kata_l_n', 'ude1_l_n', 'kubi_c_n', 'face_c_n',
'Hand IK R', 'Hand IK L', 'Foot IK R', 'Foot IK L', 'Hip'
]

TWIST = [
'asi1_twist_r_sup', 'asi1_twist_l_sup', 'ude2_twist_r_sup', 'ude2_twist1_r_sup',
'ude2_twist2_r_sup', 'kata_twist_r_sup', 'ude1_twist1_r_sup', 'ude1_twist2_r_sup',
'ude2_twist_l_sup', 'ude2_twist1_l_sup', 'ude2_twist2_l_sup', 'kata_twist_l_sup',
'ude1_twist1_l_sup', 'ude1_twist2_l_sup', 'asi2_r_sup', 'asi2_l_sup', 'ketu_r_sup',
'ketu_l_sup', 'ude3_bend_r_sup', 'elbow_r_sup', 'kata_pad_r_sup', 'ude3_bend_l_sup',
'elbow_l_sup', 'kata_pad_l_sup', 'eri_r_sup', 'eri_l_sup', 'tie_c_sup', 'waki_r_sup',
'waki_l_sup', 'munemus_r_sup', 'munemus_l_sup', 'kubiaccehi_c_sup', 'kubiaccehi_r_sup',
'kubiaccehi_l_sup', 'kubiaccelo_c_sup', 'kubiaccelo_r_sup', 'kubiaccelo_l_sup'
]

FACE =[
'_brow_c_n', '_eyebrow_r_n', '_eyebrow2_r_n', '_eyebrow3_r_n', '_eyebrow_l_n',
'_eyebrow2_l_n', '_eyebrow3_l_n', '_eyelid_r_n', '_eyelid2_r_n', '_eyelid_l_n',
'_eyelid2_l_n', '_eye_r_n', '_eye_l_n', '_eyelid_und_r_n', '_eyelid_und2_r_n',
'_eyelid_und_l_n', '_eyelid_und2_l_n', '_throat_c_n', '_jaw_c_n', '_chin_c_n',
'_chin_r_n', '_chin_l_n', '_chin_btm_c_n', '_cheek_btm1_r_n', '_cheek_btm1_l_n',
'_lip_btm1_c_n', '_lip_btm2_c_n', '_lip_btm1_r_n', '_lip_btm2_r_n', '_lip_btm1_l_n',
'_lip_btm2_l_n', '_lip_btm_side1_r_n', '_lip_btm_side2_r_n', '_lip_btm_side1_l_n',
'_lip_btm_side2_l_n', '_tooth_btm_c_n', '_lip_side_r_n', '_lip_side_l_n',
'_lip_top1_c_n', '_lip_top2_c_n', '_lip_top1_r_n', '_lip_top2_r_n',
'_lip_top1_l_n', '_lip_top2_l_n', '_lip_top_side1_r_n', '_lip_top_side2_r_n',
'_lip_top_side1_l_n', '_lip_top_side2_l_n', '_nose_top_c_n', '_nose_side_r_n',
'_nose_side_l_n', '_cheek1_r_n', '_cheek2_r_n', '_cheek3_r_n', '_cheek4_r_n',
'_cheek5_r_n', '_cheek1_l_n', '_cheek2_l_n', '_cheek3_l_n', '_cheek4_l_n',
'_cheek5_l_n', '_tooth_top_c_n', '_cheek_btm2_r_n', '_cheek_btm2_l_n',
'eri_r_n', 'eri_l_n', 'kubiaccehi_c_n', 'kubiaccehi_r_n', 'kubiaccehi_l_n',
'kubiaccelo_c_n', 'kubiaccelo_r_n', 'kubiaccelo_l_n'
]

FINGERS = [
'koyu0_r_n', 'koyu1_r_n', 'koyu2_r_n', 'koyu3_r_n', 'kusu0_r_n',
'kusu1_r_n', 'kusu2_r_n', 'kusu3_r_n', 'naka0_r_n', 'naka1_r_n', 'naka2_r_n',
'naka3_r_n', 'hito0_r_n', 'hito1_r_n', 'hito2_r_n', 'hito3_r_n', 'oya1_r_n',
'oya2_r_n', 'oya3_r_n', 'koyu0_l_n', 'koyu1_l_n', 'koyu2_l_n', 'koyu3_l_n',
'kusu0_l_n', 'kusu1_l_n', 'kusu2_l_n', 'kusu3_l_n', 'naka0_l_n', 'naka1_l_n',
'naka2_l_n', 'naka3_l_n', 'hito0_l_n', 'hito1_l_n', 'hito2_l_n', 'hito3_l_n',
'oya1_l_n', 'oya2_l_n', 'oya3_l_n'
]

DE = [
'buki1_r_n', 'buki2_r_n', 'buki1_l_n', 'buki2_l_n', 'buki1_c_n',
'buki2_c_n', 'vector_c_n', 'pattern_c_n', 'sync_c_n', 'center_c_n'
]

# MISC = [
# 'asi4_r_n', 'asi4_l_n', 'pocket_r_n', 'pocket_l_n',
# 'ude2_r_n', 'ude3_r_n', 'ude2_l_n', 'ude3_l_n', 'backhair_mune_c_n',
# 'backhair_kubi_c_n', 'tie_c_n', 'asi2_r_n', 'asi2_l_n', 'asi3_r_n', 'asi3_l_n'
# ]

MISC = [ ]
  
def create_bone_collections_from_lists(rig_armature):
    
    distributed_bones = set()
    
    for b_list in [MAIN, TWIST, FACE, FINGERS, DE]:
        for b_name in b_list:
            distributed_bones.add(b_name)
            
    for bone in rig_armature.data.bones:
        if bone.name.endswith("_phy"):
            distributed_bones.add(bone.name)
            
    all_armature_bones = {b.name for b in rig_armature.data.bones}
    unassigned_bones = all_armature_bones - distributed_bones
    
    global MISC
    MISC = list(set(MISC) | unassigned_bones)

    lists_data = {
        "Main": MAIN,
        "Twist": TWIST,
        "Face": FACE,
        "Fingers": FINGERS,
        "DE": DE,
        "Misc": MISC 
    }

    arm_data = rig_armature.data
    
    for list_name_str, bones_list in lists_data.items():
        bone_coll = arm_data.collections.get(list_name_str)
        if not bone_coll:
            bone_coll = arm_data.collections.new(name=list_name_str)
            
        for bone_name in bones_list:
            if bone_name in arm_data.bones:
                bone = arm_data.bones[bone_name]
                bone_coll.assign(bone)
    
    phys_coll_name = "Phys"
    
    for bone in arm_data.bones:
        if bone.name.endswith("_phy"):
            phys_coll = arm_data.collections.get(phys_coll_name)
            if not phys_coll:
                phys_coll = arm_data.collections.new(name=phys_coll_name)
            
            phys_coll.assign(bone)
                
    arm_data.collections_all["Main"].is_solo = True

def apply_bone_widgets(context, rig_armature):

    check_widgets()

    widgets_map = {
    "Hand IK R": ('THEME02', "cs_hand_r"),
    "Hand IK L": ('THEME03', "cs_hand_l"),
    "Foot IK R": ('THEME02', "cs_foot"),
    "Foot IK L": ('THEME03', "cs_foot"), 
    "Hip": ('THEME11', "cs_sphere"),
    "ketu_c_n": ('THEME12', "cs_circle"), 
    "ude1_r_n":('THEME04', "cs_box"),  
    "ude1_l_n":('THEME09', "cs_box"), 
    "asi1_r_n":('THEME04', "cs_box.001"),  
    "asi1_l_n":('THEME09', "cs_box.001"),          
    }   
     
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = rig_armature.pose.bones
    
    widgets_collection = context.scene.collection.children.get("Widgets")
    
    for bone_name, settings in widgets_map.items():
        if bone_name in pose_bones:
            p_bone = pose_bones[bone_name]
            
            theme_name = settings[0]       
            widget_mesh_name = settings[1]
            
            p_bone.color.palette = theme_name
            
            if widgets_collection and widget_mesh_name in widgets_collection.objects:
                widget_obj = widgets_collection.objects[widget_mesh_name]
                p_bone.custom_shape = widget_obj
                p_bone.use_custom_shape_bone_size = True

    bpy.ops.object.mode_set(mode='OBJECT')

def check_widgets():

    if "Widgets" in bpy.data.collections:
        return True

    lib_path = bpy.context.preferences.filepaths.asset_libraries["DE Hand Patterns"].path
    path_to_blend = os.path.join(lib_path, "hand_patterns.blend")

    try:
        bpy.ops.wm.append(
            filepath=os.path.join(path_to_blend, "Collection", "Widgets"),
            directory=os.path.join(path_to_blend, "Collection"),
            filename="Widgets"
        )
        
        widgets_coll = bpy.data.collections.get("Widgets")
        if widgets_coll:
            widgets_coll.hide_viewport = True
            widgets_coll.hide_render = True
            
            if widgets_coll.name not in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.link(widgets_coll)
                
        return True

    except Exception as e:
        print(f"Failed to import widget collection: {str(e)}")
        return False