import math
import os
import bpy


def get_or_create_handles_collection():

    coll_name = "Buki Handles"
    if coll_name in bpy.data.collections:
        return bpy.data.collections[coll_name]
    new_coll = bpy.data.collections.new(coll_name)
    bpy.context.scene.collection.children.link(new_coll)
    return new_coll


def equip_asset(operator_instance, asset_armature, char_armature, is_right=True):

    asset_obj = (
        bpy.data.objects.get(asset_armature)
        if isinstance(asset_armature, str)
        else asset_armature
    )
    char_obj = (
        bpy.data.objects.get(char_armature)
        if isinstance(char_armature, str)
        else char_armature
    )

    if not asset_obj or not char_obj:
        operator_instance.report(
            {"ERROR"}, "One or both armatures not found!"
        )
        return False

    if asset_obj.type != "ARMATURE":
        operator_instance.report(
            {"ERROR"}, "Selected object must be ARMATURE!"
        )
        return False

    asset_name_str = asset_obj.name
    char_name_str = char_obj.name

    if is_right:
        bone_hpos = "rhpos"
        bone_target = "buki1_r_n"
        empty_name = f"buki_r_handle_{char_name_str}_{asset_name_str}"
        side_label = "RIGHT"
    else:
        bone_hpos = "lhpos"
        bone_target = "buki1_l_n"
        empty_name = f"buki_l_handle_{char_name_str}_{asset_name_str}"
        side_label = "LEFT"

    asset_bones = asset_obj.data.bones
    if bone_hpos not in asset_bones or "anm_root" not in asset_bones:
        operator_instance.report(
            {"ERROR"},
            f"Object {asset_name_str} doesn't have {bone_hpos} or anm_root!",
        )
        return False

    original_mode = asset_obj.mode
    bpy.context.view_layer.objects.active = asset_obj
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = asset_obj.data.edit_bones
    eb_hpos = edit_bones.get(bone_hpos)
    eb_anm_root = edit_bones.get("anm_root")

    eb_hpos.parent = None
    eb_anm_root.parent = eb_hpos

    bpy.ops.object.mode_set(mode=original_mode)

    need_empty = True
    pose_bones_char = char_obj.pose.bones

    if "buki1_r_n" in pose_bones_char:
        bpy.context.view_layer.update()
        p_bone = pose_bones_char["buki1_r_n"]

        if abs(p_bone.head.y - p_bone.tail.y) > 0.0001:
            need_empty = False

    bpy.context.view_layer.objects.active = asset_obj
    pose_bone_hpos = asset_obj.pose.bones[bone_hpos]

    for c in list(pose_bone_hpos.constraints):
        pose_bone_hpos.constraints.remove(c)

    # For modelling
    if not need_empty:
        const_hpos = pose_bone_hpos.constraints.new(type="COPY_TRANSFORMS")
        const_hpos.target = char_obj
        const_hpos.subtarget = bone_target
        const_hpos.mix_mode = "REPLACE"
        const_hpos.target_space = "WORLD"
        const_hpos.owner_space = "WORLD"
        const_hpos.influence = 1.0

    # For animation
    else:
        old_empty = bpy.data.objects.get(empty_name)
        if old_empty:
            bpy.data.objects.remove(old_empty, do_unlink=True)

        bpy.ops.object.select_all(action="DESELECT")

        empty = bpy.data.objects.new(empty_name, None)

        handles_collection = get_or_create_handles_collection()
        handles_collection.objects.link(empty)

        empty.location = (0.0, 0.0, 0.0)
        empty.delta_rotation_euler = (math.radians(-90), 0.0, 0.0)

        bpy.context.view_layer.objects.active = asset_obj

        const_hpos = pose_bone_hpos.constraints.new(type="COPY_TRANSFORMS")
        const_hpos.target = empty
        const_hpos.mix_mode = "REPLACE"

        const_empty = empty.constraints.new(type="COPY_TRANSFORMS")
        const_empty.target = char_obj
        const_empty.subtarget = bone_target
        const_empty.mix_mode = "BEFORE_FULL"
        const_empty.target_space = "WORLD"
        const_empty.owner_space = "WORLD"
        const_empty.influence = 1.0

    return True

def apply_pose_action_to_selected_bones(chosen_armature, pose_action, bone_suffix):

    pose_bones = chosen_armature.pose.bones

    for curve in pose_action.fcurves:
        if curve.data_path.startswith('pose.bones["'):
            parts = curve.data_path.split('"')
            if len(parts) > 1:
                bone_name = parts[1]
                
                if bone_name.endswith(bone_suffix) and bone_name in pose_bones:
                    p_bone = pose_bones[bone_name]
                    
                    value = curve.evaluate(0.0)
                    
                    prop_path = curve.data_path.split('].')[-1]
                    
                    if curve.array_index is not None and hasattr(p_bone, prop_path):
                        prop = getattr(p_bone, prop_path)
                        try:
                            prop[curve.array_index] = value
                        except:
                            pass
                    else:
                        try:
                            setattr(p_bone, prop_path, value)
                        except:
                            pass

def set_pattern_pose(context, chosen_armature_name):

    if not chosen_armature_name or chosen_armature_name == "NONE":
        return False
        
    chosen_armature = bpy.data.objects.get(chosen_armature_name)
    if not chosen_armature or chosen_armature.type != 'ARMATURE':
        return False

    target_bone_name = "pattern_c_n"
    pose_bones = chosen_armature.pose.bones

    if target_bone_name not in pose_bones:
        return False
        
    p_bone = pose_bones[target_bone_name]

    prefixes_and_suffixes = []

    # Left hand pattern
    if hasattr(p_bone, "pat1_left_hand"):
        val_L = int(round(getattr(p_bone, "pat1_left_hand")))
        if val_L != -1:
            prefixes_and_suffixes.append((f"{val_L:02d}_", "_l_n"))

    # Right hand pattern
    if hasattr(p_bone, "pat1_right_hand"):
        val_R = int(round(getattr(p_bone, "pat1_right_hand")))
        if val_R != -1:
            prefixes_and_suffixes.append((f"{val_R:02d}_", "_r_n"))

    if not prefixes_and_suffixes:
        return True

    lib_path = bpy.context.preferences.filepaths.asset_libraries["DE Hand Patterns"].path
    path_to_blend = os.path.join(lib_path, "hand_patterns.blend")

    for prefix, bone_suffix in prefixes_and_suffixes:
        with bpy.data.libraries.load(path_to_blend, link=False) as (data_from, data_to):
            target_name = next((act for act in data_from.actions if act.startswith(prefix)), None)
            if target_name:
                data_to.actions = [target_name]

        found_action = bpy.data.actions.get(target_name)
        if found_action:
            apply_pose_action_to_selected_bones(chosen_armature, found_action, bone_suffix)

    return True

