from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from time import time
import logging

from analyzer.analyzer_lib import Analyzer
from analyzer.constraint_lib import transform_manager, TransformDef, TransformResourceHandler
from analyzer.query_processor_lib import QueryResponse, QueryErrorResponse
from analyzer.dataset.dataset_lib import Dataset, DatasetId
from analyzer.dataset.handler import DatasetHandler
from analyzer.data_view.data_view_lib import (
    DataView, DataViewId, LabelSequence, TransformList,
)
from analyzer.data_view.handler import DataViewHandler, DataViewHistoryHandler
from analyzer.data_view.rich_data_view import RichDataView
from analyzer.users.users_lib import User, UserHandler, UserId
from analyzer.transforms.enrichments_lib import TagHandler


log = logging.getLogger(__name__)


class InvalidLabelTypeException(ValueError):
    pass


class UserHasNoAssociatedDatasetsException(ValueError):
    pass


class Session:
    DEFAULT_LIMIT = 10

    def __init__(
        self,
        config_dir: Path,
        data_dir: Path,
        users_filename: str,
        datasets_filename: str,
        data_views_filename: str,
        data_view_history_filename: str,
        tag_prefix: str,
    ):
        log.info("Creating new session")

        self.config_dir = config_dir
        self.data_dir = data_dir

        users_path = config_dir / users_filename
        datasets_path = config_dir / datasets_filename
        data_views_path = config_dir / data_views_filename
        data_view_history_path = config_dir / data_view_history_filename
        tag_dir = config_dir

        self.user_handler = UserHandler(users_path)
        self.dataset_handler = DatasetHandler(datasets_path)
        self.data_view_handler = DataViewHandler(data_views_path)
        self.data_view_history_handler = DataViewHistoryHandler(data_view_history_path)
        self.tag_handler = TagHandler(tag_dir, tag_prefix)

        self.transform_resource_handler = TransformResourceHandler(
            tag_handler=self.tag_handler,
        )

        self._analyzer = Analyzer(
            data_dir=self.data_dir,
            user_handler=self.user_handler,
            dataset_handler=self.dataset_handler,
            data_view_handler=self.data_view_handler,
            transform_resource_handler=self.transform_resource_handler,
        )

        user = self.user_handler.default_user
        dataset_id = self.user_handler.get_last_dataset_id(user.id)

        if dataset_id:
            data_view_id = self.data_view_history_handler.get(user.id, dataset_id)
        else:
            data_view_id = None

        if data_view_id:
            log.info("warming up data frame for %s", data_view_id)
            start_time = time()
            self._analyzer.active_dataframe(self.rich_data_view(data_view_id))
            log.info(f"done: {time() - start_time:.2f} sec")
        else:
            log.info("DataView ID is %s", data_view_id)

    def get_most_recent_dataset_id(self, user: Union[User, UserId]) -> DatasetId:
        return self.user_handler.get_last_dataset_id(user.id)

    def get_most_recent_dataset(self, user: Union[User, UserId]) -> Dataset:
        return self.dataset_handler.by_id(
            self.user_handler.get_last_dataset_id(user.id)
        )

    def set_most_recent_dataset(self, user_id: UserId, filename: str) -> Optional[Dataset]:
        """Set the active dataset to the specified filename"""
        if not filename:
            log.error('Attempting to load dataset with empty filename: "%s"', filename)
            return

        # has this filename already been recorded?
        if not self.dataset_handler.has_filename(filename):
            # if not, create a Dataset for the new filename
            log.info("Creating new dataset: %s", filename)
            dataset = self.dataset_handler.create(filename)
        else:
            # if so, load the Dataset associated with this filename
            dataset = self.dataset_handler.by_filename(filename)

        self.user_handler.set_last_dataset(user_id, dataset.id)
        return dataset

    def rich_data_view(self, data_view_id: DataViewId) -> RichDataView:
        data_view = self.data_view_handler.by_id(data_view_id)
        log.info(f"DataView {data_view} from {data_view_id}")
        return RichDataView(
            data_view=data_view,
            dataset=self.dataset_handler.by_id(data_view.dataset_id),
            user=self.user_handler.by_id(data_view.user_id),
        )

    def refresh_data_views(self):
        self.data_view_handler.load()

    @classmethod
    def get_transform_defs(cls) -> List[TransformDef]:
        return list(transform_manager.get_transform_defs())

    def get_most_recent_data_view(
        self,
        user_id: UserId,
        dataset_id: Optional[DatasetId] = None,
    ) -> DataView:
        # if no dataset id is supplied, then look up the user's most recently used dataset
        if dataset_id is None:
            dataset_id = self.user_handler.get_last_dataset_id(user_id)

        if dataset_id is None:
            raise UserHasNoAssociatedDatasetsException(
                f"user {user_id} has no associated datasets (likely the user's first session)"
            )

        if self.data_view_history_handler.has(user_id, dataset_id):
            data_view_id = self.data_view_history_handler.get(user_id, dataset_id)
            data_view = self.data_view_handler.by_id(data_view_id)
            if data_view:
                return data_view

        return self.create_data_view(
            parent=None,
            user_id=user_id,
            dataset_id=dataset_id,
            labels=self._analyzer.get_dataset_labels(
                self.dataset_handler.by_id(dataset_id)
            ),
        )

    def create_data_view(
        self,
        parent: Optional[DataViewId],
        user_id: UserId,
        dataset_id: DatasetId,
        labels: Optional[LabelSequence] = None,
        transforms: Optional[TransformList] = None,
    ) -> DataView:
        if not labels:
            labels = self._analyzer.get_dataset_labels(
                self.dataset_handler.by_id(dataset_id)
            )

        data_view = self.data_view_handler.create(
            parent=parent,
            user=user_id,
            dataset=dataset_id,
            labels=labels,
            transforms=transforms,
        )

        self.data_view_history_handler.set(user_id, dataset_id, data_view.id)

        return data_view

    def add_tags(
        self,
        tags: List[str],
        primary_keys: List[str],
        primary_key_name: str,
        data_view_id: DataViewId,
    ):
        data_view = self.rich_data_view(data_view_id)

       