import math
from collections import Counter

def permute_data(data):
    frequency_counter = Counter(data)
    perms = math.factorial(len(data))
    for key in frequency_counter.values():
        perms //= math.factorial(key)
    return(perms)

word = 'ALGEBRA'
print('Number of permutations for word ALGEBRA:', permute_data(word))