from kraken.core.maths import Vec3
from kraken.core.maths.xfo import Xfo
from kraken.core.maths.xfo import xfoFromDirAndUpV

from kraken.core.objects.components.component import Component


from kraken.core.objects.attributes.attribute_group import AttributeGroup
from kraken.core.objects.attributes.bool_attribute import BoolAttribute
from kraken.core.objects.attributes.float_attribute import FloatAttribute

from kraken.core.objects.constraints.pose_constraint import PoseConstraint

from kraken.core.objects.component_group import ComponentGroup
from kraken.core.objects.hierarchy_group import HierarchyGroup
from kraken.core.objects.locator import Locator
from kraken.core.objects.joint import Joint
from kraken.core.objects.ctrlSpace import CtrlSpace
from kraken.core.objects.control import Control

from kraken.core.objects.operators.splice_operator import SpliceOperator

from kraken.core.profiler import Profiler
from kraken.helpers.utility_methods import logHierarchy


class ArmComponentGuide(Component):
    """Arm Component Guide"""

    def __init__(self, name='armGuide', parent=None, data=None):
        super(ArmComponentGuide, self).__init__(name, parent)

        # Declare Inputs Xfos
        self.clavicleEndInput = self.addInput('clavicleEnd', dataType='Xfo')

        # Declare Output Xfos
        self.bicepOutput = self.addOutput('bicep', dataType='Xfo')
        self.forearmOutput = self.addOutput('forearm', dataType='Xfo')
        self.armEndXfoOutput = self.addOutput('armEndXfo', dataType='Xfo')
        self.armEndPosOutput = self.addOutput('armEndPos', dataType='Xfo')

        # Declare Input Attrs
        self.bicepFKCtrlSizeInput = self.addInput('bicepFKCtrlSize', dataType='Float')
        self.forearmFKCtrlSizeInput = self.addInput('forearmFKCtrlSize', dataType='Float')

        # =========
        # Controls
        # =========
        controlsLayer = self.getOrCreateLayer('controls')
        ctrlCmpGrp = ComponentGroup(self.getName(), self, parent=controlsLayer)

        # IO Hierarchies
        inputHrcGrp = HierarchyGroup('inputs', parent=ctrlCmpGrp)
        cmpInputAttrGrp = AttributeGroup('inputs', parent=inputHrcGrp)

        outputHrcGrp = HierarchyGroup('outputs', parent=ctrlCmpGrp)
        cmpOutputAttrGrp = AttributeGroup('outputs', parent=outputHrcGrp)

        # Guide Controls
        self.bicepCtrl = Control('bicepFK', parent=ctrlCmpGrp, shape="sphere")
        self.bicepCtrl.setColor('blue')
        self.forearmCtrl = Control('forearmFK', parent=ctrlCmpGrp, shape="sphere")
        self.forearmCtrl.setColor('blue')
        self.wristCtrl = Control('wristFK', parent=ctrlCmpGrp, shape="sphere")
        self.wristCtrl.setColor('blue')

        # Guide Attributes
        self.bicepFKCtrlSizeInputAttr = FloatAttribute('bicepFKCtrlSize', value=2.0, parent=cmpInputAttrGrp)
        self.forearmFKCtrlSizeInputAttr = FloatAttribute('forearmFKCtrlSize', value=2.0, parent=cmpInputAttrGrp)

        # Set input attribute targets
        self.bicepFKCtrlSizeInput.setTarget(self.bicepFKCtrlSizeInputAttr)
        self.forearmFKCtrlSizeInput.setTarget(self.forearmFKCtrlSizeInputAttr)

        if data is None:
            data = {
            "name": name,
            "location": "L",
            "bicepXfo": Xfo(Vec3(2.27, 15.295, -0.753)),
            "forearmXfo": Xfo(Vec3(5.039, 13.56, -0.859)),
            "wristXfo": Xfo(Vec3(7.1886, 12.2819, 0.4906)),
            "bicepFKCtrlSize": 1.75,
            "forearmFKCtrlSize": 1.5
        }

        self.loadData(data)


    # =============
    # Data Methods
    # =============
    def saveData(self):
        """Save the data for the component to be persisted.


        Return:
        The JSON data object

        """

        data = {
                'name': self.getName(),
                'location': self.getLocation(),
                'bicepXfo': self.bicepCtrl.xfo,
                'forearmXfo': self.forearmCtrl.xfo,
                'wristXfo': self.wristCtrl.xfo,
                "bicepFKCtrlSize": self.bicepFKCtrlSizeInputAttr.getValue(),
                "forearmFKCtrlSize": self.forearmFKCtrlSizeInputAttr.getValue()
               }

        return data


    def loadData(self, data):
        """Load a saved guide representation from persisted data.

        Arguments:
        data -- object, The JSON data object.

        Return:
        True if successful.

        """

        if 'name' in data:
            self.setName(data['name'])

        self.setLocation(data['location'])
        self.bicepCtrl.xfo = data['bicepXfo']
        self.forearmCtrl.xfo = data['forearmXfo']
        self.wristCtrl.xfo = data['wristXfo']

        self.bicepFKCtrlSizeInputAttr.setValue(data['bicepFKCtrlSize'])
        self.forearmFKCtrlSizeInputAttr.setValue(data['forearmFKCtrlSize'])

        return True


    def getGuideData(self):
        """Returns the Guide data used by the Rig Component to define the layout of the final rig..

        Return:
        The JSON rig data object.

        """

        # values
        bicepPosition = self.bicepCtrl.xfo.tr
        forearmPosition = self.forearmCtrl.xfo.tr
        wristPosition = self.wristCtrl.xfo.tr

        # Calculate Bicep Xfo
        rootToWrist = wristPosition.subtract(bicepPosition).unit()
        rootToElbow = forearmPosition.subtract(bicepPosition).unit()

        bone1Normal = rootToWrist.cross(rootToElbow).unit()
        bone1ZAxis = rootToElbow.cross(bone1Normal).unit()

        bicepXfo = Xfo()
        bicepXfo.setFromVectors(rootToElbow, bone1Normal, bone1ZAxis, bicepPosition)

        # Calculate Forearm Xfo
        elbowToWrist = wristPosition.subtract(forearmPosition).unit()
        elbowToRoot = bicepPosition.subtract(forearmPosition).unit()
        bone2Normal = elbowToRoot.cross(elbowToWrist).unit()
        bone2ZAxis = elbowToWrist.cross(bone2Normal).unit()
        forearmXfo = Xfo()
        forearmXfo.setFromVectors(elbowToWrist, bone2Normal, bone2ZAxis, forearmPosition)

        bicepLen = bicepPosition.subtract(forearmPosition).length()
        forearmLen = forearmPosition.subtract(wristPosition).length()

        armEndXfo = Xfo()
        armEndXfo.tr = wristPosition
        armEndXfo.ori = forearmXfo.ori

        upVXfo = xfoFromDirAndUpV(bicepPosition, wristPosition, forearmPosition)
        upVXfo.tr = forearmPosition
        upVXfo.tr = upVXfo.transformVector(Vec3(0, 0, 5))

        data = {
            "class":"kraken.examples.arm_component.ArmComponent",
            "name": self.getName(),
            "location":self.getLocation(),
            "bicepXfo": bicepXfo,
            "forearmXfo": forearmXfo,
            "armEndXfo": armEndXfo,
            "upVXfo": upVXfo,
            "forearmLen": forearmLen,
            "bicepLen": bicepLen,
            "bicepFKCtrlSize": self.bicepFKCtrlSizeInputAttr.getValue(),
            "forearmFKCtrlSize": self.forearmFKCtrlSizeInputAttr.getValue()
        }

        return data


