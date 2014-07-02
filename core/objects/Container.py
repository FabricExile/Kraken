"""Kraken - objects.container module.

Classes:
Container -- Component container representation.

"""

from kraken.core.objects.scene_item import SceneItem
from kraken.core.objects.component import BaseComponent


class Container(SceneItem):
    """Container object."""

    def __init__(self, name):
        super(Container, self).__init__(name, None)
        self.layers = []