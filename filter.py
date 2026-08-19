import os
path = r"C:\Users\piotr\OneDrive - Imperial College London\hard_carbon_text_mining"
file = "test_dois.txt"

with open(os.path.join(path, file), 'r') as file:
    lines = file.readlines()

acs_dois = [line.strip() for line in lines if line.startswith('10.1021')]

with open(os.path.join(path, "acs_dois.txt"), 'w') as file:
    for doi in acs_dois:
        file.write(doi + '\n')