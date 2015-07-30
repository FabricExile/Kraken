
#
# Copyright 2010-2015
#


import json
from PySide import QtGui, QtCore

from pyflowgraph.node import Node
from pyflowgraph.port import InputPort, OutputPort

from kraken.core.maths import Vec2

from kraken.ui.component_inspector import ComponentInspector


def getPortColor(dataType):

    if dataType.startswith('Xfo'):
        return QtGui.QColor(128, 170, 170, 255)
    elif dataType.startswith('Float'):
        return QtGui.QColor(32, 255, 32, 255)
    elif dataType.startswith('Integer'):
        return QtGui.QColor(0, 128, 0, 255)
    elif dataType.startswith('Boolean'):
        return QtGui.QColor(255, 102, 0, 255)
    else:
        return QtGui.QColor(50, 205, 254, 255)

class KNode(Node):

    def __init__(self, graph, component):
        super(KNode, self).__init__(graph, component.getDecoratedName())

        self.__component = component
        self.__inspectorWidget = None

        for i in range(self.__component.getNumInputs()):
            componentInput = component.getInputByIndex(i)
            name = componentInput.getName()
            dataType = componentInput.getDataType()
            color = getPortColor(dataType)

            self.addPort(InputPort(self, graph, name, color, dataType))

        for i in range(self.__component.getNumOutputs()):
            componentOutput = component.getOutputByIndex(i)
            name = componentOutput.getName()
            dataType = componentOutput.getDataType()
            color = getPortColor(dataType)

            self.addPort(OutputPort(self, graph, name, color, dataType))

        self.setGraphPos( QtCore.QPointF( self.__component.getGraphPos().x, self.__component.getGraphPos().y ) )


    def getName(self):
        return self.__component.getDecoratedName()

    def getComponent(self):
        return self.__component

    #########################
    ## Graph Pos

    def translate(self, x, y):
        super(KNode, self).translate(x, y)
        graphPos = self.getGraphPos()
        self.__component.setGraphPos( Vec2(graphPos.x(), graphPos.y()) )


    def pushGraphPosToComponent(self):
        graphPos = self.getGraphPos()
        self.__component.setGraphPos( Vec2(graphPos.x(), graphPos.y()) )


    #########################
    ## Events

    def mouseDoubleClickEvent(self, event):
        if self.__inspectorWidget is None:
            parentWidget = self.getGraph().getGraphViewWidget()
            self.__inspectorWidget = ComponentInspector(component=self.__component, parent=parentWidget, nodeItem=self)
            self.__inspectorWidget.show()
        else:
            self.__inspectorWidget.setFocus()

        super(KNode, self).mouseDoubleClickEvent(event)


    def inspectorClosed(self):
        self.__inspectorWidget = None


