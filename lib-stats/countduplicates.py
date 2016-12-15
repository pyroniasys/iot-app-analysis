# Counts the duplicate items of a specific category

import sys

from util import read_set

to_count_p = sys.argv[1]
set1_p = sys.argv[2]
set2_p = sys.argv[3]

to_count = read_set(to_count_p)
set1 = read_set(set1_p)
set2 = read_set(set2_p)

count = 0
common = []
for i in to_count:
    if i in set1 or i in set2:
        count += 1
        common.append(i)

for i in set1:
    if i in set2 and i not in common:
        count += 1
        common.append(i)

print("Number of common apps = "+str(count))
f = open("common-apps.txt", "w+")
f.writelines(common)
f.close()
