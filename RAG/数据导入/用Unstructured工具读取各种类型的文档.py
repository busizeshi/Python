from unstructured.partition.text import partition_text

text="../data/黑悟空/设定.txt"

elements = partition_text(text)

for element in elements:
    print(element)
    print('****'*20)