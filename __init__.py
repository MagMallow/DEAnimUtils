bl_info = {
    "name": "DE Anim Utils",
    "author": "MagMallow",
    "version": (1,0),
    "blender": (4, 4, 3),
    "location": "3D View > Properties> DE Anim Utils",
    "description": "Automatic rig setup for DE armatures",   
    "category": "Animation",
    }

import bpy
import sys
import os
import importlib

from .modules import asset_stuff
from .modules import bake_stuff
from .modules import finalize_stuff
from .modules import pib_stuff
from .modules import prepare_stuff
from .modules import prettifier
from .modules import rig_stuff

PIB_COLL = 'Pib Dummy'
PIB_OBJ = 'Lil_Pib'

def refresh_blender_scene(context, armature):
    if not armature:
        return
        
    scene = context.scene
    current_frame = scene.frame_current

    if armature.animation_data and armature.animation_data.action:
        action = armature.animation_data.action
        action.id_data.update_tag()
        action.fcurves.update()   

    armature.update_tag(refresh={'OBJECT', 'DATA', 'TIME'})
    context.view_layer.update()

    scene.frame_set(current_frame + 1)
    scene.frame_set(current_frame)
    
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def get_scene_armatures(self, context):
    items = []
    for obj in context.scene.objects:
        if obj.type == 'ARMATURE':
            items.append((obj.name, obj.name, f"{obj.name}"))
            
    if not items:
        items.append(("NONE", "No armatures in scene", "At least one armature is required"))
    return items

# IK operators
class OBJECT_OT_ConvertToIK(bpy.types.Operator):
    bl_idname = "object.convert_to_ik"
    bl_label = "Convert to IK"
    bl_description = "Creates a simple IK rig for the selected armature"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'ARMATURE':
            self.report({'WARNING'}, "Select armature!")
            return {'CANCELLED'}
        
        if active_obj.name.endswith(" (RIG)"):
            self.report({'WARNING'}, "This armature already has an IK setup!")
            return {'CANCELLED'}
        
        
        rig_armature = rig_stuff.duplicate_armature(context, active_obj)

        rig_stuff.copy_bones_by_dict(rig_armature, rig_stuff.RIG_BONES)
        rig_stuff.add_rot_constraints(rig_armature, rig_stuff.RIG_BONES)
        rig_stuff.add_ik_constraints(rig_armature, rig_stuff.IK_LIMBS)  
        rig_stuff.apply_joints_offset(context, rig_armature, rig_stuff.IK_LIMBS)
        rig_stuff.setup_hip_bone(rig_armature, rig_stuff.HIP_BONES)    
        rig_stuff.transfer_bone_animation(rig_armature, rig_stuff.HIP_BONES)       
        rig_stuff.link_armatures_by_transforms(active_obj, rig_armature)
        
        prettifier.create_bone_collections_from_lists(rig_armature)
        prettifier.apply_bone_widgets(context, rig_armature)        
             
        bpy.ops.object.select_all(action='DESELECT')
        rig_armature.select_set(True)
        context.view_layer.objects.active = rig_armature
             
        active_obj.hide_viewport = True
             
        refresh_blender_scene(context, rig_armature)         
                             
        self.report({'INFO'}, f"IK armature created: {rig_armature.name}")
        return {'FINISHED'}

class OBJECT_OT_BakeIKBones(bpy.types.Operator):
    bl_idname = "object.bake_ik_bones"
    bl_label = "Bake IK bones"
    bl_description = "Bakes character animation to IK bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        rig_armature = context.active_object
        
        if not rig_armature or rig_armature.type != 'ARMATURE' or not rig_armature.name.endswith(" (RIG)"):
            self.report({'WARNING'}, "Select (RIG) armature!")
            return {'CANCELLED'}

        original_name = rig_armature.name.replace(" (RIG)", "")
        original_armature = context.scene.objects.get(original_name)

        if not original_armature:
            self.report({'ERROR'}, f"Original armature '{original_name}' not found!")
            return {'CANCELLED'}

        bake_stuff.setup_bake_constraints(context, rig_armature, original_armature, rig_stuff.RIG_BONES)
        
        bpy.ops.object.select_all(action='DESELECT')
        rig_armature.select_set(True)
        context.view_layer.objects.active = rig_armature        
        
        refresh_blender_scene(context, rig_armature)             
        
        self.report({'INFO'}, "IK bones baked!")
        return {'FINISHED'}

