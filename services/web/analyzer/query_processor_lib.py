from __future__ import annotations

from typing import List, Dict, Optional
import json
import logging
import pandas as pd

from analyzer.utils import Serializable, SerializableType
from analyzer.constraint_lib import transform_manager, Transform, TransformList

DataFrame = pd.DataFrame

log = logging.getLogger(__name__)


class QueryResponse(Serializable, dict):
    KEY_DATA = "data"
    KEY_LABELS = "labels"
    KEY_ERROR = "error"
    KEY_MSG = "msg"

    EMPTY = None

    active_keys = [KEY_ERROR, KEY_MSG, KEY_DATA, KEY_LABELS]

    def __init__(
        self,
        msg: Optional[str] = None,
        data: Optional[SerializableType] = None,
        la