class ArmComponent(Component):
    """Arm Component"""

    def __init__(self, name='arm', parent=None):

        Profiler.getInstance().push("Construct Arm Component:" + name)
        super(ArmComponent, self).__init__(name, parent)

        # ================
        # Setup Hierarchy
        # ================
        controlsLayer = self.getOrCreateLayer('controls')
        ctrlCmpGrp = ComponentGroup(self.getName(), self, parent=controlsLayer)

        # IO Hierarchies
        inputHrcGrp = HierarchyGroup('inputs', parent=ctrlCmpGrp)
        cmpInputAttrGrp = AttributeGroup('inputs', parent=inputHrcGrp)

        outputHrcGrp = HierarchyGroup('outputs', parent=ctrlCmpGrp)
        cmpOutputAttrGrp = AttributeGroup('outputs', parent=outputHrcGrp)

        # ===========
        # Declare IO
        # ===========
        # Declare Inputs Xfos
        # self.clavicleEndInput = self.addInput('clavicleEnd', dataType='Xfo')
        self.clavicleEndInputTgt = self.createInput('clavicleEnd', dataType='Xfo', parent=inputHrcGrp)

        # Declare Output Xfos
        self.bicepOutputTgt = self.createOutput('bicep', dataType='Xfo', parent=outputHrcGrp)
        self.forearmOutputTgt = self.createOutput('forearm', dataType='Xfo', parent=outputHrcGrp)
        self.armEndXfoOutputTgt = self.createOutput('armEndXfo', dataType='Xfo', parent=outputHrcGrp)
        self.armEndPosOutputTgt = self.createOutput('armEndPos', dataType='Xfo', parent=outputHrcGrp)

        # Declare Input Attrs
        self.debugInputAttr = self.createInput('debug', dataType='Boolean', parent=cmpInputAttrGrp)
        self.rightSideInputAttr = self.createInput('rightSide', dataType='Boolean', parent=cmpInputAttrGrp)

        # Declare Output Attrs
        self.debugOutputAttr = self.createOutput('debug', dataType='Boolean', parent=cmpOutputAttrGrp)


        # =========
        # Controls
        # =========
        # Bicep
        self.bicepFKCtrlSpace = CtrlSpace('bicepFK', parent=ctrlCmpGrp)

        self.bicepFKCtrl = Control('bicepFK', parent=self.bicepFKCtrlSpace, shape="cube")
        self.bicepFKCtrl.alignOnXAxis()

        # Forearm
        self.forearmFKCtrlSpace = CtrlSpace('forearmFK', parent=self.bicepFKCtrl)

        self.forearmFKCtrl = Control('forearmFK', parent=self.forearmFKCtrlSpace, shape="cube")
        self.forearmFKCtrl.alignOnXAxis()

        # Arm IK
        self.armIKCtrlSpace = CtrlSpace('IK', parent=ctrlCmpGrp)
        self.armIKCtrl = Control('IK', parent=self.armIKCtrlSpace, shape="pin")

        # Add Component Params to IK control
        armSettingsAttrGrp = AttributeGroup("DisplayInfo_ArmSettings", parent=self.armIKCtrl)
        armDebugInputAttr = BoolAttribute('debug', value=True, parent=armSettingsAttrGrp)
        self.armBone1LenInputAttr = FloatAttribute('bone1Len', value=0.0, parent=armSettingsAttrGrp)
        self.armBone2LenInputAttr = FloatAttribute('bone2Len', value=0.0, parent=armSettingsAttrGrp)
        armFkikInputAttr = FloatAttribute('fkik', value=0.0, minValue=0.0, maxValue=1.0, parent=armSettingsAttrGrp)
        armSoftIKInputAttr = BoolAttribute('softIK', value=True, parent=armSettingsAttrGrp)
        armSoftDistInputAttr = FloatAttribute('softDist', value=0.0, minValue=0.0, parent=armSettingsAttrGrp)
        armStretchInputAttr = BoolAttribute('stretch', value=True, parent=armSettingsAttrGrp)
        armStretchBlendInputAttr = FloatAttribute('stretchBlend', value=0.0, minValue=0.0, maxValue=1.0, parent=armSettingsAttrGrp)

        # UpV
        self.armUpVCtrlSpace = CtrlSpace('UpV', parent=ctrlCmpGrp)

        self.armUpVCtrl = Control('UpV', parent=self.armUpVCtrlSpace, shape="triangle")
        self.armUpVCtrl.alignOnZAxis()
        self.armUpVCtrl.rotatePoints(180, 0, 0)


        # ==========
        # Deformers
        # ==========
        deformersLayer = self.getOrCreateLayer('deformers')
        defCmpGrp = ComponentGroup(self.getName(), self, parent=deformersLayer)

        bicepDef = Joint('bicep', parent=defCmpGrp)
        bicepDef.setComponent(self)

        forearmDef = Joint('forearm', parent=defCmpGrp)
        forearmDef.setComponent(self)

        wristDef = Joint('wrist', parent=defCmpGrp)
        wristDef.setComponent(self)


        # ==============
        # Constrain I/O
        # ==============
        # Constraint inputs
        armRootInputConstraint = PoseConstraint('_'.join([self.armIKCtrl.getName(), 'To', self.clavicleEndInputTgt.getName()]))
        armRootInputConstraint.setMaintainOffset(True)
        armRootInputConstraint.addConstrainer(self.clavicleEndInputTgt)
        self.bicepFKCtrlSpace.addConstraint(armRootInputConstraint)

        # Constraint outputs


        # ===============
        # Add Splice Ops
        # ===============
        # Add Solver Splice Op
        # spliceOp = SpliceOperator("armSpliceOp", "LimbSolver", "KrakenLimbSolver")
        # self.addOperator(spliceOp)

        # # Add Att Inputs
        # spliceOp.setInput("debug", self.debugInputAttr)
        # spliceOp.setInput("bone1Len", self.armBone1LenInputAttr)
        # spliceOp.setInput("bone2Len", self.armBone2LenInputAttr)
        # spliceOp.setInput("fkik", armFkikInputAttr)
        # spliceOp.setInput("softIK", softIKInputAttr)
        # spliceOp.setInput("softDist", armSoftDistInputAttr)
        # spliceOp.setInput("stretch", armStretchInputAttr)
        # spliceOp.setInput("stretchBlend", armStretchBlendInputAttr)
        # spliceOp.setInput("rightSide", self.rightSideInputAttr)

        # # Add Xfo Inputs
        # spliceOp.setInput("root", self.clavicleEndInputTgt)
        # spliceOp.setInput("bone1FK", self.bicepFKCtrl)
        # spliceOp.setInput("bone2FK", forearmFKCtrl)
        # spliceOp.setInput("ikHandle", armIKCtrl)
        # spliceOp.setInput("upV", self.armUpVCtrl)

        # # Add Xfo Outputs
        # spliceOp.setOutput("bone01Out", self.bicepOutputTgt)
        # spliceOp.setOutput("bone02Out", self.forearmOutputTgt)
        # spliceOp.setOutput("bone03Out", self.armEndXfoOutputTgt)
        # spliceOp.setOutput("bone03PosOut", self.armEndPosOutputTgt)


        # # Add Deformer Splice Op
        # spliceOp = SpliceOperator("armDeformerSpliceOp", "LimbConstraintSolver", "KrakenLimbSolver")
        # self.addOperator(spliceOp)

        # # Add Att Inputs
        # spliceOp.setInput("debug", self.debugInputAttr)

        # # Add Xfo Inputs
        # spliceOp.setInput("bone01Constrainer", self.bicepOutputTgt)
        # spliceOp.setInput("bone02Constrainer", self.forearmOutputTgt)
        # spliceOp.setInput("bone03Constrainer", self.armEndXfoOutputTgt)

        # # Add Xfo Outputs
        # spliceOp.setOutput("bone01Deformer", bicepDef)
        # spliceOp.setOutput("bone02Deformer", forearmDef)
        # spliceOp.setOutput("bone03Deformer", wristDef)

        Profiler.getInstance().pop()


    def loadData(self, data=None):

        self.setName(data.get('name', 'arm'))
        location = data.get('location', 'M')
        self.setLocation(location)

        self.clavicleEndInputTgt.xfo.tr = data['bicepXfo'].tr

        self.bicepFKCtrlSpace.xfo = data['bicepXfo']
        self.bicepFKCtrl.xfo = data['bicepXfo']
        self.bicepFKCtrl.scalePoints(Vec3(data['bicepLen'], data['bicepFKCtrlSize'], data['bicepFKCtrlSize']))

        self.bicepOutputTgt.xfo = data['bicepXfo']
        self.forearmOutputTgt.xfo = data['forearmXfo']

        self.forearmFKCtrlSpace.xfo = data['forearmXfo']
        self.forearmFKCtrl.xfo = data['forearmXfo']
        self.forearmFKCtrl.scalePoints(Vec3(data['forearmLen'], data['forearmFKCtrlSize'], data['forearmFKCtrlSize']))

        self.armIKCtrlSpace.xfo.tr = data['armEndXfo'].tr
        self.armIKCtrl.xfo.tr = data['armEndXfo'].tr

        if self.getLocation() == "R":
            self.armIKCtrl.rotatePoints(0, 90, 0)
        else:
            self.armIKCtrl.rotatePoints(0, -90, 0)

        self.armUpVCtrlSpace.xfo = data['upVXfo']
        self.armUpVCtrl.xfo = data['upVXfo']

        self.rightSideInputAttr.setValue(self.getLocation() is 'R')
        self.armBone1LenInputAttr.setMin(0.0)
        self.armBone1LenInputAttr.setMax(data['bicepLen'] * 3.0)
        self.armBone1LenInputAttr.setValue(data['bicepLen'])
        self.armBone2LenInputAttr.setMin(0.0)
        self.armBone2LenInputAttr.setMax(data['forearmLen'] * 3.0)
        self.armBone2LenInputAttr.setValue(data['forearmLen'])

        self.armEndXfoOutputTgt.xfo = data['armEndXfo']
        self.armEndPosOutputTgt.xfo = data['armEndXfo']


from kraken.core.kraken_system import KrakenSystem
ks = KrakenSystem.getInstance()
ks.registerComponent(ArmComponentGuide)
ks.registerComponent(ArmComponent)
