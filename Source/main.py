from TA.MayaMaterialTool.MayaMaterial import *
import TA.MayaMaterialTool.MayaMaterial as MayaMaterial
from importlib import reload
reload(MayaMaterial);

meshSelector = MayaMaterial.MeshSelector();

if workspaceControl(meshSelector.windowTitleName, exists = True) :
    workspaceControl(meshSelector.windowTitleName, edit = True, close = True);
    
workspaceControl(meshSelector.windowTitleName, retain = False, floating = True, uiScript = 'meshSelector.ShowUI()');