import pytest
import sys
from io import StringIO
from semana6.Ejercicio_Funciones import sum_all_numbers, print_string_backwards, count_lowercase_letters, count_uppercase_letters, order_alphabetically, is_prime, prime_filter

# Tests for Ejercicio 3
def test_sum_all_numbers_positive():
    assert sum_all_numbers([1, 2, 3, 4, 5]) == 15
    
def test_sum_all_numbers_negative():
    assert sum_all_numbers([-1, -2, -3, -4, -5]) == -15
    
def test_sum_all_numbers_mixed():
    assert sum_all_numbers([-10, 5, 0, 15, -5]) == 5

# Tests for Ejercicio 4
def test_print_string_backwards_hello(monkeypatch):
    # Redirect stdout to capture print output
    captured_output = StringIO()
    monkeypatch.setattr(sys, 'stdout', captured_output)
    
    print_string_backwards("Hello")
    
    assert captured_output.getvalue() == "o\nl\nl\ne\nH\n"
    
def test_print_string_backwards_empty(monkeypatch):
    captured_output = StringIO()
    monkeypatch.setattr(sys, 'stdout', captured_output)
    
    print_string_backwards("")
    
    assert captured_output.getvalue() == ""
    
def test_print_string_backwards_numbers(monkeypatch):
    captured_output = StringIO()
    monkeypatch.setattr(sys, 'stdout', captured_output)
    
    print_string_backwards("12345")
    
    assert captured_output.getvalue() == "5\n4\n3\n2\n1\n"

# Tests for Ejercicio 5
def test_count_lowercase_letters_mixed():
    assert count_lowercase_letters("Hello World") == 8
    
def test_count_lowercase_letters_all_lower():
    assert count_lowercase_letters("all lowercase") == 12
    
def test_count_lowercase_letters_no_lower():
    assert count_lowercase_letters("12345 UPPERCASE") == 0
    

# Tests for Ejercicio 6
def test_order_alphabetically_words():
    assert order_alphabetically("python-variable-funcion-computadora-monitor") == "computadora-funcion-monitor-python-variable"
    
def test_order_alphabetically_colors():
    assert order_alphabetically("verde-rojo-azul-amarillo-negro") == "amarillo-azul-negro-rojo-verde"
    
def test_order_alphabetically_numbers():
    assert order_alphabetically("5-3-1-4-2") == "1-2-3-4-5"

# Tests for Ejercicio 7
def test_is_prime_small_primes():
    assert is_prime(5) == True
    
def test_is_prime_non_primes():
    assert is_prime(6) == False
    
def test_is_prime_large_number():
    assert is_prime(97) == True
    
def test_prime_filter_mixed_list():
    assert prime_filter([1, 2, 3, 4, 5, 6, 7, 8, 9]) == [2, 3, 5, 7]
    
def test_prime_filter_all_primes():
    assert prime_filter([2, 3, 5, 7, 11, 13]) == [2, 3, 5, 7, 11, 13]
    
def test_prime_filter_no_primes():
    assert prime_filter([1, 4, 6, 8, 9, 10]) == []
