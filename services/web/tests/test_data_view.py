import logging

from analyzer.users import UserId
from analyzer.dataset import DatasetId
from analyzer.data_view.data_view_lib import Label, LabelSet
from analyzer.data_view.handler import HistoryKey


logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)


def test_history_key():
    user_id1 = UserId("111")
    user