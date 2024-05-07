__author__ = 'Elysia'

import pymel.core as pm
from pymel.core import workspaceControl
from pymel.core import optionVar
from functools import partial, reduce

class Color:
    RED = [1, 0, 0]
    GREEN = [0.5, 1, 0.5]
    BLUE = [0.5, 0.7, 1]
    LIGHTGREY = [0.8, 0.8, 0.8]
    MIDGREY = [0.5, 0.5, 0.5]
    DARKGREY = [0.2] * 3

class MeshSelector :
    """
    get material in selecting mesh 
    
    """
    
    def __init__(self) :
        self.windowName = "Mesh Selector Tool";
        self.windowTitleName = "Selct Material";
        self.objects = list();              # save selected objects
        self.frames = list();               # save frameLayouts
        self.annotationObjects = list();    # show in text field
        
        if not optionVar.has_key('loadMode') :
            optionVar['loadMode'] = False;     # default: mesh select mode
        if not optionVar.has_key('selectMode') :
            optionVar['selectMode'] = 0;
        if not optionVar.has_key('autoLoadMode') :
            optionVar['autoLoadMode'] = True;
        if not optionVar.has_key('autoLoadMemory') :
            optionVar['autoLoadMemory'] = True;

        self.selectionSetName = 'SaveSelectionData' # save selection data in set even quit app
        self.CreateSelectionSet();
        
    def CreateSelectionSet(self):
        try :
            return pm.PyNode(self.selectionSetName);
        except pm.MayaNodeError :
            return pm.createNode('objectSet', name = self.selectionSetName);
    def CheckSelectionMesh(self):
        selectedObjects = pm.selected(type = 'transform');
        self.objects = [object for object in selectedObjects if object.getShape()]
        if(self.objects) :
            return True;
        else : 
            return False
    def CheckSelectionGroup(self):
        selectedGroups = pm.selected(type = 'transform');
        dependencies = [group.getChildren(ad = True, type = 'transform') for group in selectedGroups];
        dependencies = reduce(lambda x, y : x + y, dependencies);
        self.objects = [mesh for mesh in set(dependencies) if mesh.getShape()]
        if(self.objects) :
            return True;
        else :
            return False
    def SetButtonColor(self, button):
        button.setBackgroundColor(Color.BLUE if button.isHighLight else Color.DARKGREY);
    def ButtonSelectMeshFace(self, button, *args) :
        if optionVar['selectMode'] == 1:
            self.ButtonSelectMeshFaceAdditive(button);
        else :
            self.ButtonSelectMeshFaceExclusive(button);
    def ButtonSelectMeshFaceAdditive(self, button) :
        if not any([b.isHighLight for b in self.buttons]) :
            pm.select(clear = True);
        if button.isHighLight == True :
            pm.select(button.meshFaces, deselect = True);
            button.isHighLight = False;
        else :
            pm.select(button.meshFaces, add = True);
            button.isHighLight = True;
        self.SetButtonColor(button);
    def ButtonSelectMeshFaceExclusive(self, button) :
        if button.isHighLight == True :
            pm.select(button.meshFaces, deselect = True);
            button.isHighLight = False;
        else :
            pm.select(button.meshFaces, replace = True)
            for b in self.buttons :
                b.isHighLight = False;
            button.isHighLight = True;
        
        for b in self.buttons :
            self.SetButtonColor(b);
    def AddButton(self, object, frame) :
        mesh = object.getShape();
        shadingEngineNodes = list(set(mesh.inputs(type = 'shadingEngine')));
        for shadingEngineNode in shadingEngineNodes :
            shader = shadingEngineNode.surfaceShader.inputs()[0];
            meshFaces = shadingEngineNode.members()[0];
            button = pm.iconTextButton(
                style = 'textOnly',
                label = f'{shader.name()} ({len(meshFaces)})',
                parent = frame,
                enableBackground = True
            );
            button.meshFaces = meshFaces;
            button.isHighLight = False;
            self.SetButtonColor(button);
            self.buttons.append(button);
            button.setCommand(partial(self.ButtonSelectMeshFace, button));
    def InsertObejcts(self):
        self.mainScroll.clear();
        self.frames = [];
        self.buttons = [];
        self.annotationObjects = [];
        self.CreateSelectionSet().clear();

        for object in self.objects :
            self.textField.setText(object.name());   # show in text field
            self.annotationObjects.append(object.name());   # Mouse Hover Display

            with pm.frameLayout(
                    label = object.getShape().name(),
                    collapsable = True,
                    parent = self.mainScroll
            ) as frame:
                self.frames.append(frame);
                self.AddButton(object, frame);
            
            self.CreateSelectionSet().add(object);

        self.textField.setAnnotation('\n'.join(self.annotationObjects));
    def InsertSelection(self, *args) :
        selectFun = self.CheckSelectionGroup if optionVar['loadMode'] else self.CheckSelectionMesh;
        selectFun();
        self.InsertObejcts();
        
    def ClearCommand(self, *args):
        self.obejcts = [];
        self.mainScroll.clear();
        self.frames = [];
        self.textField.setText('Please select meshes in viewport');
        self.textField.setAnnotation('');
    def RefreshCommand(self, *args):
        pm.select(clear = True);
        self.InsertObejcts();
    def LoadCommand(self, value) :
        optionVar['loadMode'] = value;
        self.InsertSelection();
    def AutoLoadListCommand(self, value):
        optionVar['autoLoadMode'] = value;
    def AutoLoad(self):
        if optionVar['autoLoadMode'] == True :
            self.InsertSelection();
    def AutoLoadMemoryCommand(self, value):
        optionVar['autoLoadMemory'] = value;
    def SceneOpened(self, *args):
        if optionVar['autoLoadMemory'] == True :
            self.objects = self.CreateSelectionSet().members();
            self.InsertObejcts();
    
    def AddEditorSelection(self):
        with pm.menu(label = 'Window') as self.windowMenu :
            pm.menuItem(label = 'Refresh', image = 'refresh.png', command = self.RefreshCommand);
            pm.menuItem(label = 'Clear', image = 'clearAll.png', command = self.ClearCommand);
            pm.menuItem(label = 'Collapse All', image = 'arrowUp.png', command = lambda *args : [frame.setCollapse(True) for frame in self.frames]);
            pm.menuItem(label = 'Expand All', image = 'arrowDown.png', command = lambda *args : [frame.setCollapse(False) for frame in self.frames]);
            pm.menuItem(label = 'Close', image = 'closeTabButton.png', command = lambda *args : workspaceControl(self.windowTitleName, edit = True, close = True));

        # tearOff: make Editor independent
        with pm.menu(label = 'Editor', tearOff = True) as self.editorMenu :
            pm.menuItem(divider = True, dividerLabel = 'Selection Mode');   # divide Button list
            self.modeRadio = pm.radioMenuItemCollection();  # radio(only select one) Menu
            pm.menuItem(label = 'Exclusive(only select one)', radioButton = not bool(optionVar['selectMode']), command = lambda *args : optionVar.update({'selectMode' : 0}));
            pm.menuItem(label = 'Additive(can select one more)', radioButton = bool(optionVar['selectMode']), command = lambda *args : optionVar.update({'selectMode' : 1}));
            
            pm.menuItem(divider = True, dividerLabel = 'Load Mesh Mode');
            pm.menuItem(label = 'Dependencies Mode', checkBox = optionVar['loadMode'], command = self.LoadCommand, ann = 'Load child objects when a group node is selected');
            pm.menuItem(label = 'Auto Load Selected', checkBox = optionVar['autoLoadMode'], command = self.AutoLoadListCommand, ann = 'Auto load selected objects');
            pm.menuItem(label = 'Auto Load Memory', checkBox = optionVar['autoLoadMemory'], command = self.AutoLoadMemoryCommand, ann = 'Auto load last selected objects in current scene when opened');

        with pm.menu(label = 'Help') as self.helpMenu :
            pm.menuItem(label = 'Help', image = 'help.png', command = lambda *args : pm.showHelp('http://chenglixue.top/', absolute = True));
            
    def AddScrollLayout(self):
        with pm.scrollLayout(childResizable = True) as self.mainScroll : 
            pass;
    
    def AddLayout(self, *args):
        with pm.formLayout() as self.mainForm:
            with pm.menuBarLayout() as self.menuBar:
                self.AddEditorSelection();
                
            self.textField = pm.textFieldButtonGrp(
                label = 'Objects',
                placeholderText = 'Please select meshes in viewport',
                editable = False,
                buttonLabel = '<',
                buttonCommand = lambda *args : self.InsertSelection(),
                
                columnWidth3 = [50, 100, 5],
                adjustableColumn = 2,
            );

            self.AddScrollLayout();
            
        self.mainForm.attachForm(self.menuBar.name(), 'top', 0)
        self.mainForm.attachForm(self.menuBar.name(), 'left', 0)
        self.mainForm.attachForm(self.menuBar.name(), 'right', 0)
        self.mainForm.attachForm(self.textField.name(), 'left', 0)
        self.mainForm.attachForm(self.textField.name(), 'right', 0)
        self.mainForm.attachControl(self.textField.name(), 'top', 0, self.menuBar.name())
        self.mainForm.attachForm(self.mainScroll.name(), 'bottom', 0)
        self.mainForm.attachForm(self.mainScroll.name(), 'left', 0)
        self.mainForm.attachForm(self.mainScroll.name(), 'right', 0)
        self.mainForm.attachControl(self.mainScroll.name(), 'top', 0, self.textField.name())
        
        pm.scriptJob(event = ['SelectionChanged', self.AutoLoad], parent = self.mainForm, rp = True);
        pm.scriptJob(event = ['SceneOpened', self.SceneOpened], parent = self.mainScroll, rp = True);
        
    # add need feature in here
    def AddUI(self, *args) :
        self.AddLayout();
        
    # show window
    def ShowUI(self, *args):
        self.AddUI();