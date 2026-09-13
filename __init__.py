bl_info = {
    "name": "DE Anim Utils",
    "author": "MagMallow",
    "version": (1,1),
    "blender": (4, 4, 3),
    "location": "3D View > Properties> DE Anim Utils",
    "description": "Automatic rig setup for DE armatures",   
    "doc_url": "https://github.com/MagMallow/DEAnimUtils",    
    "category": "Animation",
    }

import bpy
import sys
import os
from enum import Enum

from .modules import asset_stuff
from .modules import bake_stuff
from .modules import finalize_stuff
from .modules import pib_stuff
from .modules import prepare_stuff
from .modules import prettifier
from .modules import rig_stuff

PIB_COLL = 'Pib Dummy'
PIB_OBJ = 'Lil_Pib'
IS_DE = True

class ArmatureEngine(Enum):
    DE = "DRAGON ENGINE"  
    OE = "OLD ENGINE"
    OOE = "OLD OLD ENGINE"    

class InvalidArmatureError(Exception):
    pass

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
    
def check_engine(armature):
    hip_bones = {"kosi_c_n", "ketu_c_n"}
    ooe_hip_bones = {"ketu_n", "kosi_n"}

    bones = armature.data.bones
    bone_keys = set(armature.data.bones.keys())
    
    if not hip_bones.issubset(bone_keys):
        if ooe_hip_bones.issubset(bone_keys):
            print("Armature is OOE!")
            armature.data["derig_eng"] = 3
            return []
        raise InvalidArmatureError("Bones 'kosi_c_n' or 'ketu_c_n' not found!")
    
    if bones["kosi_c_n"].parent == bones["ketu_c_n"]:
        print("Armature is DE!")
        armature.data["derig_eng"] = 1
        return []
  
    print("Armature is OE")    
    armature.data["derig_eng"] = 2
    return []    

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

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        
        if not obj or obj.type != 'ARMATURE':
            cls.poll_message_set("Select armature!")
            return False
            
        if obj.data.get("derig_status", 0) != 1:
            cls.poll_message_set("Prepare armature first!")
            return False
            
        return True

    def execute(self, context):
        
        active_obj = context.active_object
        
        rig_stuff.add_keys_if_empty(active_obj, rig_stuff.BONES_TO_INSERT)

        # DE
        if active_obj.data.get("derig_eng", 0) == 1:
            rig_armature = rig_stuff.duplicate_armature(context, active_obj)
            rig_stuff.copy_bones_by_dict(rig_armature, rig_stuff.RIG_BONES)
            bake_stuff.setup_bake_constraints(context, rig_armature, active_obj,
            rig_stuff.IK_LIMBS)
            rig_stuff.add_rot_constraints(rig_armature, rig_stuff.RIG_BONES)
            rig_stuff.add_ik_constraints(rig_armature, rig_stuff.IK_LIMBS)  
            rig_stuff.apply_joints_offset(context, rig_armature, rig_stuff.IK_LIMBS)
            rig_stuff.setup_hip_bone(rig_armature, rig_stuff.HIP_BONES)    
            rig_stuff.transfer_bone_animation(rig_armature, rig_stuff.HIP_BONES)
            bake_stuff.bake_offset_empties(active_obj, rig_armature, rig_stuff.ArmOff_BONES)
            bake_stuff.bake_offset_constraints(active_obj, rig_armature, rig_stuff.ArmOff_BONES) 
            rig_stuff.link_armatures_by_transforms(active_obj, rig_armature)

        # OE
        if active_obj.data.get("derig_eng", 0) == 2:
            rig_armature = rig_stuff.duplicate_armature(context, active_obj)
            rig_stuff.copy_bones_by_dict(rig_armature, rig_stuff.RIG_BONES_OE)
            rig_stuff.apply_joints_offset(context, rig_armature, rig_stuff.IK_LIMBS)             
            bake_stuff.setup_bake_constraints(context, rig_armature, active_obj,
            rig_stuff.IK_LIMBS)
            rig_stuff.add_rot_constraints(rig_armature, rig_stuff.RIG_BONES_OE)
            rig_stuff.add_ik_constraints(rig_armature, rig_stuff.IK_LIMBS)   
            bake_stuff.bake_offset_empties(active_obj, rig_armature, rig_stuff.ArmOff_BONES)
            bake_stuff.bake_offset_constraints(active_obj, rig_armature, rig_stuff.ArmOff_BONES)  
            rig_stuff.link_armatures_by_transforms(active_obj, rig_armature)
            
        # OOE
        if active_obj.data.get("derig_eng", 0) == 3:
            rig_armature = rig_stuff.duplicate_armature(context, active_obj)
            rig_stuff.copy_bones_by_dict(rig_armature, rig_stuff.RIG_BONES_OOE)
            bake_stuff.setup_bake_constraints(context, rig_armature, active_obj,
            rig_stuff.IK_LIMBS)        
            rig_stuff.add_rot_constraints(rig_armature, rig_stuff.RIG_BONES_OOE)
            rig_stuff.add_ik_constraints(rig_armature, rig_stuff.IK_LIMBS)  
            rig_stuff.apply_joints_offset(context, rig_armature, rig_stuff.IK_LIMBS)
            bake_stuff.bake_offset_empties(active_obj, rig_armature, rig_stuff.ArmOff_BONES)
            bake_stuff.bake_offset_constraints(active_obj, rig_armature, rig_stuff.ArmOff_BONES) 
            rig_stuff.link_armatures_by_transforms(active_obj, rig_armature)

        rig_stuff.rename_bones(rig_armature)
        prettifier.create_bone_collections_from_lists(rig_armature)
        prettifier.apply_bone_widgets(context, rig_armature)  

        bpy.ops.object.select_all(action='DESELECT')
        rig_armature.select_set(True)
        context.view_layer.objects.active = rig_armature
             
        active_obj.hide_viewport = True
             
        refresh_blender_scene(context, rig_armature)         
                             
        self.report({'INFO'}, f"IK armature created: {rig_armature.name}")
        return {'FINISHED'}

