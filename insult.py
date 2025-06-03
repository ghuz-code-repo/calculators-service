import math


def count_trailing_zeros(base, exponent):
    # Calculate the number of digits in base^exponent
    num_digits = math.floor(exponent * math.log10(base)) + 1

    # Calculate the number of trailing zeros
    trailing_zeros = exponent * -math.log10(base) - num_digits

    return int(trailing_zeros)


# Example usage
base = 0.000003
exponent = 8000000000
print(count_trailing_zeros(base, exponent))