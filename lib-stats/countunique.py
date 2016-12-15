# Counts the unique items of a specific category

import sys

from util import read_set, get_name

to_count_p = sys.argv[1]
set1_p = sys.argv[2]
set2_p = sys.argv[3]

to_count = read_set(to_count_p)
set1 = read_set(set1_p)
set2 = read_set(set2_p)

to_count_name = get_name(to_count_p)

count = 0
unique = []
for i in to_count:
    if i not in set1 and i not in set2:
        count += 1
        unique.append(i)

print("Number of unique "+to_count_name+" = "+str(count))

f = open(to_count_name+"-unique.txt", "w+")
f.writelines(unique)
f.close()
