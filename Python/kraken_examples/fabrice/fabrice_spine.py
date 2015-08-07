from kraken.core.maths import Vec3

from kraken.core.objects.components.base_example_component import BaseExampleComponent

from kraken.core.objects.attributes.attribute_group import AttributeGroup
from kraken.core.objects.attributes.bool_attribute import BoolAttribute
from kraken.core.objects.attributes.integer_attribute import IntegerAttribute
from kraken.core.objects.attributes.scalar_attribute import ScalarAttribute
from kraken.core.objects.attributes.string_attribute import StringAttribute

from kraken.core.objects.constraints.pose_constraint import PoseConstraint
from kraken.core.objects.constraints.position_constraint import PositionConstraint
from kraken.core.objects.constraints.orientation_constraint import OrientationConstraint

from kraken.core.objects.component_group import ComponentGroup
from kraken.core.objects.components.component_output import ComponentOutput
from kraken.core.objects.hierarchy_group import HierarchyGroup
from kraken.core.objects.locator import Locator
from kraken.core.objects.joint import Joint
from kraken.core.objects.ctrlSpace import CtrlSpace
from kraken.core.objects.layer import Layer
from kraken.core.objects.control import Control

from kraken.core.objects.operators.splice_operator import SpliceOperator

from kraken.core.profiler import Profiler
from kraken.helpers.utility_methods import logHierarchy


class FabriceSpine(BaseExampleComponent):
    """Spine Component"""

    def __init__(self, name="spineBase", parent=None):
        super(FabriceSpine, self).__init__(name, parent)

        # ===========
        # Declare IO
        # ===========
        # Declare Inputs Xfos
        self.spineMainSrtInputTgt = self.createInput('mainSrt', dataType='Xfo', parent=self.inputHrcGrp).getTarget()

        # Declare Output Xfos
        self.spineCogOutputTgt = self.createOutput('cog', dataType='Xfo', parent=self.outputHrcGrp).getTarget()
        self.spineBaseOutputTgt = self.createOutput('spineBase', dataType='Xfo', parent=self.outputHrcGrp).getTarget()
        self.spineEndOutputTgt = self.createOutput('spineEnd', dataType='Xfo', parent=self.outputHrcGrp).getTarget()
        self.spineEndCtrlOutputTgt = self.createOutput('spineEndCtrl', dataType='Xfo', parent=self.outputHrcGrp).getTarget()

        self.spineVertebraeOutput = self.createOutput('spineVertebrae', dataType='Xfo[]')

        # Declare Input Attrs
        self.drawDebugInputAttr = self.createInput('drawDebug', dataType='Boolean', value=False, parent=self.cmpInputAttrGrp).getTarget()
        self.rigScaleInputAttr = self.createInput('rigScale', dataType='Float', value=1.0, parent=self.cmpInputAttrGrp).getTarget()
        self.lengthInputAttr = self.createInput('length', dataType='Float', value=1.0, parent=self.cmpInputAttrGrp).getTarget()

        # Declare Output Attrs


