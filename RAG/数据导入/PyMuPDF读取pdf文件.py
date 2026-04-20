import pymupdf

doc=pymupdf.open("../data/黑悟空/黑神话悟空.pdf")

text=[page.get_text() for page in doc]

print(text)