class OBJECT_OT_Complete(bpy.types.Operator):
    bl_idname = "object.complete"
    bl_label = "Finalize animation"
    bl_description = "Bakes and cleans animation for export"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):        

        rig_armature = context.active_object
        if not rig_armature or rig_armature.type != 'ARMATURE' or not rig_armature.name.endswith(" (RIG)"):
            self.report({'WARNING'}, "Select (RIG) armature!")
            return {'CANCELLED'}

        original_name = rig_armature.name.replace(" (RIG)", "")
        original_armature = context.scene.objects.get(original_name)

        original_armature.hide_viewport = False

        if not original_armature:
            self.report({'ERROR'}, f"Original armature '{original_name}' not found!")
            return {'CANCELLED'}

        finalize_stuff.finalize_bake(context, rig_armature, original_armature)  
        
        refresh_blender_scene(context, original_armature)
        
        self.report({'INFO'}, "Animation baked. RIG armature removed!")
        return {'FINISHED'}

class OBJECT_OT_Prepare(bpy.types.Operator):
    bl_idname = "object.prepare"
    bl_label = "[Optional] Prepare armature"
    bl_description = "Prepares armature for IK (cw and gmd for animation mostly)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        active_obj = context.active_object        

        if not active_obj or active_obj.type != 'ARMATURE':
            self.report({'WARNING'}, "Select armature!")
            return {'CANCELLED'}

        if active_obj.name.endswith(" (RIG)"):
            self.report({'WARNING'}, "This armature already has an IK setup!")
            return {'CANCELLED'}
        
        prepare_stuff.prepare_armature(active_obj)
        
        self.report({'INFO'}, "Armature is ready!")
        return {'FINISHED'}
    
# Pib Operators

class OBJECT_OT_GetPibTransform(bpy.types.Operator):
    bl_idname = "object.get_pib_transform"
    bl_label = "Get pib transform"
    bl_description = "Calculates matrix vectors and the location of a pib for use in AuthEdit."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):      

        pib_stuff.get_pib_transform(PIB_COLL, PIB_OBJ)
        
        self.report({'INFO'}, f"Pib dummy matrices are printed to the console (Window ‣ Toggle System Console)!")                             
        return {'FINISHED'}

class OBJECT_OT_SetPibShape(bpy.types.Operator):
    bl_idname = "object.set_pib_shape"
    bl_label = "Set pib shape"
    bl_description = "Set selected object as shape to pib dummy."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):  
    
        pib_stuff.set_pib_shape(context, self, PIB_COLL, PIB_OBJ)     
        return {'FINISHED'}

class OBJECT_OT_SetPibParentBone(bpy.types.Operator):
    bl_idname = "object.set_pib_parent_bone"
    bl_label = "Set pib parent bone"
    bl_description = "Set selected bone as pib dummy parent."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context): 

        pib_stuff.set_pib_parent_bone(context, self, PIB_COLL, PIB_OBJ)
        return {'FINISHED'}

class OBJECT_OT_CreatePibDummy(bpy.types.Operator):
    bl_idname = "object.create_pib_dummy"
    bl_label = "Create Pib Dummy"
    bl_description = "Creates Pib Dummy Empty."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):      

        pib_stuff.create_pib_dummy(PIB_COLL, PIB_OBJ)
        
        self.report({'INFO'}, f"Pib Dummy created!")                             
        return {'FINISHED'}

# Asset Operators
class OBJECT_OT_SetAssetToR(bpy.types.Operator):
    bl_idname = "object.set_asset_to_r"
    bl_label = "Equip to Right hand"
    bl_description = "Equip selected asset armature to right hand."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):        

        asset_armature = context.active_object
        if not asset_armature or asset_armature.type != 'ARMATURE':
            self.report({'WARNING'}, "Select asset armature!")
            return {'CANCELLED'}

        char_armature = context.scene.char_armature
        if char_armature == "NONE":
            self.report({'WARNING'}, "Character armature not selected!")
            return {'CANCELLED'}
        
        asset_stuff.equip_asset(self, asset_armature, char_armature, True)
                                    
        return {'FINISHED'}

class OBJECT_OT_SetAssetToL(bpy.types.Operator):
    bl_idname = "object.set_asset_to_l"
    bl_label = "Equip to Left hand"
    bl_description = "Equip selected asset armature to left hand."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):        

        asset_armature = context.active_object
        if not asset_armature or asset_armature.type != 'ARMATURE':
            self.report({'WARNING'}, "Select asset armature!")
            return {'CANCELLED'}

        char_armature = context.scene.char_armature
        if char_armature == "NONE":
            self.report({'WARNING'}, "Character armature not selected!")
            return {'CANCELLED'}
        
        asset_stuff.equip_asset(self, asset_armature, char_armature, False)
                                    
        return {'FINISHED'}

class OBJECT_OT_SetPatternPose(bpy.types.Operator):
    bl_idname = "object.set_pattern_pose"
    bl_label = "Set hand pattern pose"
    bl_description = "Pose hands according to the pattern_c_n."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):      
 
        char_armature = context.scene.char_armature
        if char_armature == "NONE":
            self.report({'WARNING'}, "Character armature not selected!")
            return {'CANCELLED'}
        
        asset_stuff.set_pattern_pose(context, char_armature)

        self.report({'INFO'}, f"Hand pattern pose has been successfully assigned!")
 
        return {'FINISHED'}