class FabriceSpineGuide(FabriceSpine):
    """Fabrice Spine Component Guide"""

    def __init__(self, name='spine', parent=None):

        Profiler.getInstance().push("Construct Fabrice Spine Guide Component:" + name)
        super(FabriceSpineGuide, self).__init__(name, parent)

        # =========
        # Controls
        # ========
        guideSettingsAttrGrp = AttributeGroup("GuideSettings", parent=self)
        self.numDeformersAttr = IntegerAttribute('numDeformers', value=1, minValue=0, maxValue=20, parent=guideSettingsAttrGrp)
        self.numDeformersAttr.setValueChangeCallback(self.updateNumDeformers)

        # Guide Controls
        self.cogCtrl = Control('cog', parent=self.ctrlCmpGrp, shape="circle")
        self.cogCtrl.rotatePoints(90, 0, 0)
        self.cogCtrl.scalePoints(Vec3(3.0, 3.0, 3.0))
        self.cogCtrl.setColor('red')

        self.spineBaseCtrl = Control('spineBase', parent=self.ctrlCmpGrp, shape='pin')
        self.spineBaseCtrl.rotatePoints(90, 0, 0)
        self.spineBaseCtrl.translatePoints(Vec3(0, 1.0, 0))

        self.spineBaseHandleCtrl = Control('spineBaseHandle', parent=self.ctrlCmpGrp, shape='pin')
        self.spineBaseHandleCtrl.rotatePoints(90, 0, 0)
        self.spineBaseHandleCtrl.translatePoints(Vec3(0, 1.0, 0))

        self.spineEndHandleCtrl = Control('spineEndHandle', parent=self.ctrlCmpGrp, shape='pin')
        self.spineEndHandleCtrl.rotatePoints(90, 0, 0)
        self.spineEndHandleCtrl.translatePoints(Vec3(0, 1.0, 0))

        self.spineEndCtrl = Control('spineEnd', parent=self.ctrlCmpGrp, shape='pin')
        self.spineEndCtrl.rotatePoints(90, 0, 0)
        self.spineEndCtrl.translatePoints(Vec3(0, 1.0, 0))

        # ===============
        # Add Splice Ops
        # ===============
        # Add Spine Splice Op
        self.bezierSpineSpliceOp = SpliceOperator('spineGuideSpliceOp', 'BezierSpineSolver', 'Kraken', alwaysEval=True)
        self.addOperator(self.bezierSpineSpliceOp)

        # Add Att Inputs
        self.bezierSpineSpliceOp.setInput('drawDebug', self.drawDebugInputAttr)
        self.bezierSpineSpliceOp.setInput('rigScale', self.rigScaleInputAttr)
        self.bezierSpineSpliceOp.setInput('length', self.lengthInputAttr)

        # Add Xfo Inputs
        self.bezierSpineSpliceOp.setInput('base', self.spineBaseCtrl)
        self.bezierSpineSpliceOp.setInput('baseHandle', self.spineBaseHandleCtrl)
        self.bezierSpineSpliceOp.setInput('tipHandle', self.spineEndHandleCtrl)
        self.bezierSpineSpliceOp.setInput('tip', self.spineEndCtrl)

        # Add Xfo Outputs
        self.bezierSpineSpliceOp.setOutput('outputs', self.spineVertebraeOutput.getTarget())

        self.loadData({
            'name': name,
            'location': 'M',
            'cogPos': Vec3(0.0, 1.65, 0.75),
            'cogCtrlCrvData': self.cogCtrl.getCurveData(),
            'spineBasePos': Vec3(0.0, 1.65, 0.75),
            'spineBaseCtrlCrvData': self.spineBaseCtrl.getCurveData(),
            'spineBaseHandlePos': Vec3(0.0, 1.6, -0.7),
            'spineBaseHandleCtrlCrvData': self.spineBaseHandleCtrl.getCurveData(),
            'spineEndHandlePos': Vec3(0.0, 1.15, -2.0),
            'spineEndHandleCtrlCrvData': self.spineEndHandleCtrl.getCurveData(),
            'spineEndPos': Vec3(0.0, 0.65, -3.1),
            'spineEndCtrlCrvData': self.spineEndCtrl.getCurveData(),
            'numDeformers': 6
        })

        Profiler.getInstance().pop()

    # ==========
    # Callbacks
    # ==========
    def updateNumDeformers(self, count):
        """Generate the guide controls for the variable outputes array.

        Arguments:
        count -- object, The number of joints inthe chain.

        Return:
        True if successful.

        """

        if count == 0:
            raise IndexError("'count' must be > 0")


        vertebraeOutputs = self.spineVertebraeOutput.getTarget()
        if count > len(vertebraeOutputs):
            for i in xrange(len(vertebraeOutputs), count):
                debugCtrl = Control('spine' + str(i+1).zfill(2), parent=self.outputHrcGrp, shape="vertebra")
                debugCtrl.rotatePoints(0, -90, 0)
                debugCtrl.scalePoints(Vec3(0.5, 0.5, 0.5))
                debugCtrl.setColor("yellowLight")
                vertebraeOutputs.append(debugCtrl)

        elif count < len(vertebraeOutputs):
            numExtraCtrls = len(vertebraeOutputs) - count
            for i in xrange(numExtraCtrls):
                extraCtrl = vertebraeOutputs.pop()
                self.outputHrcGrp.removeChild(extraCtrl)

        return True


    # =============
    # Data Methods
    # =============
    def saveData(self):
        """Save the data for the component to be persisted.

        Return:
        The JSON data object

        """

        data = super(FabriceSpineGuide, self).saveData()

        data['cogPos'] = self.cogCtrl.xfo.tr
        data['cogCtrlCrvData'] = self.cogCtrl.getCurveData()

        data['spineBasePos'] = self.spineBaseCtrl.xfo.tr
        data['spineBaseCtrlCrvData'] = self.spineBaseCtrl.getCurveData()

        data['spineBaseHandlePos'] = self.spineBaseHandleCtrl.xfo.tr
        data['spineBaseHandleCtrlCrvData'] = self.spineBaseHandleCtrl.getCurveData()

        data['spineEndHandlePos'] = self.spineEndHandleCtrl.xfo.tr
        data['spineEndHandleCtrlCrvData'] = self.spineEndHandleCtrl.getCurveData()

        data['spineEndPos'] = self.spineEndCtrl.xfo.tr
        data['spineEndCtrlCrvData'] = self.spineEndCtrl.getCurveData()

        data['numDeformers'] = self.numDeformersAttr.getValue()

        return data


    def loadData(self, data):
        """Load a saved guide representation from persisted data.

        Arguments:
        data -- object, The JSON data object.

        Return:
        True if successful.

        """

        super(FabriceSpineGuide, self).loadData( data )

        self.cogCtrl.xfo.tr = data["cogPos"]
        self.cogCtrl.setCurveData(data['cogCtrlCrvData'])

        self.spineBaseCtrl.xfo.tr = data["spineBasePos"]
        self.spineBaseCtrl.setCurveData(data['spineBaseCtrlCrvData'])

        self.spineBaseHandleCtrl.xfo.tr = data["spineBaseHandlePos"]
        self.spineBaseHandleCtrl.setCurveData(data['spineBaseHandleCtrlCrvData'])

        self.spineEndHandleCtrl.xfo.tr = data["spineEndHandlePos"]
        self.spineEndHandleCtrl.setCurveData(data['spineEndHandleCtrlCrvData'])

        self.spineEndCtrl.xfo.tr = data["spineEndPos"]
        self.spineEndCtrl.setCurveData(data['spineEndCtrlCrvData'])

        self.numDeformersAttr.setValue(data["numDeformers"])

        length = data["spineBasePos"].distanceTo(data["spineBaseHandlePos"]) + data["spineBaseHandlePos"].distanceTo(data["spineEndHandlePos"]) + data["spineEndHandlePos"].distanceTo(data["spineEndPos"])
        self.lengthInputAttr.setMax(length * 3.0)
        self.lengthInputAttr.setValue(length)

        self.bezierSpineSpliceOp.evaluate()

        return True


    def getRigBuildData(self):
        """Returns the Guide data used by the Rig Component to define the layout of the final rig.

        Return:
        The JSON rig data object.

        """

        data = super(FabriceSpineGuide, self).getRigBuildData()

        data['cogPos'] = self.cogCtrl.xfo.tr
        data['cogCtrlCrvData'] = self.cogCtrl.getCurveData()

        data['spineBasePos'] = self.spineBaseCtrl.xfo.tr
        data['spineBaseCtrlCrvData'] = self.spineBaseCtrl.getCurveData()

        data['spineBaseHandlePos'] = self.spineBaseHandleCtrl.xfo.tr
        data['spineBaseHandleCtrlCrvData'] = self.spineBaseHandleCtrl.getCurveData()

        data['spineEndHandlePos'] = self.spineEndHandleCtrl.xfo.tr
        data['spineEndHandleCtrlCrvData'] = self.spineEndHandleCtrl.getCurveData()

        data['spineEndPos'] = self.spineEndCtrl.xfo.tr
        data['spineEndCtrlCrvData'] = self.spineEndCtrl.getCurveData()

        data['numDeformers'] = self.numDeformersAttr.getValue()

        return data


    # ==============
    # Class Methods
    # ==============
    @classmethod
    def getComponentType(cls):
        """Enables introspection of the class prior to construction to determine if it is a guide component.

        Return:
        The true if this component is a guide component.

        """

        return 'Guide'

    @classmethod
    def getRigComponentClass(cls):
        """Returns the corresponding rig component class for this guide component class

        Return:
        The rig component class.

        """

        return FabriceSpineRig


