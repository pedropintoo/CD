<<<<<<< HEAD
# coding: utf-8

import time


# Leibniz formula for pi
def leibniz_pi_precision(precision=10):
    rv = 1
    for i in range(precision):
        time.sleep(0.001)
        if i % 2 == 0:
            rv -= 1/(2*(i+1)+1)
        else:
            rv += 1/(2*(i+1)+1)
    return rv * 4.0


# Bailey–Borwein–Plouffe formula
# spigot algorithm for computing the nth binary digit of the mathematical
# constant pi using base-16 representation
def bailey_pi_precision(precision=10):
    p16 = 1
    pi = 0
    for k in range(precision):
        time.sleep(0.01)
        pi += 1.0/p16 * (4.0/(8*k + 1) - 2.0/(8*k + 4) - 1.0/(8*k + 5) - 1.0/(8*k+6));
        p16 *= 16;
    return pi
=======
def dht_hash(text, seed=0, maximum=2**10):
    """ FNV-1a Hash Function. """
    fnv_prime = 16777619
    offset_basis = 2166136261
    h = offset_basis + seed
    for char in text:
        h = h ^ ord(char)
        h = h * fnv_prime
    return h % maximum


def contains(begin, end, node):
    """Check node is contained between begin and end in a ring."""
    #TODO
    if (begin < node <= end): return True
    if (begin > end and (node > begin or node <= end)): return True
    return False
>>>>>>> cecd2bc (Initial commit)
