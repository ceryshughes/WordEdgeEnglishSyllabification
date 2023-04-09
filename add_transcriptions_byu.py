import csv
from collections import defaultdict
import re

#Returns (string) lowercase orthography: (list) transcription dictionary
def read_cmu_file(file_name):
    transcriptions = defaultdict(lambda:[""])
    for line in open(file_name):
        line = line.strip('\n')
        if len(line) > 0 and not line.startswith(";;;"):
            line = line.split("  ")
            orth = line[0].lower()
            transcrip = line[1].split(" ")
            transcriptions[orth] = transcrip
    return transcriptions

#Reads BYU data file and adds phonetic transcriptions from cmu_dict
def read_byu_add_transcriptions(cmu_dict):
    byu_fn = "BYU Syllabification Survey.csv"
    byu_file = open(byu_fn, encoding='utf-8-sig', newline="")
    byu_fields = ["Word","# of Medial Consonants",	"# of .C*",	"# of C.*",	"# of CC.*","# of CCC.*","# of ?",	"prop. of .C*",	"prop. of C.*",	"prop. of CC.*","prop. of CCC.*","prop. of ?"]
    byu_reader = csv.DictReader(byu_file)#, fieldnames = byu_fields)

    new_rows = []
    for row in byu_reader:

        new_row = {}
        orth = row["Word"].strip()
        print(orth)
        transcrip = " ".join(cmu_dict[orth])
        transcrip = re.sub(r'ER([012])', r'UH\1 R', transcrip)
        new_row["Transcription"] = transcrip
        new_row.update(row)
        new_rows.append(new_row)

    byu_file.close()

    #Write transcriptions in new version of the BYU file
    new_byu_fn = "BYU Syllabification Survey Transcriptions.csv"
    new_byu_file = open(new_byu_fn, "w", newline="")
    byu_fields.insert(1, "Transcription")
    new_byu_writer = csv.DictWriter(new_byu_file, fieldnames = byu_fields)
    new_byu_writer.writeheader()
    for row in new_rows:
        print(row)
        row.pop('')
        new_byu_writer.writerow(row)
    new_byu_file.close()

def main():
    cmu_dict = read_cmu_file("cmudict-0.7b.txt")
    read_byu_add_transcriptions(cmu_dict)

main()