class FabriceSpineRig(FabriceSpine):
    """Fabrice Spine Component"""

    def __init__(self, name="spine", parent=None):

        Profiler.getInstance().push("Construct Spine Rig Component:" + name)
        super(FabriceSpineRig, self).__init__(name, parent)


        # =========
        # Controls
        # =========
        # COG
        self.cogCtrlSpace = CtrlSpace('cog', parent=self.ctrlCmpGrp)
        self.cogCtrl = Control('cog', parent=self.cogCtrlSpace, shape="circle")
        self.cogCtrl.rotatePoints(90, 0, 0)
        self.cogCtrl.scalePoints(Vec3(3.0, 3.0, 3.0))
        self.cogCtrl.translatePoints(Vec3(0.0, 0.0, 0.2))
        self.cogCtrl.lockScale(x=True, y=True, z=True)
        self.cogCtrl.setColor("orange")

        # Spine Base
        self.spineBaseCtrlSpace = CtrlSpace('spineBase', parent=self.cogCtrl)
        self.spineBaseCtrl = Control('spineBase', parent=self.spineBaseCtrlSpace, shape="pin")
        self.spineBaseCtrl.rotatePoints(90, 0, 0)
        self.spineBaseCtrl.translatePoints(Vec3(0, 1.0, 0))
        self.spineBaseCtrl.lockScale(x=True, y=True, z=True)

        # Spine Base Handle
        self.spineBaseHandleCtrlSpace = CtrlSpace('spineBaseHandle', parent=self.spineBaseCtrl)
        self.spineBaseHandleCtrl = Control('spineBaseHandle', parent=self.spineBaseHandleCtrlSpace, shape="pin")
        self.spineBaseHandleCtrl.rotatePoints(90, 0, 0)
        self.spineBaseHandleCtrl.translatePoints(Vec3(0, 1.0, 0))
        self.spineBaseHandleCtrl.lockScale(x=True, y=True, z=True)
        self.spineBaseHandleCtrl.setColor("orange")

        # Spine End
        self.spineEndCtrlSpace = CtrlSpace('spineEnd', parent=self.cogCtrl)
        self.spineEndCtrl = Control('spineEnd', parent=self.spineEndCtrlSpace, shape="pin")
        self.spineEndCtrl.rotatePoints(90, 0, 0)
        self.spineEndCtrl.lockScale(x=True, y=True, z=True)
        self.spineEndCtrl.translatePoints(Vec3(0, 1.0, 0))

        # Spine End Handle
        self.spineEndHandleCtrlSpace = CtrlSpace('spineEndHandle', parent=self.spineEndCtrl)
        self.spineEndHandleCtrl = Control('spineEndHandle', parent=self.spineEndHandleCtrlSpace, shape="pin")
        self.spineEndHandleCtrl.rotatePoints(90, 0, 0)
        self.spineEndHandleCtrl.translatePoints(Vec3(0, 1.0, 0))
        self.spineEndHandleCtrl.lockScale(x=True, y=True, z=True)
        self.spineEndHandleCtrl.setColor("orange")


        # ==========
        # Deformers
        # ==========
        deformersLayer = self.getOrCreateLayer('deformers')
        self.defCmpGrp = ComponentGroup(self.getName(), self, parent=deformersLayer)
        self.chestDef = Joint('chest', parent=self.defCmpGrp)
        self.chestDef.setComponent(self)

        self.deformerJoints = []
        self.spineOutputs = []
        self.setNumDeformers(1)


        # =====================
        # Create Component I/O
        # =====================
        # Setup component Xfo I/O's
        self.spineVertebraeOutput.setTarget(self.spineOutputs)

        # =====================
        # Constraint Deformers
        # =====================
        self.chestDefConstraint = PoseConstraint('_'.join([self.chestDef.getName(), 'To', self.spineBaseOutputTgt.getName()]))
        self.chestDefConstraint.addConstrainer(self.spineBaseOutputTgt)
        self.chestDef.addConstraint(self.chestDefConstraint)

        # ==============
        # Constrain I/O
        # ==============

        # Constraint inputs
        self.spineSrtInputConstraint = PoseConstraint('_'.join([self.cogCtrlSpace.getName(), 'To', self.spineMainSrtInputTgt.getName()]))
        self.spineSrtInputConstraint.addConstrainer(self.spineMainSrtInputTgt)
        self.spineSrtInputConstraint.setMaintainOffset(True)
        self.cogCtrlSpace.addConstraint(self.spineSrtInputConstraint)

        # Constraint outputs
        self.spineCogOutputConstraint = PoseConstraint('_'.join([self.spineCogOutputTgt.getName(), 'To', self.cogCtrl.getName()]))
        self.spineCogOutputConstraint.addConstrainer(self.cogCtrl)
        self.spineCogOutputTgt.addConstraint(self.spineCogOutputConstraint)

        # Spine Base
        self.spineBaseOutputPosConstraint = PositionConstraint('_'.join([self.spineBaseOutputTgt.getName(), 'PosTo', self.spineOutputs[0].getName()]))
        self.spineBaseOutputPosConstraint.addConstrainer(self.spineOutputs[0])
        self.spineBaseOutputTgt.addConstraint(self.spineBaseOutputPosConstraint)

        self.spineBaseOutputOriConstraint = OrientationConstraint('_'.join([self.spineBaseOutputTgt.getName(), 'PosTo', self.cogCtrl.getName()]))
        self.spineBaseOutputOriConstraint.addConstrainer(self.cogCtrl)
        self.spineBaseOutputTgt.addConstraint(self.spineBaseOutputOriConstraint)

        # Spine End
        self.spineEndOutputConstraint = PoseConstraint('_'.join([self.spineEndOutputTgt.getName(), 'To', 'spineEnd']))
        self.spineEndOutputConstraint.addConstrainer(self.spineOutputs[0])
        self.spineEndOutputTgt.addConstraint(self.spineEndOutputConstraint)

        self.spineEndCtrlOutputConstraint = PoseConstraint('_'.join([self.spineEndCtrlOutputTgt.getName(), 'To', self.spineEndCtrl.getName()]))
        self.spineEndCtrlOutputConstraint.addConstrainer(self.spineEndCtrl)
        self.spineEndCtrlOutputTgt.addConstraint(self.spineEndCtrlOutputConstraint)


        # ===============
        # Add Splice Ops
        # ===============
        # Add Spine Splice Op
        self.bezierSpineSpliceOp = SpliceOperator('spineSpliceOp', 'BezierSpineSolver', 'Kraken')
        self.addOperator(self.bezierSpineSpliceOp)

        # Add Att Inputs
        self.bezierSpineSpliceOp.setInput('drawDebug', self.drawDebugInputAttr)
        self.bezierSpineSpliceOp.setInput('rigScale', self.rigScaleInputAttr)
        self.bezierSpineSpliceOp.setInput('length', self.lengthInputAttr)

        # Add Xfo Inputs
        self.bezierSpineSpliceOp.setInput('base', self.spineBaseCtrl)
        self.bezierSpineSpliceOp.setInput('baseHandle', self.spineBaseHandleCtrl)
        self.bezierSpineSpliceOp.setInput('tipHandle', self.spineEndHandleCtrl)
        self.bezierSpineSpliceOp.setInput('tip', self.spineEndCtrl)

        # Add Xfo Outputs
        self.bezierSpineSpliceOp.setOutput('outputs', self.spineOutputs)

        # Add Deformer Splice Op
        self.deformersToOutputsSpliceOp = SpliceOperator('spineDeformerSpliceOp', 'MultiPoseConstraintSolver', 'Kraken', alwaysEval=True)
        self.addOperator(self.deformersToOutputsSpliceOp)

        # Add Att Inputs
        self.deformersToOutputsSpliceOp.setInput('drawDebug', self.drawDebugInputAttr)
        self.deformersToOutputsSpliceOp.setInput('rigScale', self.rigScaleInputAttr)

        # Add Xfo Outputs
        self.deformersToOutputsSpliceOp.setInput('constrainers', self.spineOutputs)

        # Add Xfo Outputs
        self.deformersToOutputsSpliceOp.setOutput('constrainees', self.deformerJoints)

        Profiler.getInstance().pop()


    def setNumDeformers(self, numDeformers):

        # Add new deformers and outputs
        for i in xrange(len(self.spineOutputs), numDeformers):
            name = 'spine' + str(i + 1).zfill(2)
            spineOutput = ComponentOutput(name, parent=self.outputHrcGrp)
            self.spineOutputs.append(spineOutput)

        for i in xrange(len(self.deformerJoints), numDeformers):
            name = 'spine' + str(i + 1).zfill(2)
            spineDef = Joint(name, parent=self.defCmpGrp)
            spineDef.setComponent(self)
            self.deformerJoints.append(spineDef)

        return True


    def loadData(self, data=None):
        """Load a saved guide representation from persisted data.

        Arguments:
        data -- object, The JSON data object.

        Return:
        True if successful.

        """

        super(FabriceSpineRig, self).loadData( data )

        # Get Data
        cogPos = data['cogPos']
        cogCtrlCrvData = data['cogCtrlCrvData']

        spineBasePos = data['spineBasePos']
        spineBaseCtrlCrvData = data['spineBaseCtrlCrvData']

        spineBaseHandlePos = data['spineBaseHandlePos']
        spineBaseHandleCtrlCrvData = data['spineBaseHandleCtrlCrvData']

        spineEndHandlePos = data['spineEndHandlePos']
        spineEndHandleCtrlCrvData = data['spineEndHandleCtrlCrvData']

        spineEndPos = data['spineEndPos']
        spineEndCtrlCrvData = data['spineEndCtrlCrvData']

        numDeformers = data['numDeformers']

        # Set Xfos
        self.cogCtrlSpace.xfo.tr = cogPos
        self.cogCtrl.xfo.tr = cogPos
        self.cogCtrl.setCurveData(cogCtrlCrvData)

        self.spineBaseCtrlSpace.xfo.tr = spineBasePos
        self.spineBaseCtrl.xfo.tr = spineBasePos
        self.spineBaseCtrl.setCurveData(spineBaseCtrlCrvData)

        self.spineBaseHandleCtrlSpace.xfo.tr = spineBaseHandlePos
        self.spineBaseHandleCtrl.xfo.tr = spineBaseHandlePos
        self.spineBaseHandleCtrl.setCurveData(spineBaseHandleCtrlCrvData)

        self.spineEndHandleCtrlSpace.xfo.tr = spineEndHandlePos
        self.spineEndHandleCtrl.xfo.tr = spineEndHandlePos
        self.spineEndHandleCtrl.setCurveData(spineEndHandleCtrlCrvData)

        self.spineEndCtrlSpace.xfo.tr = spineEndPos
        self.spineEndCtrl.xfo.tr = spineEndPos
        self.spineEndCtrl.setCurveData(spineEndCtrlCrvData)

        length = spineBasePos.distanceTo(spineBaseHandlePos) + spineBaseHandlePos.distanceTo(spineEndHandlePos) + spineEndHandlePos.distanceTo(spineEndPos)
        self.lengthInputAttr.setMax(length * 3.0)
        self.lengthInputAttr.setValue(length)

        # Update number of deformers and outputs
        self.setNumDeformers(numDeformers)

        # Updating constraint to use the updated last output.
        self.spineEndOutputConstraint.setConstrainer(self.spineOutputs[-1], index=0)

        # ============
        # Set IO Xfos
        # ============

        # ====================
        # Evaluate Splice Ops
        # ====================
        # evaluate the spine op so that all the output transforms are updated.
        self.bezierSpineSpliceOp.evaluate()

        # evaluate the constraint op so that all the joint transforms are updated.
        self.deformersToOutputsSpliceOp.evaluate()

        # evaluate the constraints to ensure the outputs are now in the correct location.
        self.spineSrtInputConstraint.evaluate()
        self.spineCogOutputConstraint.evaluate()
        self.spineBaseOutputPosConstraint.evaluate()
        self.spineBaseOutputOriConstraint.evaluate()
        self.spineEndOutputConstraint.evaluate()
        self.spineEndCtrlOutputConstraint.evaluate()



from kraken.core.kraken_system import KrakenSystem
ks = KrakenSystem.getInstance()
ks.registerComponent(FabriceSpineGuide)
ks.registerComponent(FabriceSpineRig)