import pytest
import numpy as np
from src.analysis.cluster import sort_cluster_labels


@pytest.mark.parametrize(
    "labels,expected",
    [(np.array([2, 2, 2, 0, 0, 1, 0, 1, 2]),
      np.array([0, 0, 0, 1, 1, 2, 1, 2, 0])),
     (np.array([0, 0, 0, 1, 1, 2]),
      np.array([0, 0, 0 ,1, 1, 2])),
    ],
)
def test_sort_cluster_labels(labels, expected):
    sorted_labels = sort_cluster_labels(labels)
    assert all(sorted_labels == expected)
