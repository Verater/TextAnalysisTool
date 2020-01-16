from __future__ import annotations

from typing import List, Dict, Optional, Union
from collections import deque
from enum import Enum
import logging

from analyzer.utils import Serializable
from analyzer.data_view import DataViewId
from analyzer.dataset.dataset_lib import DatasetId
from analyzer.users.users_lib import UserId
from analyzer.constraint_lib import (
    TransformList, TransformTree,
)


log = logging.getLogger(__name__)


class LabelType(Enum):
    ALL = "all"
    DERIVED = "derived"
    ORIGINAL = "original"
    ACTIVE = "active"


class Label(Serializable):
    KEY_NAME = "n"
    KEY_WIDTH = "w"
    KEY_FONT_SIZE = "s"

    DEFAULT_WIDTH = 150
    DEFAULT_FONT_SIZE = 18

    def __init__(
        self,
        name: str,
        width: Optional[int] = None,
        font_size: Optional[int] = None,
    ):
        self._name = name
        self._width = width
        self._font_size = font_size

    @property
    def name(self) -> str:
        return self._name

    @property
    def width(self) -> int:
        return self._width or self.DEFAULT_WIDTH

    @property
    def font_size(self) -> int:
        return self._font_size or self.DEFAULT_FONT_SIZE

    def serialize(self) -> Dict[str, Union[int, str]]:
        d = {self.KEY_NAME: str(self.name)}
        if self._width:
            d[self.KEY_WIDTH] = int(self._width)