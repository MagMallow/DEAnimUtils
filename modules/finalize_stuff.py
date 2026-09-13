import bpy


CLEAN_MAP = [
'asi1_r_n', 'asi2_r_n', 'asi3_r_n', 'asi1_l_n',
'asi2_l_n', 'asi3_l_n', 'kosi_c_n', 'mune_c_n',
'kubi_c_n', 'face_c_n', 'kata_r_n', 'ude1_r_n',
'ude2_r_n', 'ude3_r_n', 'kata_l_n', 'ude1_l_n',
'ude2_l_n', 'ude3_l_n'
]


def finalize_bake(context, rig_armature, original_armature, 
    clean_twist_bool = False, clean_face_bool = False, clean_phy_bool = False):

    scene = context.scene
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    current_frame_orig = scene.frame_current

    search_keywords = ['left_hand', 'right_hand', 'face']
    saved_fcurves_data = []

    # Copy pattern channels data
    if rig_armature.animation_data and rig_armature.animation_data.action:
        rig_action = rig_armature.animation_data.action
        for curve in rig_action.fcurves:
            path_lower = curve.data_path.lower()
            if any(keyword in path_lower for keyword in search_keywords):
                curve_data = {
                    'data_path': curve.data_path,
                    'array_index': curve.array_index,
                    'group_name': curve.group.name if curve.group else "GMD Pattern Properties",
                    'keyframes': []
                }
                for kp in curve.keyframe_points:
                    curve_data['keyframes'].append({
                        'co': (kp.co[0], kp.co[1]),
                        'interpolation': kp.interpolation,
                        'handle_left': (kp.handle_left[0], kp.handle_left[1]),
                        'handle_right': (kp.handle_right[0], kp.handle_right[1])
                    })
                saved_fcurves_data.append(curve_data)

    # Bake
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    context.view_layer.objects.active = original_armature
    original_armature.select_set(True)
    rig_armature.select_set(False)
    
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    
    area_3d = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
    if area_3d:
        with context.temp_override(area=area_3d):
            bpy.ops.nla.bake(
                frame_start=frame_start, 
                frame_end=frame_end, 
                step=1, 
                only_selected=True,     
                visual_keying=True,     
                clear_constraints=True, 
                bake_types={'POSE'},
                channel_types={'LOCATION', 'ROTATION'} 
            )
    else:
        bpy.ops.nla.bake(frame_start=frame_start, frame_end=frame_end, step=1, only_selected=True, visual_keying=True, clear_constraints=True, bake_types={'POSE'}, channel_types={'LOCATION', 'ROTATION'})

    final_action = original_armature.animation_data.action
    final_action.name = f"{original_armature.name}_FinalBake"
    final_action.use_fake_user = True

    # Paste copied pattern channels
    if saved_fcurves_data:
        for curve_data in saved_fcurves_data:
            old_curve = final_action.fcurves.find(curve_data['data_path'], index=curve_data['array_index'])
            if old_curve:
                final_action.fcurves.remove(old_curve)
            
            new_curve = final_action.fcurves.new(
                data_path=curve_data['data_path'], 
                index=curve_data['array_index'], 
                action_group=curve_data['group_name']
            )
            for kp_data in curve_data['keyframes']:
                new_kp = new_curve.keyframe_points.insert(frame=kp_data['co'][0], value=kp_data['co'][1])
                new_kp.interpolation = kp_data['interpolation']
                new_kp.handle_left = kp_data['handle_left']
                new_kp.handle_right = kp_data['handle_right']

    if clean_twist_bool:
        _clean_animation_channels(final_action, '_sup')
    if clean_face_bool:
        _clean_animation_channels(final_action, '', '_')
    if clean_phy_bool:
        _clean_animation_channels(final_action, '_phy')
        
    final_action.fcurves.update()

    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    original_armature.select_set(False)
    rig_armature.select_set(True)
    bpy.data.objects.remove(rig_armature, do_unlink=True)

    original_armature.select_set(True)
    context.view_layer.objects.active = original_armature
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
    scene.frame_set(current_frame_orig)

def _clean_animation_channels(final_action, suffix="", prefix=""):

    clean_bones_list = CLEAN_MAP

    curves_to_remove = []
    
    for curve in final_action.fcurves:
        if curve.data_path.startswith('pose.bones["'):
            parts = curve.data_path.split('"')
            if len(parts) > 1:
                bone_name = parts[1]
                     
                is_target_bone = False
                if suffix and bone_name.endswith(suffix):
                    is_target_bone = True
                if prefix and bone_name.startswith(prefix):
                    is_target_bone = True
                    
                if is_target_bone:
                    curves_to_remove.append(curve)
                elif bone_name in clean_bones_list and "location" in curve.data_path:
                    curves_to_remove.append(curve)
                    
    for curve in curves_to_remove:
        final_action.fcurves.remove(curve)
