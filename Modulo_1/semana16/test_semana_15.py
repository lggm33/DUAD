import pytest
from semana15.ejercicio1 import bubble_sort

def test_bubble_sort_short_list():
    assert bubble_sort([5, 8, 1, 3, 7, 2]) == [1, 2, 3, 5, 7, 8]

def test_bubble_sort_long_list():
    assert bubble_sort([18, 20, 27, 36, 44, 15, 55, 65, 77, 91]) == [15, 18, 20, 27, 36, 44, 55, 65, 77, 91]

def test_bubble_sort_empty_list():
    assert bubble_sort([]) == []

def test_bubble_sort_invalid_input():
    with pytest.raises(TypeError):
        bubble_sort("Input must be a list") 