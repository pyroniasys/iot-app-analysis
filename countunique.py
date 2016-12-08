# Counts the unique items of a specific category

import sys

to_count_p = sys.argv[1]
set1_p = sys.argv[2]
set2_p = sys.argv[3]

def read_set(name):
    s_f = open(name, "r")
    s = s_f.readlines()
    s_f.close()
    return s

to_count = read_set(to_count_p)
set1 = read_set(set1_p)
set2 = read_set(set2_p)

count = 0
for i in to_count:
    if i not in set1 and i not in set2:
        count += 1

print("Number of unique "+to_count_p+" = "+str(count))
