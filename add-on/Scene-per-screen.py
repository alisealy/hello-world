bl_info = {
    "name": "Scene-per-screen",
    "category": "Interface",
    "blender": (2, 80, 0)
}

import bpy


#class to define custom pop-up menu for switching worspaces
class WORKSPACE_OT_select(bpy.types.Operator):
    bl_idname = "workspace.select"
    bl_label = "Select Workspace"
    bl_description = "Select workspace"
    bl_property = "workspace"

    enum_items = None

    def get_items(self, context):
        if WORKSPACE_OT_select.enum_items is None:
            enum_items = []

            for w in bpy.data.workspaces:
                identifier, name, description = \
                    w.name, w.name, w.name
                if context.workspace.name == identifier:
                    name += "|Active"
                enum_items.append((
                    identifier,
                    name,
                    description))

            WORKSPACE_OT_select.enum_items = enum_items

        return WORKSPACE_OT_select.enum_items

    workspace = bpy.props.EnumProperty(items=get_items)

    def execute(self, context):
        if not self.workspace or self.workspace not in bpy.data.workspaces:
            return {'CANCELLED'}

        context.window.workspace = bpy.data.workspaces[self.workspace]
        return {'FINISHED'}

    def invoke(self, context, event):
        WORKSPACE_OT_select.enum_items = None
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


# Override topbar drawing    
def my_draw_left(self, context):
    layout = self.layout

    window = context.window
    screen = context.screen

    bpy.types.TOPBAR_MT_editor_menus.draw_collapsible(context, layout)

    layout.separator()

    if not screen.show_fullscreen:
        pass
    else:
        layout.operator(
            "screen.back_to_previous",
            icon='SCREEN_BACK',
            text="Back to Previous",
        )


# Custom property to store scene-per-screen
class PerScreenVariables(bpy.types.PropertyGroup):
    scene: bpy.props.StringProperty(
        name="scenePerScreen",
        description="the scene for each screen (for backwards compatability with 2.79)",
        default="Scene"
    )


# Modal operator for changing scenes
class ModalWorkspaceScene(bpy.types.Operator):
    bl_idname = "wm.modal_workspace_scene"
    bl_label = "Each Workspace Remembers A Scene"
    
    def __init__(self):
        print("Start")
        
    def __del__(self):
        print("End")
    
    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            if not (self.lastWorkspace == context.workspace):
                self.keepingTrack[self.lastWorkspace] = context.scene
                if context.workspace in self.keepingTrack.keys():
                    context.window.scene = self.keepingTrack[context.workspace]
                else:
                    self.keepingTrack[context.workspace] = context.scene
                self.lastWorkspace = context.workspace
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        self.keepingTrack = {context.workspace:context.scene}
        self.lastWorkspace = context.workspace
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


addon_keymaps = []


def register():
    # first register the custom menu, and the associated hotkey
    bpy.utils.register_class(WORKSPACE_OT_select)
    
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(
        name='Screen Editing')
    kmi = km.keymap_items.new(
        WORKSPACE_OT_select.bl_idname, 'SPACE', 'PRESS', 
        ctrl=True, shift=True)
    addon_keymaps.append((km, kmi))
    
    # Now we override the top-bar
    bpy.types.TOPBAR_HT_upper_bar.default_draw_left = \
        bpy.types.TOPBAR_HT_upper_bar.draw_left
    bpy.types.TOPBAR_HT_upper_bar.draw_left = my_draw_left
    
    # add custom property to store scene names
    bpy.utils.register_class(PerScreenVariables)
    bpy.types.Screen.per_screen_vars = bpy.props.PointerProperty(type=PerScreenVariables)
    
    # Now register the modal operator
    bpy.utils.register_class(ModalWorkspaceScene)
    
    #run the modal operator
    bpy.ops.wm.modal_workspace_scene('INVOKE_DEFAULT')


def unregister():
    # First un-register the modal operator
    bpy.utils.unregister_class(ModalWorkspaceScene)
    
    # now remove the class defining the custom property and how to access it (data is still stored in .blend file though)
    del bpy.types.Screen.per_screen_vars
    bpy.utils.unregister_class(PerScreenVariables)
    
    # next restore the topbar
    bpy.types.TOPBAR_HT_upper_bar.draw_left = \
        bpy.types.TOPBAR_HT_upper_bar.default_draw_left
    
    # now reset the keymap & unregister the custom menu
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)        
    addon_keymaps.clear()
    
    bpy.utils.unregister_class(WORKSPACE_OT_select)


if __name__ == "__main__":
    register()

