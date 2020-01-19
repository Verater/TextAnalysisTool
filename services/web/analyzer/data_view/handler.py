from __future__ import annotations

from typing import List, Dict, Deque, Tuple, Optional, Union
from collections import deque
from pathlib import Path
import json
import logging

from analyzer.data_view.data_view_lib import (
    DataView, DataViewId, Label, LabelSequence,
)
from analyzer.constraint_lib import (
    Transform, TransformDef, TransformList, EnrichmentTransform, FilterTransform,
)
from analyzer.dataset.dataset_lib import Dataset, DatasetId
from analyzer.users.users_lib import User, UserId

from analyzer.utils import Serializable, SerializableHandler, SerializableType


log = logging.getLogger(__name__)


class HistoryKey(tuple, Serializable):
    SEPARATOR = "_"

    def __new__(cls, user_id: UserId, dataset_id: DatasetId) -> HistoryKey:
        return tuple.__new__(HistoryKey, tuple((user_id, dataset_id)))

    @property
    def user_id(self) -> UserId:
        return self[0]

    @property
    def dataset_id(self) -> DatasetId:
        return self[1]

    def serialize(self) -> SerializableType:
        return self.SEPARATOR.join([self.user_id, self.dataset_id])

    @classmethod
    def deserialize(cls, s: str) -> HistoryKey:
        user_id, dataset_id = s.split(cls.SEPARATOR)
        return HistoryKey(user_id=user_id, dataset_id=dataset_id)

    def __repr__(self) -> str:
        return "<User:%s Dataset:%s>" % (self.user_id, self.dataset_id)


HistoryLookup = Dict[HistoryKey, DataViewId]


class DataViewHistoryHandler(SerializableHandler):
    def __init__(self, path: Path):
        self._path = path
        self._data_view_history: HistoryLookup = {}

        self._loaded = False
        self.load()

    def serialize(self) -> Dict[SerializableType, SerializableType]:
        sorted_keys = sorted(self._data_view_history.keys())
        return {key.serialize(): self._data_view_history[key] for key in sorted_keys}

    @classmethod
    def deserialize(cls, d: Dict[str, str]) -> HistoryLookup:
        return {
            HistoryKey.deserialize(key): DataViewId(value) for key, value in d.items()
        }

    @classmethod
    def initialization_data(cls) -> HistoryLookup:
        return {}

    def load(self):
        try:
            data_view_history = self._load(self._path)
        except Exception as exc:
            log.error("Could not load data_view_history '%s': %s", self._path, exc)
            data_view_history = {}

        self._data_view_history = data_view_history
        self._loaded = True

    def save(self):
        if not self._loaded:
            log.warning("Attempting to save DataViews that have not been loaded")
            return
        self._save(self._path)

    def keys(self):
        return self._data_view_history.keys()

    @classmethod
    def make_key(cls, user_id: UserId, dataset_id: DatasetId) -> HistoryKey:
        return HistoryKey(user_id, dataset_id)

    def has_key(self, key: HistoryKey) -> bool:
        return key in self._data_view_history

    def get_key(self, key: HistoryKey) -> DataViewId:
        return self._data_view_history.get(key)

    def set_key(self, key: HistoryKey, data_view_id: DataViewId):
        self._data_view_history[key] = data_view_id
        self.save()

    def has(self, user_id: UserId, dataset_id: DatasetId) -> bool:
        return HistoryKey(user_id, dataset_id) in self._data_view_history

    def get(self, user_id: UserId, dataset_id: DatasetId) -> DataViewId:
        return self.get_key(HistoryKey(user_id, dataset_id))

    def set(self, user_id: UserId, dataset_id: DatasetId, data_view_id: DataViewId):
        self.set_key(HistoryKey(user_id, dataset_id), data_view_id)

    def data_view_ids_by_user_id(self, user_id: UserId) -> List[DataViewId]:
        return [
            self.get_key(dv) for dv in self._data_view_history if dv.user_id == user_id
        ]


class DataViewHandler(SerializableHandler):
    def __init__(self, path: Path):
        self._path = path

        self._data_views: List[DataView] = []
        self._data_view_by_id: Dict[DataViewId, DataView] = {}

        self._label_by_name_by_data_view: Dict[DataView, Dict[str, Label]] = {}

        self._data_view_id_by_serialization: Dict[str, DataViewId] = {}

        self._loaded = False
        self.load()

    def serialize(self) -> List:
        return [data_view.serialize() for data_view in self._data_views]

    @classmethod
    def deserialize(cls, lst: List) -> List[DataView]:
        return [DataView.deserialize(elem) for elem in lst]

    @classmethod
    def initialization_data(cls) -> List[DataView]:
        return []

    def load(self):
        try:
            data_views = self._load(self._path)
        except Exception as exc:
            log.error("Could not load '%s': %s", self._path, exc)
            data_views = self.initialization_data()

        self._data_views = data_views

        self._data_view_by_id.clear()
        for data_view in self._data_views:
            self._index_data_view(data_view)

        self._loaded = True

    def save(self):
        if not self._load