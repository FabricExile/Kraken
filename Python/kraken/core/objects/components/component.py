"""Kraken - objects.component module.

Classes:
Component -- Component representation.

"""

from kraken.core.configs.config import Config
from kraken.helpers.utility_methods import mirrorData
from kraken.core.maths import *
from kraken.core.objects.object_3d import Object3D
from kraken.core.objects.layer import Layer
from kraken.core.objects.locator import Locator
from kraken.core.objects.attributes.bool_attribute import BoolAttribute
from kraken.core.objects.attributes.scalar_attribute import ScalarAttribute
from kraken.core.objects.attributes.integer_attribute import IntegerAttribute
from kraken.core.objects.attributes.string_attribute import StringAttribute

from kraken.core.objects.components.component_input_port import ComponentInputPort
from kraken.core.objects.components.component_input import ComponentInput
from kraken.core.objects.components.component_output_port import ComponentOutputPort
from kraken.core.objects.components.component_output import ComponentOutput

from kraken.log import getLogger

logger = getLogger('kraken')

# Note: does a Component need to inherit off 'Object3D'?
# These items exist only to structure a rig as a graph.
# The never get built.
class Component(Object3D):
    """Kraken Component object."""

    def __init__(self, name, parent=None, location='M', metaData=None):
        self.location = StringAttribute('location', value=location)
        super(Component, self).__init__(name, parent, metaData=metaData)
        self._color = (154, 205, 50, 255)
        self._inputs = []
        self._outputs = []
        self._operators = []
        self._items = {}

        self.setShapeVisibility(False)

        self.lockRotation(x=True, y=True, z=True)
        self.lockScale(x=True, y=True, z=True)
        self.lockTranslation(x=True, y=True, z=True)

        self._graphPos = Vec2()


    # =============
    # Name Methods
    # =============
    def getNameDecoration(self):
        """Gets the decorated name of the object.

        Returns:
            str: Decorated name of the object.

        """

        # We decorate the name of the component with the location. This
        # enables multiple components to have the same name as long as they
        # have different locations. e.g. Leg:R, and Leg:L
        return ":" + self.getLocation()


    # ==============
    # Color Methods
    # ==============
    def getComponentColor(self):
        """Gets the color assigned to this component.

        Returns:
            tuple: R, G, B, A values.

        """

        return self._color

    def setComponentColor(self, r, g, b, a):
        """Sets the componetn color by the rgba values.

        Args:
            r (int): Red value.
            g (int): Green value.
            b (int): Blue value.
            a (int): Alpha value.

        Returns:
            bool: True if successful.

        """

        self._color = (r, g, b, a)

        return True


    # =============
    # Side Methods
    # =============
    def getLocation(self):
        """Returns the location of the component as a string.

        Returns:
            str: Location of the component.

        """

        return self.location.getValue()


    def setLocation(self, location):
        """Sets the location of the component.

        Args:
            location (str): Location that the component is on.

        Returns:
            bool: True if successful.

        """

        config = Config.getInstance()
        nameTemplate = config.getNameTemplate()
        locations = nameTemplate['locations']

        if location not in locations:
            logger.warn("'{}' is not a valid location. Valid locations are: {}".format(location, ','.join(locations)))
            return False

        self.location.setValue(location)

        # The new location might cause a name colision.
        # forcing a name refresh will generate a new name if a collision exists
        self.setName(self.getName())

        return True


    # =============
    # Graph UI
    # =============
    def getGraphPos(self):
        """Returns the graphPos of the component as a string.

        Returns:
            str: The graphPos of the component.

        """

        return self._graphPos


    def setGraphPos(self, graphPos):
        """Sets the graphPos of the component.

        Args:
            graphPos (Vec2): The position in the graph where this node is placed.

        Returns:
            bool: True if successful.

        """

        self._graphPos = graphPos

        return True


    # =============
    # Layer methods
    # =============
    def getLayer(self, name):
        """Retrieves a layer from the owning container.

        Args:
            name (str): Name of the layer to find.

        Returns:
            Layer: The layer from the container.

        """

        container = self.getContainer()
        if container is None:
            container = self

        layer = container.getChildByName(name)
        if layer is not None and layer.isTypeOf('Layer') is False:
            logger.warn("No layer with name '{}' was found.".format(name))
            layer = None

        return layer


    def getOrCreateLayer(self, name):
        """Retrieves a layer from the owning container, or generates a layer (and warning message)

        Args:
            name (str): Name of the layer to retrieve or create.

        Returns:
            Layer: The layer from the container, or generated layer.

        """

        # Note: layer objects are added to the generated rig, but without a rig, they are
        # simply root items in the scene. This is because components are never built
        container = self.getContainer()

        layer = None
        if container is not None:
            layer = container.getChildByName(name)
        if layer is None or layer.isTypeOf('Layer') is False:
            layer = Layer(name, parent=container)

        if container is not None:
            container.addItem(name, layer)
        else:
            self.addItem(name, layer)

        return layer


    # ==============
    # Item Methods
    # ==============
    def addItem(self, name, item):
        """Adds a child to the component and sets the object's component attribute.

        Args:
            child (Object): Object to add as a child.

        Returns:
            bool: True if successful.

        """



        # Assign the child self as the component.
        item.setComponent(self)

        self._items[name] = item

        return True

    def getItems(self):
        """Returns all items for this component.

        Returns:
            list: Items for this component.

        """

        return dict(self._items)

    # ==============
    # Child Methods
    # ==============
    def addChild(self, child):
        """Adds a child to the component and sets the object's component attribute.

        Args:
            child (Object): Object to add as a child.

        Returns:
            bool: True if successful.

        """

        raise NotImplementedError("We should not be here. This method is to be deprecated")


    def getHierarchyNodes(self, classType='', inheritedClass=False):
        """Returns a nodeList with all children in component hierarchy that
        matches classType.

        Args:
            classType (str): Optional Class type to match.
            inheritedClass (bool): Optional Match nodes that is a sub-class of type.

        Returns:
            list: Nodes that match the class type.

        """

        assert isinstance(classType, str), "Warning in Component {}: getHierarchyNodes needs classType to be passed as string".format(self._name)


        nodeList = []

        for name, item in self._items.iteritems():

            if item.isTypeOf("Object3D") is False:
                continue

            if classType:
                if inheritedClass and item.isTypeOf(classType):
                    nodeList.append(item)
                elif item.getTypeName() == classType:
                    nodeList.append(item)
            else:
                nodeList.append(item)

            item.getDescendents(nodeList=nodeList, classType=classType, inheritedClass=inheritedClass)

        return nodeList

    # ==============
    # Input Methods
    # ==============
    def getInputs(self):
        """Returns all inputs for this component.

        Returns:
            list: Inputs for this component.

        """

        return list(self._inputs)


    def checkInputIndex(self, index):
        """Checks the supplied index is valid.

        Args:
            index (int): Input index to check.

        Returns:
            bool: True if successful.

        """

        if len(self._inputs) == 0:
            return False

        if index > len(self._inputs) - 1:
            raise IndexError("'" + str(index) + "' is out of the range of 'inputs' array.")

        return True


    def createInput(self, name, dataType, **kwargs):
        """Creates an input object and also a connected target object that matches
        the data type that is passed.

        Args:
            name (str): Name of the input to create.
            dataType (str): Data type of the input.

        Returns:
            Object: The connected target object for the input.

        """

        componentInputPort = self.addInput(name, dataType)

        # Create object
        if dataType.startswith('Xfo'):
            newInputTgt = ComponentInput(name)

        elif dataType.startswith('Boolean'):
            newInputTgt = BoolAttribute(name)

        elif dataType.startswith('Float'):
            newInputTgt = ScalarAttribute(name)

        elif dataType.startswith('Integer'):
            newInputTgt = IntegerAttribute(name)

        elif dataType.startswith('String'):
            newInputTgt = StringAttribute(name)
        else:
            raise NotImplementedError("Datatype: {} is not a supported type for createInput.".format(dataType))

        # Handle keyword arguments
        for k, v in kwargs.iteritems():
            if k == 'value':
                newInputTgt.setValue(v)
            elif k == 'minValue':
                newInputTgt.setMin(v)
                newInputTgt.setUIMin(v)
            elif k == 'maxValue':
                newInputTgt.setMax(v)
                newInputTgt.setUIMax(v)
            elif k == 'parent':
                if dataType.startswith('Xfo'):
                    v.addChild(newInputTgt)
                else:
                    v.addAttribute(newInputTgt)
            else:
                logger.warning("Keyword '%s' is not supported with createInput method!" % k)

        componentInputPort.setTarget(newInputTgt)

        return componentInputPort


    def addInput(self, name, dataType):
        """Add input port Object to this object.

        Args:
            name (str): Name of the input to create.
            dataType (str): Data type of the input.

        Returns:
            Object: New input object.

        """

        if self.getInputByName(name) is not None:
            raise Exception("'" + name + "' argument is already an output!")

        componentInputPort = ComponentInputPort(name, parent=self, dataType=dataType)

        self._inputs.append(componentInputPort)

        return componentInputPort


    def removeInputByIndex(self, index):
        """Remove ComponentInputPort at specified index.

        Args:
            index (int): Index of the ComponentInputPort to remove.

        Returns:
            bool: True if successful.

        """

        if self.checkInputIndex(index) is not True:
            return False

        del self._inputs[index]

        return True


    def removeInputByName(self, name):
        """Removes a input from this object by name.

        Args:
            name (str): Name of input to remove.

        Returns:
            bool: True if successful.

        """

        removeIndex = None

        for i, eachInput in enumerate(self._inputs):
            if eachInput.getName() == name:
                removeIndex = i

        if removeIndex is None:
            raise ValueError("'" + name + "' is not a valid input of this object.")

        self.removeInputByIndex(removeIndex)

        return True


    def getNumInputs(self):
        """Returns the number of inputs this component has.

        Returns:
            int: number of inputs of this object.

        """

        return len(self._inputs)


    def getInputByIndex(self, index):
        """Returns the input object at specified index.

        Args:
            index (int): Index of the input to return.

        Returns:
            Object: Input object at specified index.

        """

        if self.checkInputIndex(index) is not True:
            return False

        return self._inputs[index]


    def getInputByName(self, name):
        """Returns the input object with the specified name.

        Args:
            name (str): Name of the input to return.

        Returns:
            Object: Input object.

        """

        for eachInput in self._inputs:
            if eachInput.getName() == name:
                return eachInput

        return None


    # ===============
    # Output Methods
    # ===============
    def getOutputs(self):
        """Returns all outputs for this component.

        Returns:
            list: Outputs for this component.

        """

        return list(self._outputs)


    def checkOutputIndex(self, index):
        """Checks the supplied index is valid.

        Args:
            index (int): Output index to check.

        Returns:
            bool: True if successful.

        """

        if len(self._outputs) == 0:
            return False

        if index > len(self._outputs) - 1:
            raise IndexError("'" + str(index) + "' is out of the range of 'outputs' array.")

        return True


    def createOutput(self, name, dataType, **kwargs):
        """Creates an output object and also a connected target object that matches
        the data type that is passed.

        Args:
            name (str): Name of the output to create.
            dataType (str): Data type of the output.

        Returns:
            Object: The connected target object for the output.

        """

        componentOutputPort = self.addOutput(name, dataType)

        if dataType.endswith('[]'):
            newOutputTgt = []
        else:
            # Create object
            if dataType.startswith('Xfo'):
                newOutputTgt = ComponentOutput(name)

            elif dataType.startswith('Boolean'):
                newOutputTgt = BoolAttribute(name)

            elif dataType.startswith('Float'):
                newOutputTgt = ScalarAttribute(name)

            elif dataType.startswith('Integer'):
                newOutputTgt = IntegerAttribute(name)

            elif dataType.startswith('String'):
                newOutputTgt = StringAttribute(name)

        # Handle keyword arguments
        for k, v in kwargs.iteritems():
            if k == 'value':
                newOutputTgt.setValue(v)
            elif k == 'minValue':
                newOutputTgt.setMin(v)
            elif k == 'maxValue':
                newOutputTgt.setMax(v)
            elif k == 'parent':
                if isinstance(newOutputTgt, list):
                    raise Exception("Array outputs cannot be assigned to a parent. Each element in the array must be parented individually: " + name + ".")

                if dataType.startswith('Xfo'):
                    v.addChild(newOutputTgt)
                else:
                    v.addAttribute(newOutputTgt)
            else:
                logger.warning("Keyword '%s' is not supported with createOutput method!" % k)

        componentOutputPort.setTarget(newOutputTgt)

        return componentOutputPort


    def addOutput(self, name, dataType):
        """Add output port Object to this object.

        Args:
            name (str): Name of the output to create.
            dataType (str): Data type of the output.

        Returns:
            Object: New output object.

        """

        if self.getOutputByName(name) is not None:
            raise Exception("'outputObject' argument is already an output!")

        componentOutputPort = ComponentOutputPort(name, parent=self, dataType=dataType)

        self._outputs.append(componentOutputPort)

        return componentOutputPort


    def getNumOutputs(self):
        """Returns the number of outputs this component has.

        Returns:
            int: Number of outputs of this object.

        """

        return len(self._outputs)


    def getOutputByIndex(self, index):
        """Returns the output object at specified index.

        Args:
            index (int): Index of the output to return.

        Returns:
            Output object at specified index.

        """

        if self.checkOutputIndex(index) is not True:
            return False

        return self._outputs[index]


    def getOutputByName(self, name):
        """Returns the output object with the specified name.

        Args:
            name (str): Name of the output to return.

        Returns:
            Object: Output object.

        """

        for eachOutput in self._outputs:
            if eachOutput.getName() == name:
                return eachOutput

        return None


    # =================
    # Operator Methods
    # =================
    def evalOperators(self):
        """Evaluates all component operators in order they were created.

        Returns:
            bool: True if no errors during evaluation.

        """

        for op in self._operators:
            op.evaluate()

        return True


    def checkOperatorIndex(self, index):
        """Checks the supplied index is valid.

        Args:
            index (int): operator index to check.

        Returns:
            bool: True if the index is valid.

        """

        if index > len(self._operators) - 1:
            raise IndexError("'" + str(index) + "' is out of the range of the 'children' array.")

        return True


    def addOperator(self, operator):
        """Adds a operator to this object.

        Args:
            operator (Object): Object that will be a operator of this object.

        Returns:
            bool: True if successful.

        """
        operator.setParent(self)

        if operator.getBuildName() in [x.getBuildName() for x in self._operators]:
            raise IndexError("Operator with " + operator.getBuildName() + " already exists as a operator.")

        self._operators.append(operator)


        return True


    def removeOperatorByIndex(self, index):
        """Removes a operator from this object by index.

        Args:
            index (int): Index of operator to remove.

        Returns:
            bool: True if successful.

        """

        if self.checkOperatorIndex(index) is not True:
            return False

        del self._operators[index]

        return True


    def removeOperatorByName(self, name):
        """Removes a operator from this object by name.

        Args:
            name (str): Name of operator to remove.

        Returns:
            bool: True if successful.

        """

        removeIndex = None

        for i, eachOperator in enumerate(self._operators):
            if eachOperator.getName() == name:
                removeIndex = i

        if removeIndex is None:
            raise ValueError("'" + name + "' is not a valid operator of this object.")

        self.removeOperatorByIndex(removeIndex)

        return True


    def getNumOperators(self):
        """Returns the number of operators this object has.

        Returns:
            int: Number of operators of this object.

        """

        return len(self._operators)


    def getOperatorByIndex(self, index):
        """Returns the operator object at specified index.

        Args:
            index (int): Index of the operator to return.

        Returns:
            Object: Operator object at specified index.

        """

        if self.checkOperatorIndex(index) is not True:
            return False

        return self._operators[index]


    def getOperatorByName(self, name):
        """Returns the operator object with the specified name.

        Args:
            name (str): Name of the operator to return.

        Returns:
            Object: Operator if found.

        """

        for eachOperator in self._operators:
            if eachOperator.getName() == name:
                return eachOperator

        return None


    def getOperatorByType(self, childType):
        """Returns all children that are of the specified type.

        Args:
            childType (str): The object type to search for.

        Returns:
            list: Array of operator objects of the specified type.

        """

        childrenOfType = []
        for eachOperator in self._operators:
            if eachOperator.isTypeOf(childType):
                childrenOfType.append(eachOperator)

        return childrenOfType


    def getOperatorIndex(self, operator):
        """Return the index of the specified operator.

        Args:
            operator (Object): Operator to find the index of.

        Returns:
            Object: Operator if found.

        """

        for index in xrange(self.getNumOperators()):
            if self._operators[index] is operator:
                return index

        return None


    def moveOperatorToIndex(self, operator, index):
        """Moves an operator to the specified index.

        Args:
            operator (Object): Operator to move.
            index (int): Index position to move the operator to.

        Returns:
            bool: True if successful.

        """

        oldIndex = self.getOperatorIndex(operator)
        self._operators.insert(index, self._operators.pop(oldIndex))

        return True

    def getOperators(self):
        """Returns all operators for this component.

        Returns:
            list: Outputs for this component.

        """

        return list(self._operators)

    # =============
    # Data Methods
    # =============
    def saveData(self):
        """Save the data for the component to be persisted.

        Returns:
            dict: The JSON data object

        """

        data = {
            'class': self.__class__.__module__ + "." + self.__class__.__name__,
            'name': self.getName(),
            'location': self.getLocation(),
            'graphPos': self._graphPos
        }


        # TODO: AttributeGroup needs to become a hierachy object like all the others.
        # so it can be traversed usign the regular traversial methods.
        # attributeGroups = self.getChildrenByType('AttributeGroup')
        # attributeGroups = getNumAttributeGroups()
        # for grp in attributeGroups:
        for i in range(self.getNumAttributeGroups()):
            grp = self.getAttributeGroupByIndex(i)
            for j in range(grp.getNumAttributes()):
                attr = grp.getAttributeByIndex(j)
                data[attr.getName()] = attr.getValue()

        return data


    def loadData(self, data):
        """Load a saved guide representation from persisted data.

        Args:
            data (dict): The JSON data object.

        Returns:
            bool: True if successful.

        """

        location = data.get('location', None)
        compName = data.get('name', None)
        graphPos = data.get('graphPos', None)

        if location is not None:
            self.setLocation(data['location'])

        if compName is not None:
            self.setName(data['name'])

        if graphPos is not None:
            self.setGraphPos(data['graphPos'])

        for i in range(self.getNumAttributeGroups()):
            grp = self.getAttributeGroupByIndex(i)
            for i in range(grp.getNumAttributes()):
                attr = grp.getAttributeByIndex(i)
                if attr.getName() in data:
                    attr.setValue(data[attr.getName()])

        return True


    # ==================
    # Copy/Paste Methods
    # ==================
    def copyData(self):
        """Copy the data for the component to our clipboard.

        Returns:
            dict: The JSON data object

        """

        return self.saveData()

    def pasteData(self, data, setLocation=True, mirror=False):
        """Paste a copied guide representation.

        Args:
            data (dict): The JSON data object.
            setLocation (bool): Whether to set the location after pasting data.

        Returns:
            bool: True if successful.

        """

        import pprint
        print "Orig pasted data"
        pp = pprint.PrettyPrinter(indent=4)

        for k, v in data.iteritems():
            if k.endswith('Xfo'):
                print "{}: {}".format(str(k), str(v))

        if mirror:
            config = Config.getInstance()
            mirrorMap = config.getNameTemplate()['mirrorMap']
            data['location'] = mirrorMap[data['location']]
            data = mirrorData(data, 0)

            print "post mirror data"
            pp = pprint.PrettyPrinter(indent=4)

            for k, v in data.iteritems():
                if k.endswith('Xfo'):
                    print "{}: {}".format(str(k), str(v))

        # if data['location'] != self.getLocation():
        #     config = Config.getInstance()
        #     mirrorMap = config.getNameTemplate()['mirrorMap']
        #     if mirrorMap[data['location']] != data['location']:
        #         data = mirrorData(data, 0)

        # if setLocation is False:
        #     del data['location']

        self.loadData(data)

        return True


    def saveAllObjectData(self, data, classType="Control", inheritedClass=False):
        """Stores the Guide data for all objects of this type in the component.

        Args:
            data (dict): The JSON rig data object.
            classType (str): The class of the type of object we want to store to data
            inheritedClass (bool): Also include all objects that are inherited from classType

        Returns:
            dict: The JSON rig data object.

        """

        objects = self.getHierarchyNodes(classType=classType, inheritedClass=inheritedClass)
        self.saveObjectData(data, objects)

        return data

    def saveObjectData(self, data, objectList):
        """Stores the Guide data for component objects in this list.
        Guide data is xfo and curve information

        Args:
            data (dict): The JSON rig data object.
            objectList (list): list of Object3D objects

        Returns:
            dict: The JSON rig data object.

        """

        for obj in objectList:
            objName = obj.getName()
            if obj.getMetaDataItem("altLocation") is not None:
                objName = obj.getMetaDataItem("altLocation") + "_" + objName
            data[objName + "Xfo"] = obj.xfo
            if obj.isTypeOf("Curve"):
                data[objName + "CurveData"] = obj.getCurveData()

        return data

    def loadAllObjectData(self, data, classType="Control", inheritedClass=False):
        """Stores the Guide data for all objects of this type in the component.

        Args:

            data (dict): The JSON rig data object.
            classType (type): The class of the type of object we want to store to data
            inheritedClass (bool): Also include all objects that are inherited from classType

        Returns:
            dict: The JSON rig data object.

        """
        objects = self.getHierarchyNodes(classType=classType, inheritedClass=inheritedClass)
        self.loadObjectData(data, objects)

        return data

    def loadObjectData(self, data, objectList):
        """
        Loads the Guide data for component objects in this list.
        Guide data is xfo and curve information

        Args:
            data (dict): The JSON rig data object.
            objectList (list): list of Object3D objects

        """
             # this should probably live in the GuideClase
        for obj in objectList:
            objName = obj.getName()
            if obj.getMetaDataItem("altLocation") is not None:
                objName = obj.getMetaDataItem("altLocation") + "_" + objName

            if (objName + "Xfo") in data:
                obj.xfo = data[objName + "Xfo"]

            if obj.isTypeOf("Curve"):
                if (objName + "CurveData") in data:
                    obj.setCurveData(data[objName + "CurveData"])


    # ==================
    # Rig Build Methods
    # =================
    def getRigBuildData(self):
        """Returns the Guide data used by the Rig Component to define the layout
        of the final rig.

        Returns:
            dict: The JSON rig data object.

        """

        rigComponentClass = self.getRigComponentClass()

        data = {
            'class': rigComponentClass.__module__ + '.' + rigComponentClass.__name__,
            'name': self.getName(),
            'location': self.getLocation()
        }

        # automatically save all attributes.
        for i in range(self.getNumAttributeGroups()):
            grp = self.getAttributeGroupByIndex(i)
            for j in range(grp.getNumAttributes()):
                attr = grp.getAttributeByIndex(j)
                data[attr.getName()] = attr.getValue()

        return data


    def detach(self):
        """Detaches component from container.

        Raises:
            NotImplemented: This method should be implemented in sub-classes.

        """

        raise NotImplementedError("This method should be implemented in sub-classes.")

    def attach(self, container):
        """Attaches component to container.

        Args:
            container (object): container to attach to.

        Raises:
            NotImplemented: This method should be implemented in sub-classes.

        """

        raise NotImplementedError("This method should be implemented in sub-classes.")


    # ==============
    # Class Methods
    # ==============
    @classmethod
    def getComponentType(cls):
        """Enables introspection of the class prior to construction to determine if it is a guide component.

        Note:
            This is a localized method specific to the Component object.

        Returns:
            str: String name of the Component type.

        """

        return 'Base'
