import itertools

def unique_permutations(word):
    permutations_set = set(itertools.permutations(word))
    return len(permutations_set)

word = "ALGEBRA"
print(unique_permutations(word))