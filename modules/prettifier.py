import bpy
import os
import re

MAIN = [
'Hip', 'pelvis', 'spine1', 'spine2', 'neck', 'head',
'shoulder r', 'shoulder l',
'Hand IK R', 'Hand IK L', 'Foot IK R', 'Foot IK L',
'Arm Pole R', 'Arm Pole L', 'Leg Pole R', 'Leg Pole L',
'toe r', 'toe l'
]

TWIST = [
'kubiaccelo_r_n', 'kubiaccehi_r_n', 'eri_r_n', 'kubiaccelo_c_n',
'kubiaccelo_l_n', 'kubiaccehi_l_n', 'eri_l_n', 'kubiaccehi_c_n'
'backhair_mune_c_n', 'pocket_n_r', 'pocket_n_r',
# OE
'sode_r_n', 'sode_l_n',
'eri_n_l', 'eri_n_l'
]

FINGERS_TAGS = [
'carpal', 'pinky',
'ring', 'middle', 
'index', 'thumb'
]

DE = [
'buki1_r_n', 'buki2_r_n', 'buki1_l_n', 'buki2_l_n', 'buki1_c_n',
'buki2_c_n', 'vector_c_n', 'pattern_c_n', 'sync_c_n', 'center_c_n',
'buki_r_n', 'buki_l_n', 'Root' # OE
]

MISC = [ ]
  
def create_bone_collections_from_lists(rig_armature):
    
    distributed_bones = set()
    
    for b_list in [MAIN, TWIST, DE]:
        for b_name in b_list:
            distributed_bones.add(b_name)
            
    arm_data = rig_armature.data 
    
    # Phys bones
    phys_coll = arm_data.collections.get("Phys")
    if not phys_coll:
        phys_coll = arm_data.collections.new(name="Phys")    

    for bone in arm_data.bones:
        if bone.name.endswith("_phy"):
            distributed_bones.add(bone.name)
            phys_coll.assign(bone)            

    # Twist bones
    twist_coll = arm_data.collections.get("Twist")
    if not twist_coll:
        twist_coll = arm_data.collections.new(name="Twist")    

    sup_ptr = re.compile(r"_sup_.$")
    for bone in arm_data.bones:
        if sup_ptr.search(bone.name):
            distributed_bones.add(bone.name)
            twist_coll.assign(bone)            
 
    # Face bones
    target_bone = arm_data.bones.get("head") 
    
    face_coll = arm_data.collections.get("Face")    
    if not face_coll:
        face_coll = arm_data.collections.new(name="Face")  
    
    for child in target_bone.children_recursive:
        face_coll.assign(child)
        distributed_bones.add(child.name)        

    # Collect Finger bones
    fingers = []
    for bone in arm_data.bones:
        if any(part in bone.name for part in FINGERS_TAGS):
            fingers.append(bone.name)
            distributed_bones.add(bone.name)

    # Collect Misc bones
    all_armature_bones = {b.name for b in rig_armature.data.bones}
    unassigned_bones = all_armature_bones - distributed_bones
    
    global MISC
    MISC = list(set(MISC) | unassigned_bones)

    lists_data = {
        "Main": MAIN,
        "Twist": TWIST,
        "Fingers": fingers,
        "DE": DE,
        "Misc": MISC 
    }
    
    for list_name_str, bones_list in lists_data.items():
        bone_coll = arm_data.collections.get(list_name_str)
        if not bone_coll:
            bone_coll = arm_data.collections.new(name=list_name_str)
            
        for bone_name in bones_list:
            if bone_name in arm_data.bones:
                bone = arm_data.bones[bone_name]
                bone_coll.assign(bone)

    arm_data.collections.move(from_index=arm_data.collections.find("Main"), to_index=0)
    arm_data.collections.move(from_index=arm_data.collections.find("Face"), to_index=1)
    arm_data.collections.move(from_index=arm_data.collections.find("Twist"), to_index=2)    
    arm_data.collections.move(from_index=arm_data.collections.find("Fingers"), to_index=3)
    arm_data.collections_all["Main"].is_solo = True

def apply_bone_widgets(context, rig_armature):

    check_widgets()

    widgets_map = {
        "Hand IK R": ('THEME02', "cs_hand_r", 1.0),
        "Hand IK L": ('THEME03', "cs_hand_l", 1.0),
        "Foot IK R": ('THEME02', "cs_foot", 1.0),  
        "Foot IK L": ('THEME03', "cs_foot", 1.0), 
        "Hip": ('THEME11', "cs_sphere", 1.0),
        "pelvis": ('THEME12', "cs_circle", 1.0),
        "center_c_n": ('THEME01', "cs_circle_root", 4000.0),
        "pattern_c_n": ('THEME03', "cs_pattern", 4000.0),
        "head": ('THEME11', "cs_circle_head", 1.0),   
        "neck": ('THEME11', "cs_circle_head", 1.0),
        "spine1": ('THEME10', "cs_circle_spine_01", 1.0),   
        "spine2": ('THEME10', "cs_circle_spine_02", 1.0),
        "shoulder r": ('THEME05', "cs_shoulder", 1.0),   
        "shoulder l": ('THEME05', "cs_shoulder", 1.0),
        "Arm Pole R": ('THEME04', "cs_sphere_pole", 1.0),
        "Arm Pole L": ('THEME09', "cs_sphere_pole", 1.0),
        "Leg Pole R": ('THEME04', "cs_sphere_pole", 1.0),
        "Leg Pole L": ('THEME09', "cs_sphere_pole", 1.0),
        "toe r": ('THEME11', "cs_circle_toe", 1.0),
        "toe l": ('THEME11', "cs_circle_toe", 1.0),
        #OE
        "Root": ('THEME01', "cs_circle_root", 4000.0)
    }   
     
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = rig_armature.pose.bones
    
    widgets_collection = context.scene.collection.children.get("Widgets")
    
    for bone_name, settings in widgets_map.items():
        if bone_name in pose_bones:
            p_bone = pose_bones[bone_name]
            
            theme_name = settings[0]       
            widget_mesh_name = settings[1]
            scale_value = settings[2]
            
            p_bone.color.palette = theme_name
            
            if widgets_collection and widget_mesh_name in widgets_collection.objects:
                widget_obj = widgets_collection.objects[widget_mesh_name]
                p_bone.custom_shape = widget_obj
                p_bone.use_custom_shape_bone_size = True
                
                if isinstance(scale_value, (int, float)):
                    p_bone.custom_shape_scale_xyz = (scale_value, scale_value, scale_value)
                else:
                    p_bone.custom_shape_scale_xyz = scale_value

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