class OBJECT_OT_Complete(bpy.types.Operator):
    bl_idname = "object.complete"
    bl_label = "Finalize Animation"
    bl_description = "Bakes and cleans animation for export"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if not obj or not obj.data or obj.type != 'ARMATURE':
            cls.poll_message_set("Select RIG armature first!")
            return False

        if obj.data.get("derig_status", 0) != 2:
            cls.poll_message_set("Convert armature to IK first!")
            return False
            
        return True

    def execute(self, context):        
        rig_armature = context.active_object

        original_name = rig_armature.name.replace(" (RIG)", "")
        original_armature = context.scene.objects.get(original_name)

        original_armature.hide_viewport = False

        clean_twist_bool = False
        clean_face_bool = False    
        clean_phy_bool = False          
        if context.scene.clean_twist_checkbox:
            clean_twist_bool = True
        if context.scene.clean_face_checkbox:
            clean_face_bool = True
        if context.scene.clean_phy_checkbox:
            clean_phy_bool = True
            
        if not original_armature:
            self.report({'ERROR'}, f"Original armature '{original_name}' not found!")
            return {'CANCELLED'}

        finalize_stuff.finalize_bake(context, rig_armature, original_armature, 
        clean_twist_bool, clean_face_bool, clean_phy_bool)  
        
        refresh_blender_scene(context, original_armature)
        
        self.report({'INFO'}, "Animation baked. RIG armature removed!")
        return {'FINISHED'}

