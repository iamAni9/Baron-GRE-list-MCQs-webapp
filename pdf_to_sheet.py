from PyPDF2 import PdfReader
import os
import csv

# Load the PDF
pdf_path = 'Barron_GRE_word_list.pdf'
reader = PdfReader(pdf_path)

# Initialize variables
word_lists = {}
current_letter = None

# Function to clean and structure lines
def process_line(line):
    # Split word and meaning by multiple spaces
    if '  ' in line:
        parts = line.split('  ', 1)
        if len(parts) == 2:
            word, meaning = parts
            return word.strip(), meaning.strip()
    return None, None

# Parse the PDF content
for page in reader.pages:
    lines = page.extract_text().split('\n')
    for line in lines:
        # Detect section headers (e.g., "Barron GRE word list - A")
        if line.startswith("Barron GRE word list - "):
            current_letter = line.split('-')[-1].strip()
            if current_letter not in word_lists:
                word_lists[current_letter] = []
        # Process lines for word and meaning
        elif current_letter:
            word, meaning = process_line(line)
            if word and meaning:
                word_lists[current_letter].append((word, meaning))

# Output directory for CSV files
output_dir = './word_lists'
os.mkdir(output_dir, exist_ok=True)

# Save each word list to a separate CSV file
output_files = []
for letter, words in word_lists.items():
    file_path = os.path.join(output_dir, f'{letter}.csv')
    with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Word', 'Meaning'])  # Header
        writer.writerows(words)
    output_files.append(file_path)

print(output_files)
