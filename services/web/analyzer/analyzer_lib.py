
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Callable, DefaultDict
from collections import Counter, defaultdict, OrderedDict
from functools import lru_cache
from time import time

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import text

from analyzer.data_view.handler import DataViewHandler
from analyzer.dataset.handler import DatasetHandler
from analyzer.users.users_lib import UserHandler

from analyzer.data_view.data_view_lib import Label, LabelSequence, DataViewId
from analyzer.data_view.rich_data_view import RichDataView
from analyzer.dataset.dataset_lib import Dataset, DatasetId
from analyzer.constraint_lib import (
    TransformResourceHandler, Transform, FilterTransform, EnrichmentTransform,
)

from analyzer.text_processing import WordHistoryProcessor, WordHistoryResult

import logging

log = logging.getLogger(__name__)


DataFrame = pd.DataFrame
TransformLookup = DefaultDict[DatasetId, Dict[DataViewId, Set[Transform]]]


TAB = "\t"
COMMA = ","

stop_words = text.ENGLISH_STOP_WORDS.union(["book"])


class DataFrameCache:
    def __init__(self):
        self._cache: Dict[DataViewId, DataFrame] = {}


class Analyzer:
    DEFAULT_LIMIT = 250

    def __init__(
        self,
        data_dir: Path,
        data_view_handler: DataViewHandler,
        dataset_handler: DatasetHandler,
        user_handler: UserHandler,
        transform_resource_handler: TransformResourceHandler,
    ):
        self.data_dir = Path(data_dir)
        assert self.data_dir.exists()

        self._data_view_handler = data_view_handler
        self._dataset_handler = dataset_handler
        self._user_handler = user_handler
        self.transform_resource_handler = transform_resource_handler