class OBJECT_OT_Prepare(bpy.types.Operator):
    bl_idname = "object.prepare"
    bl_label = "Prepare Armature"
    bl_description = "Prepares armature for IK"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        
        alert_row = layout.column()
        alert_row.alert = True
        alert_row.label(text="Armature has animation!", icon='ERROR')
        
        layout.label(text="Do not import animation before this operation.")        
        layout.label(text="Results may be unexpected. Continue?")

    def invoke(self, context, event):
        obj = context.active_object
        
        if obj and obj.animation_data and obj.animation_data.action:
            return context.window_manager.invoke_props_dialog(self, width=350)
            
        return self.execute(context)

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if not obj or obj.type != 'ARMATURE':
            cls.poll_message_set("Select armature!")
            return False

        if obj.data.get("derig_status", 0) != 0:
            cls.poll_message_set("Convert armature to IK first!")
            return False
            
        return True

    def execute(self, context):
        active_obj = context.active_object 
        
        try:
            engine = check_engine(active_obj)
        except InvalidArmatureError as error:
            self.report({'ERROR'}, f"Invalid armature: {error}")
            return {'CANCELLED'}
            
        prepare_stuff.prepare_armature(active_obj)
        
        self.report({'INFO'}, "Armature is ready!")
        return {'FINISHED'}

class OBJECT_OT_MirrorAnim(bpy.types.Operator):
    bl_idname = "object.mirror_anim"
    bl_label = "Mirror Animation"
    bl_description = "Mirrors selected animation by X"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if not obj or obj.type != 'ARMATURE':
            cls.poll_message_set("Select RIG armature first!")
            return False

        if obj.data.get("derig_status", 0) != 2:
            cls.poll_message_set("Convert armature to IK first!")
            return False
        
        return True

    def execute(self, context):
        active_obj = context.active_object        

        rig_stuff.mirror_anim(active_obj)
        
        self.report({'INFO'}, "Animation is mirrored!")
        return {'FINISHED'}

class OBJECT_OT_SeparateKetu(bpy.types.Operator):
    bl_idname = "object.separate_ketu"
    bl_label = "[DE] Separate Ketu channels"
    bl_description = "Separates ketu_c_n channels between ketu and center. Used for specific tasks like retargeting"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'ARMATURE':
            self.report({'WARNING'}, "Select armature first!")
            return {'CANCELLED'}
            
        if not active_obj.animation_data or not active_obj.animation_data.action:
            self.report({'WARNING'}, "Action not found!")
            return {'CANCELLED'}       

        rig_stuff.separate_ketu(active_obj)
        
        self.report({'INFO'}, "Channels are separated!")
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

