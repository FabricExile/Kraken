#
# Copyright 2010-2015
#

from PySide import QtGui, QtCore

from pyflowgraph.graph_view import GraphView
from pyflowgraph.connection import Connection
from knode import KNode

from kraken.core.maths import Vec2
from kraken.core.kraken_system import KrakenSystem
from kraken.core.configs.config import Config


class KGraphView(GraphView):

    beginCopyData = QtCore.Signal()
    endCopyData = QtCore.Signal()

    beginPasteData = QtCore.Signal()
    endPasteData = QtCore.Signal()

    _clipboardData = None

    def __init__(self, parent=None):
        super(KGraphView, self).__init__(parent)
        self.__rig = None
        self.setAcceptDrops(True)


    def getRig(self):
        return self.__rig

    #######################
    ## Graph
    def displayGraph(self, rig):
        self.reset()

        self.__rig = rig

        guideComponents = self.__rig.getChildrenByType('Component')

        for component in guideComponents:
            self.addNode(KNode(self, component))

        for component in guideComponents:
            for i in range(component.getNumInputs()):
                componentInput = component.getInputByIndex(i)
                if componentInput.isConnected():
                    componentOutput = componentInput.getConnection()

                    self.connectPorts(
                        srcNode = componentOutput.getParent().getDecoratedName(), outputName = componentOutput.getName(),
                        tgtNode = component.getDecoratedName(), inputName=componentInput.getName()
                    )

        self.frameAllNodes()



    ################################################
    ## Events
    def mousePressEvent(self, event):

        # If the contextual node list is open, close it.
        contextualNodeList = self.getGraphViewWidget().getContextualNodeList()
        if contextualNodeList is not None and contextualNodeList.isVisible():
            contextualNodeList.searchLineEdit.clear()
            contextualNodeList.hide()

        if event.button() == QtCore.Qt.MouseButton.RightButton:

            def graphItemAt(item):
                if isinstance(item, KNode):
                    return item
                elif item is not None:
                    return graphItemAt(item.parentItem())
                return None

            graphicItem = graphItemAt(self.itemAt(event.pos()))
            pos = self.mapToScene(event.pos())

            if graphicItem is None:

                if self.getClipboardData() is not None:

                    contextMenu = QtGui.QMenu(self.getGraphViewWidget())
                    contextMenu.setObjectName('rightClickContextMenu')
                    contextMenu.setMinimumWidth(150)

                    def pasteSettings():
                        self.pasteSettings(pos)

                    def pasteSettingsMirrored():
                        self.pasteSettings(pos, mirrored=True)

                    contextMenu.addAction("Paste").triggered.connect(pasteSettings)
                    contextMenu.addAction("Paste Mirrored").triggered.connect(pasteSettingsMirrored)
                    contextMenu.popup(event.globalPos())


            if isinstance(graphicItem, KNode) and graphicItem.isSelected():
                contextMenu = QtGui.QMenu(self.getGraphViewWidget())
                contextMenu.setObjectName('rightClickContextMenu')
                contextMenu.setMinimumWidth(150)

                def copySettings():
                    self.copySettings(pos)

                contextMenu.addAction("Copy").triggered.connect(copySettings)

                if self.getClipboardData() is not None:

                    def pasteSettings():
                        # Paste the settings, not modifying the location, because that will be used to determine symmetry.
                        graphicItem.getComponent().pasteData(self.getClipboardData()['components'][0], setLocation=False)

                    contextMenu.addSeparator()
                    contextMenu.addAction("Paste Data").triggered.connect(pasteSettings)

                contextMenu.popup(event.globalPos())

        else:
            super(KGraphView, self).mousePressEvent(event)


    def dragEnterEvent(self, event):
        textParts = event.mimeData().text().split(':')
        if textParts[0] == 'KrakenComponent':
            event.accept()
        else:
            event.setDropAction(QtCore.Qt.IgnoreAction)
            super(GraphView, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        super(GraphView, self).dragMoveEvent(event)
        event.accept()

    def dropEvent(self, event):
        textParts = event.mimeData().text().split(':')
        if textParts[0] == 'KrakenComponent':
            componentClassName = textParts[1]

            # Add a component to the rig placed at the given position.
            dropPosition = self.mapToScene(event.pos())

            # construct the node and add it to the graph.
            krakenSystem = KrakenSystem.getInstance()
            componentClass = krakenSystem.getComponentClass( componentClassName )
            component = componentClass(parent=self.getRig())
            component.setGraphPos(Vec2(dropPosition.x(), dropPosition.y()))
            self.addNode(KNode(self, component) )

            event.acceptProposedAction()
        else:
            super(GraphView, self).dropEvent(event)



    #######################
    ## Copy/Paste

    def getClipboardData(self):
        return self.__class__._clipboardData

    def copySettings(self, pos):
        clipboardData = {}

        copiedComponents = []
        nodes = self.getSelectedNodes()
        for node in nodes:
            copiedComponents.append(node.getComponent())

        componentsJson = []
        connectionsJson = []
        for component in copiedComponents:
            componentsJson.append(component.copyData())

            for i in range(component.getNumInputs()):
                componentInput = component.getInputByIndex(i)
                if componentInput.isConnected():
                    componentOutput = componentInput.getConnection()
                    connectionJson = {
                        'source': componentOutput.getParent().getDecoratedName() + '.' + componentOutput.getName(),
                        'target': component.getDecoratedName() + '.' + componentInput.getName()
                    }

                    connectionsJson.append(connectionJson)

        clipboardData = {
            'components': componentsJson,
            'connections': connectionsJson,
            'copyPos': pos
        }

        self.__class__._clipboardData = clipboardData


    def pasteSettings(self, pos, mirrored=False, createConnectionsToExistingNodes=True):

        clipboardData = self.__class__._clipboardData

        krakenSystem = KrakenSystem.getInstance()
        delta = pos - clipboardData['copyPos']
        self.clearSelection()
        pastedComponents = {}
        nameMapping = {}

        for componentData in clipboardData['components']:
            componentClass = krakenSystem.getComponentClass(componentData['class'])
            component = componentClass(parent=self.__rig)
            decoratedName = componentData['name'] + component.getNameDecoration()
            nameMapping[decoratedName] = decoratedName
            if mirrored:
                config = Config.getInstance()
                mirrorMap = config.getNameTemplate()['mirrorMap']
                component.setLocation(mirrorMap[componentData['location']])
                nameMapping[decoratedName] = componentData['name'] + component.getNameDecoration()
                component.pasteData(componentData, setLocation=False)
            else:
                component.pasteData(componentData, setLocation=True)
            graphPos = component.getGraphPos( )
            component.setGraphPos(Vec2(graphPos.x + delta.x(), graphPos.y + delta.y()))
            node = KNode(self,component)
            self.addNode(node)
            self.selectNode(node, False)

            # save a dict of the nodes using the orignal names
            pastedComponents[nameMapping[decoratedName]] = component


        for connectionData in clipboardData['connections']:
            sourceComponentDecoratedName, outputName = connectionData['source'].split('.')
            targetComponentDecoratedName, inputName = connectionData['target'].split('.')

            sourceComponent = None

            # The connection is either between nodes that were pasted, or from pasted nodes
            # to unpasted nodes. We first check that the source component is in the pasted group
            # else use the node in the graph.
            if sourceComponentDecoratedName in nameMapping:
                sourceComponent = pastedComponents[nameMapping[sourceComponentDecoratedName]]
            else:
                if not createConnectionsToExistingNodes:
                    continue;

                # When we support copying/pasting between rigs, then we may not find the source
                # node in the target rig.
                if not self.hasNode(sourceComponentDecoratedName):
                    continue
                node = self.getNode(sourceComponentDecoratedName)
                sourceComponent = node.getComponent()

            targetComponentDecoratedName = nameMapping[targetComponentDecoratedName]
            targetComponent = pastedComponents[targetComponentDecoratedName]

            outputPort = sourceComponent.getOutputByName(outputName)
            inputPort = targetComponent.getInputByName(inputName)

            inputPort.setConnection(outputPort)
            self.connectPorts(
                srcNode = sourceComponent.getDecoratedName(), outputName = outputPort.getName(),
                tgtNode = targetComponent.getDecoratedName(), inputName=inputPort.getName()
            )

