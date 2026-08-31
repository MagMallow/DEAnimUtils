# DEAnimUtils
Blender add-on for automatic Dragon Engine rig setup, and more.

Location: 3D View > Properties> DE Anim Utils
## Features
* Convert any (in theory) humanoid Dragon Engine armature to IK Rig and vice versa.
* Edit pre-existing animations using IK.
* Equip assets to character armature.
* Pose hand bones based on `pattern_c_n` parameters + Hand patterns pose library.
* Get PIB transform.
## IK Rig
1. Select the armature (preferably Skinned GMD for Modelling).
2. [Optional] Use __Prepare Armature__ for female armature, Skinned GMD for Animation or if something goes wrong.
3. [Optional] Import an animation.
4. Click __Convert to Ik__.
5. Edit the animation.
6. Click __Finalize animation__.
## Assets
1. Select armature from __Character armature__ list.
2. Select asset armature (supports only Unskinned GMD for Animation).
3. Click __Equip to Right hand__ / __Equip to Left hand__.

Use __Set Pattern pose__ to automatically set the hand pose according to the character's `pattern_c_n`. _Note: it doesn't insert any keyframes_

Also Pose Library is available for manual applying
<img width="1617" height="652" alt="image" src="https://github.com/user-attachments/assets/ab2cc969-31a1-4524-8200-e6625fd7b07c" />

## PIB
1. Click __Create Pib Dummy__.
2. [Optional] Click __Set pib parent bone__. 
3. [Optional] Select any mesh object and click __Set pib shape__. _Note: This is for visualization purposes only._
4. Move Pib Dummy and click __Get pib transform__. Check the System Console for output.
<img width="873" height="305" alt="image" src="https://github.com/user-attachments/assets/2bbdb74f-8b98-421e-9e1e-64476f990e96" />