# Inverse kinematics
class VIEW3D_PT_DEAnimationUtils_A_IK(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DE Anim Utils'
    bl_label = "Inverse Kinematics"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        col_comp = layout.column(align=True)       

        col_comp.operator("object.prepare", text="Prepare Armature")      
        
        col_comp.separator(factor=0.5)
        
        col_comp.operator("object.convert_to_ik", text="Convert to IK")
        
        col_comp.separator(factor=0.5)

        col_comp.operator("object.complete", text="Finalize Animation") 

        col_comp.separator(factor=0.5)
        
        col_comp.prop(scene, "clean_twist_checkbox", text="Clean _sup channels")
        
        col_comp.separator(factor=0.5)
        
        col_comp.prop(scene, "clean_face_checkbox", text="Clean face channels")   
        
        col_comp.separator(factor=0.5)
        
        col_comp.prop(scene, "clean_phy_checkbox", text="Clean _phy channels")           
        
        col_off = layout.column(align=True)
        col_off.prop(scene, "elbow_offset", text="Elbow offset")
        col_off.prop(scene, "knee_offset", text="Knee offset") 
        
        col_oth = layout.column(align=True)  
        
        col_oth.label(text="Other:")   
        
        col_oth.operator("object.mirror_anim", text="Mirror Animation")  
        
        col_oth.separator(factor=0.5)   
        
        col_oth.operator("object.separate_ketu", text="[DE] Separate Ketu channels")   
   
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
            
            col.label(text="center_c_n: All transforms")     
            
            col.separator(factor=0.5)
            
            col.label(text="Other bones: Rotation only (probably)")    

            col.separator(factor=0.5)            
        
            col.operator("object.get_pib_transform", text="Get pib transform")
            
            col.separator(factor=0.5)
            
            col.operator("object.set_pib_parent_bone", text="Set pib parent bone")
                        
            col.separator(factor=0.5)
        
            col.operator("object.set_pib_shape", text="Set pib shape")        
        else:
            col.operator("object.create_pib_dummy", text="Create Pib Dummy")         

classes = (
    OBJECT_OT_ConvertToIK,
    OBJECT_OT_Complete,
    OBJECT_OT_Prepare, 
    OBJECT_OT_SetAssetToR,
    OBJECT_OT_SetAssetToL,
    OBJECT_OT_SetPatternPose,  
    OBJECT_OT_CreatePibDummy,    
    OBJECT_OT_GetPibTransform,
    OBJECT_OT_SetPibShape,
    OBJECT_OT_SetPibParentBone,
    OBJECT_OT_MirrorAnim,
    OBJECT_OT_SeparateKetu,
    VIEW3D_PT_DEAnimationUtils_A_IK,
    VIEW3D_PT_DEAnimationUtils_B_ASSET,    
    VIEW3D_PT_DEAnimationUtils_C_PIB,
)

def register():
    bpy.types.Scene.clean_twist_checkbox = bpy.props.BoolProperty(
        name="Clean _sup channels",
        description="Cleans _sup animation channels after Finalize operation",
        default=True
    )   
    bpy.types.Scene.clean_face_checkbox = bpy.props.BoolProperty(
        name="Clean face channels",
        description="Cleans face animation channels after Finalize operation",
        default=True
    )
    bpy.types.Scene.clean_phy_checkbox = bpy.props.BoolProperty(
        name="Clean _phy channels",
        description="Cleans _phy animation channels after Finalize operation",
        default=True
    )
    for cls in classes:
        bpy.utils.register_class(cls)
    # Armature status: 0 - None, 1 - Prepared, 2 - Rig
    bpy.types.Armature.derig_status = bpy.props.IntProperty(
        name = "DEAnimUtils Prep",
        default = 0,
        options={'HIDDEN'}
    )
    # Engine: 0 - None, 1 - DE, 2 - OE, 3 - OOE
    bpy.types.Armature.derig_eng = bpy.props.IntProperty(
        name = "DEAnimUtils Eng",
        default = 0,
        options={'HIDDEN'}
    )        
    bpy.types.Scene.elbow_offset = bpy.props.FloatProperty(
        name = "Elbow offset",
        default = -0.0003,
        description="Set to fix IK solver ambiguity on straight limbs"
    )
    bpy.types.Scene.knee_offset = bpy.props.FloatProperty(
        name = "Knee offset",
        default = 0.0003,
        description = "Set to fix IK solver ambiguity on straight limbs"
    )
    bpy.types.Scene.char_armature = bpy.props.EnumProperty(
        items = get_scene_armatures,
        name = "Char armature",
        description = "List of all armatures in the current scene"
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
        
    del bpy.types.Scene.clean_twist_checkbox    
    del bpy.types.Scene.clean_face_checkbox    
    del bpy.types.Scene.clean_phy_checkbox     
    del bpy.types.Scene.elbow_offset
    del bpy.types.Scene.knee_offset
    del bpy.types.Scene.char_armature
    del bpy.types.Armature.derig_status
    del bpy.types.Armature.derig_eng 
    
    asset_libraries = bpy.context.preferences.filepaths.asset_libraries
    
    if "DE Hand Patterns" in asset_libraries:
        lib_to_remove = asset_libraries.get("DE Hand Patterns")
        if lib_to_remove:
            asset_libraries.remove(lib_to_remove)

if __name__ == "__main__":
    register()
