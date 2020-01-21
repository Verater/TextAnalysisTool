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
            user_handler=self.user_handler