# INVERSE KINEMATICS
class VIEW3D_PT_DEAnimationUtils_A_IK(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DE Anim Utils'
    bl_label = "Inverse Kinematics"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row(align=True)
        row.operator("object.convert_to_ik", text="Convert to IK")
        row.operator("object.bake_ik_bones", text="Bake IK bones")
        
        col_comp = layout.column(align=True)
        col_comp.operator("object.complete", text="Finalize animation")
        
        col_comp.separator(factor=0.5)
        
        col_comp.label(text="Use for female armatures and GMDs for Animation")
        
        col_comp.separator(factor=0.5)
        
        col_comp.operator("object.prepare", text="[Optional] Prepare armature")
                
        layout.separator(factor=0.5)

        col_off = layout.column(align=True)
        col_off.prop(scene, "elbow_offset", text="Elbow offset")
        col_off.prop(scene, "knee_offset", text="Knee offset") 
   
# ASSET EQUIP
class VIEW3D_PT_DEAnimationUtils_B_ASSET(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DE Anim Utils'
    bl_label = "Asset Equip"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="Asset must be Unskinned GMD for Animation")   
          
        col = layout.column(align=True)   
        
        col.prop(scene, "char_armature", text="Character armature", icon='ARMATURE_DATA')
        
        col.separator(factor=0.5)        
        
        col.operator("object.set_asset_to_r", text="Equip to Right hand")

        col.separator(factor=0.5)        
        
        col.operator("object.set_asset_to_l", text="Equip to Left hand")
        
        col.separator(factor=0.5)        
        
        col.operator("object.set_pattern_pose", text="Set hand pattern pose")
        
# PIB TRANSFORM
class VIEW3D_PT_DEAnimationUtils_C_PIB(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DE Anim Utils'
    bl_label = "Pib Transform"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        col = layout.column(align=True)    

        collection = bpy.data.collections.get(PIB_COLL)
        if collection and PIB_OBJ in collection.objects:           
            col.operator("object.get_pib_transform", text="Get pib transform")
        
            col.separator(factor=0.5)
        
            col.operator("object.set_pib_parent_bone", text="Set pib parent bone")
                        
            col.separator(factor=0.5)
        
            col.operator("object.set_pib_shape", text="Set pib shape")        
        else:
            col.operator("object.create_pib_dummy", text="Create Pib Dummy")         

classes = (
    OBJECT_OT_ConvertToIK,
    OBJECT_OT_BakeIKBones,
    OBJECT_OT_Complete,
    OBJECT_OT_Prepare, 
    OBJECT_OT_SetAssetToR,
    OBJECT_OT_SetAssetToL,
    OBJECT_OT_SetPatternPose,  
    OBJECT_OT_CreatePibDummy,    
    OBJECT_OT_GetPibTransform,
    OBJECT_OT_SetPibShape,
    OBJECT_OT_SetPibParentBone,
    VIEW3D_PT_DEAnimationUtils_A_IK,
    VIEW3D_PT_DEAnimationUtils_B_ASSET,    
    VIEW3D_PT_DEAnimationUtils_C_PIB,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.elbow_offset = bpy.props.FloatProperty(
        name="Elbow offset",
        default=0.0,
        description="Set to fix IK solver ambiguity on straight limbs (for example -0.00007)"
    )
    bpy.types.Scene.knee_offset = bpy.props.FloatProperty(
        name="Knee offset",
        default=0.0,
        description="Set to fix IK solver ambiguity on straight limbs (for example -0.00007)"
    )
    bpy.types.Scene.char_armature = bpy.props.EnumProperty(
        items=get_scene_armatures,
        name="Char armature",
        description="List of all armatures in the current scene"
    )
    
    addon_dir = os.path.dirname(__file__)
    plib_dir = os.path.join(addon_dir, "pose_lib") 
    
    asset_libraries = bpy.context.preferences.filepaths.asset_libraries
    
    if "DE Hand Patterns" not in asset_libraries:
        new_lib = asset_libraries.new(name="DE Hand Patterns")
        new_lib.path = plib_dir 


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.elbow_offset
    del bpy.types.Scene.knee_offset
    del bpy.types.Scene.char_armature
    
    asset_libraries = bpy.context.preferences.filepaths.asset_libraries
    
    if "DE Hand Patterns" in asset_libraries:
        lib_to_remove = asset_libraries.get("DE Hand Patterns")
        if lib_to_remove:
            asset_libraries.remove(lib_to_remove)

if __name__ == "__main__":
    register()
