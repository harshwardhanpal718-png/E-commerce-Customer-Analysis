"""
Execute all Jupyter Notebooks and persist output cells
"""

import os
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), '.matplotlib_cache')

import nbformat
from nbclient import NotebookClient

notebooks = [
    'notebooks/01_data_cleaning.ipynb',
    'notebooks/02_exploratory_analysis.ipynb',
    'notebooks/03_rfm_segmentation.ipynb'
]

print("="*75)
print("EXECUTING NOTEBOOKS END-TO-END")
print("="*75)

for nb_path in notebooks:
    print(f"\n[Running] {nb_path}...")
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
        
    client = NotebookClient(nb, timeout=600, kernel_name='python3')
    client.execute()
    
    with open(nb_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
        
    print(f"  -> Successfully executed and saved {nb_path} with outputs!")

print("\nALL NOTEBOOKS EXECUTED SUCCESSFULLY!")
