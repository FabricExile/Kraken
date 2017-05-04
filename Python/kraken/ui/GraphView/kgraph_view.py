#
# Copyright 2010-2015
#

import copy

from kraken.ui.Qt import QtWidgets, QtGui, QtCore

from pyflowgraph.graph_view import GraphView
from pyflowgraph.graph_view import MANIP_MODE_NONE, MANIP_MODE_SELECT, MANIP_MODE_PAN, MANIP_MODE_MOVE, MANIP_MODE_ZOOM

from pyflowgraph.connection import Connection
from pyflowgraph.selection_rect import SelectionRect

from knode import KNode
from kbackdrop import KBackdrop
from edit_index_widget import EditIndexWidget
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

    # ======
    # Graph
    # ======
    def displayGraph(self, rig):
        self.reset()

        self.__rig = rig

        guideComponents = self.__rig.getChildrenByType('Component')

        for component in guideComponents:
            node = KNode(self, component)
            self.addNode(node)

        for component in guideComponents:
            for i in range(component.getNumInputs()):
                componentInput = component.getInputByIndex(i)
                if componentInput.isConnected():
                    componentOutput = componentInput.getConnection()

                    self.connectPorts(
                        srcNode=componentOutput.getParent().getDecoratedName(), outputName=componentOutput.getName(),
                        tgtNode=component.getDecoratedName(), inputName=componentInput.getName()
                    )

        # Get backdrops from meta data
        metaData = self.__rig.getMetaData()
        if 'backdrops' in metaData:
            for backdrop in metaData['backdrops']:
                backdropNode = KBackdrop(self, backdrop.get('name', 'Backdrop'))
                self.addNode(backdropNode)
                backdropNode.setData(backdrop)

        self.frameAllNodes()

    def addConnection(self, connection, emitSignal=True):

        result = super(KGraphView, self).addConnection(connection, emitSignal=emitSignal)

        # Indicate that this is an indexed connection.
        outPort = connection.getSrcPortCircle().getPort()
        inPort = connection.getDstPortCircle().getPort()
        if outPort is not None and inPort is not None and outPort.getDataType() != inPort.getDataType():
            if outPort.getDataType().startswith(inPort.getDataType()) and outPort.getDataType().endswith('[]'):
                connection.setPenStyle(QtCore.Qt.DashDotLine)
                connection.setPenWidth(2.5)

        return connection

    def getNodesOfType(self, nodeType):
        """Gets all the nodes of the specified type.

        Arguments:
        nodeType -- String, class name to search nodes for.

        Return:
        list, nodes that are of the specified type.

        """

        graphNodes = self.getNodes()

        return [graphNodes[x] for x in graphNodes if type(graphNodes[x]).__name__ == nodeType]

    # =======
    # Events
    # =======
    def mousePressEvent(self, event):

        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if event.button() == QtCore.Qt.RightButton:

            zoom_with_alt_rmb = self.window().preferences.getPreferenceValue('zoom_with_alt_rmb')
            if zoom_with_alt_rmb and modifiers == QtCore.Qt.AltModifier:
                self._manipulationMode = MANIP_MODE_ZOOM
                self.setCursor(QtCore.Qt.SizeHorCursor)
                self._lastMousePos = event.pos()
                self._lastTransform = QtGui.QTransform(self.transform())
                self._lastSceneRect = self.sceneRect()
                self._lastSceneCenter = self._lastSceneRect.center()
                self._lastScenePos = self.mapToScene(event.pos())
                self._lastOffsetFromSceneCenter = self._lastScenePos - self._lastSceneCenter
                return


            def graphItemAt(item):
                if isinstance(item, KNode):
                    return item
                if isinstance(item, Connection):
                    return item
                elif item is not None:
                    return graphItemAt(item.parentItem())
                return None

            graphicItem = graphItemAt(self.itemAt(event.pos()))
            pos = self.mapToScene(event.pos())

            if graphicItem is None:

                contextMenu = QtWidgets.QMenu(self.getGraphViewWidget())
                contextMenu.setObjectName('rightClickContextMenu')
                contextMenu.setMinimumWidth(150)

                if self.getClipboardData() is not None:

                    def pasteSettings():
                        self.pasteSettings(pos)

                    def pasteSettingsMirrored():
                        self.pasteSettings(pos, mirrored=True)

                    contextMenu.addAction("Paste").triggered.connect(pasteSettings)
                    contextMenu.addAction("Paste Mirrored").triggered.connect(pasteSettingsMirrored)
                    contextMenu.addSeparator()

                graphViewWidget = self.getGraphViewWidget()
                contextMenu.addAction("Add Backdrop").triggered.connect(graphViewWidget.addBackdrop)
                contextMenu.popup(event.globalPos())

            if isinstance(graphicItem, KNode):
                self.selectNode(graphicItem, clearSelection=True, emitSignal=True)

                contextMenu = QtWidgets.QMenu(self.getGraphViewWidget())
                contextMenu.setObjectName('rightClickContextMenu')
                contextMenu.setMinimumWidth(150)

                def copySettings():
                    self.copySettings(pos)

                contextMenu.addAction("Copy").triggered.connect(copySettings)

                if self.getClipboardData() is not None:

                    def pasteSettings():
                        # Paste the settings, not modifying the location, because that will be used to determine symmetry.
                        pasteData = self.getClipboardData()['components'][0]
                        pasteData.pop('graphPos', None)

                        graphicItem.getComponent().pasteData(pasteData, setLocation=False)

                    contextMenu.addSeparator()
                    contextMenu.addAction("Paste Data").triggered.connect(pasteSettings)

                contextMenu.popup(event.globalPos())

            elif isinstance(graphicItem, Connection):

                outPort = graphicItem.getSrcPortCircle().getPort()
                inPort = graphicItem.getDstPortCircle().getPort()
                if outPort.getDataType() != inPort.getDataType():

                    if outPort.getDataType().startswith(inPort.getDataType()) and outPort.getDataType().endswith('[]'):

                        globalPos = event.globalPos()
                        contextMenu = QtWidgets.QMenu(self.getGraphViewWidget())
                        contextMenu.setObjectName('rightClickContextMenu')
                        contextMenu.setMinimumWidth(150)

                        def editIndex():
                            componentInput = graphicItem.getDstPortCircle().getPort().getComponentInput()
                            EditIndexWidget(componentInput, pos=globalPos, parent=self.getGraphViewWidget())

                        contextMenu.addAction("EditIndex").triggered.connect(editIndex)
                        contextMenu.popup(globalPos)


        elif event.button() == QtCore.Qt.LeftButton and self.itemAt(event.pos()) is None:
            self.beginNodeSelection.emit()
            self._manipulationMode = MANIP_MODE_SELECT
            self._mouseDownSelection = copy.copy(self.getSelectedNodes())
            self._selectionRect = SelectionRect(graph=self, mouseDownPos=self.mapToScene(event.pos()))

        elif event.button() == QtCore.Qt.MidButton:

            pan_with_alt = self.window().preferences.getPreferenceValue('pan_with_alt')
            if pan_with_alt is True and modifiers != QtCore.Qt.AltModifier:
                return

            self.setCursor(QtCore.Qt.OpenHandCursor)
            self._manipulationMode = MANIP_MODE_PAN
            self._lastPanPoint = self.mapToScene(event.pos())

        else:
            super(GraphView, self).mousePressEvent(event)

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
            node = KNode(self, component)
            self.addNode(node)

            self.selectNode(node, clearSelection=True, emitSignal=False)

            event.acceptProposedAction()
        else:
            super(GraphView, self).dropEvent(event)

    def wheelEvent(self, event):

        zoom_mouse_scroll = self.window().preferences.getPreferenceValue('zoom_mouse_scroll')
        if zoom_mouse_scroll is True:
            super(KGraphView, self).wheelEvent(event)

    # =============
    # Copy / Paste
    # =============
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

        # print "Paste Data"
        # print "mirrored: " + str(mirrored)
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)

        # for comp in clipboardData['components']:
        #     for k, v in comp.iteritems():
        #         if k.endswith('Xfo'):
        #             print "{}: {}".format(str(k), str(v))

        krakenSystem = KrakenSystem.getInstance()
        delta = pos - clipboardData['copyPos']
        self.clearSelection()
        pastedComponents = {}
        nameMapping = {}

        for componentData in clipboardData['components']:
            componentClass = krakenSystem.getComponentClass(componentData['class'])
            component = componentClass(parent=self.__rig)

            # if mirrored:
            component.pasteData(componentData, setLocation=True, mirror=mirrored)
            # else:
            #     component.pasteData(componentData, setLocation=True, mirror=False)

            decoratedName = component.getName() + component.getDecoratedName()
            nameMapping[componentData['name'] + ":" + componentData['location']] = decoratedName

            graphPos = component.getGraphPos()
            component.setGraphPos(Vec2(graphPos.x + delta.x(), graphPos.y + delta.y()))

            node = KNode(self, component)
            self.addNode(node)
            # self.selectNode(node, clearSelection=False)
            self.selectNode(node, clearSelection=True)

            self.copySettings(pos)

            import pprint
            print "New Data on New Node"
            pp = pprint.PrettyPrinter(indent=4)

            for comp in clipboardData['components']:
                for k, v in comp.iteritems():
                    if k.endswith('Xfo'):
                        print "{}: {}".format(str(k), str(v))

            # save a dict of the nodes using the orignal names
            pastedComponents[nameMapping[componentData['name'] + ":" + componentData['location']]] = component

        # Create Connections
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
                    continue

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
                srcNode=sourceComponent.getDecoratedName(), outputName=outputPort.getName(),
                tgtNode=targetComponent.getDecoratedName(), inputName=inputPort.getName()
            )
