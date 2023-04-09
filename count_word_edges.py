from format_corpus import read_cmu_file_bh, get_legal_onsets
import re
from collections import defaultdict
import csv
from format_corpus import get_legal_onsets, read_cmu_file_bh, read_cmu_phone_file


#Returns a dictionary of [tuple of string] => [integer] where the keys are word-final consonant clusters
# and the values are their frequency of occurrence in transcripts
# transcripts: a list of list of string, where each string is a DARPABET sound
# consonants: a list of DARPABET consonant symbols
def word_final_codas(transcripts, consonants, remove_exotics = False):
    consonant_spaces = [" "+consonant for consonant in consonants]
    consonant_re = "|".join(consonant_spaces)
    word_final_consonants_re = "(("+consonant_re+")+)$"
    print(word_final_consonants_re)
    coda_counts = defaultdict(lambda: 0)
    print(len(transcripts))
    for transcript in transcripts:
        transcript_str = " ".join(transcript)
        coda_match = re.search(word_final_consonants_re, transcript_str)
        if coda_match:
            coda = tuple(coda_match.group(0).split())
            coda_counts[coda] += 1
        else:
            coda_counts[tuple()] += 1 #Words that end in vowels
    return coda_counts

# Creates a csv file where the columns are consonant cluster, onset frequency, and coda frequency
def output_counts(output_fn, onset_counts, coda_counts):
    output_file = open(output_fn, "w", newline="")
    header_fields = ["Cluster", "Length", "Onset count", "Coda count", "Onset proportion", "Coda proportion",
                     "Onset prob2", "Coda prob2"]
    coda_probs = compute_prob_model2(coda_counts)
    onset_probs = compute_prob_model2(onset_counts)
    coda_props = compute_proportion(coda_counts)
    onset_props = compute_proportion(onset_counts)

    dictwriter = csv.DictWriter(fieldnames= header_fields, f=output_file)
    dictwriter.writeheader()
    for cluster in set(list(onset_counts.keys()) + list(coda_counts.keys())):
        row_dict = {"Cluster": str(cluster), "Length":len(cluster),
                    "Onset count": onset_counts[cluster], "Coda count": coda_counts[cluster],
                    "Onset proportion": onset_props[cluster], "Coda proportion": coda_props[cluster],
                    "Onset prob2": onset_probs[cluster], "Coda prob2": coda_probs[cluster]}
        dictwriter.writerow(row_dict)
    output_file.close()

def compute_proportion(count_dict):
    total = sum(count_dict.values())
    props = defaultdict(lambda:0)
    props.update({key:count/total for key,count in count_dict.items()})
    return props

#Returns a joint probability distribution of P(Consonants, Length) = P(cons|length)P(length)/normalizer:
# dictionary from (tuple of string, consonants) => number
#count_dict: dictionary from (tuple of string) => number, representing the corpus counts of consonant sequences
#length_smooth: number to be added to the count of each length
def compute_prob_model2(count_dict, length_smooth = 10000):
    #Get lengths
    lengths = set([len(cluster) for cluster in count_dict])

    #Separate counts by length
    #Dictionary from length => {dictionary from cluster => count}
    cluster_counts = {length:{cluster: count for cluster, count in count_dict.items() if len(cluster) == length} for length in
                      lengths}

    #Compute P(length)
    length_counts = {length: sum(counts.values()) + length_smooth for length, counts in cluster_counts.items()}
    smoothed_length_norm = sum(length_counts.values())
    length_probs = {length: length_sum/smoothed_length_norm for length,length_sum in length_counts.items()}
    print("P(Length)", length_probs)

    #Compute P(cons|length) for each length
    condit_probs = {}
    for length in cluster_counts:
        norm = float(sum([count for cluster, count in cluster_counts[length].items()]))
        condit_probs[length] = {cluster: count/norm for cluster, count in cluster_counts[length].items()}
        print(condit_probs[length])

    #Compute P(cons|length)P(length)/(normalizer)
    joint_probs = defaultdict(lambda:0)
    for length in condit_probs:
        length_prob = length_probs[length]
        scaled = {cluster: condit_prob * length_prob for cluster, condit_prob in condit_probs[length].items()}
        joint_probs.update(scaled)
    normalizer = sum(joint_probs.values())
    joint_probs.update({key: value/normalizer for key, value in joint_probs.items()})

    return joint_probs


def main():
    cmu_file = "CMUDictionaryEditedWithCELEXFrequenciesPublicVersion2.xls"
    cmu_phone_file = "cmudict-0.7b.phones.txt"
    output_file = "cmu_bh_word_edges.csv"
    phone_types, consonants = read_cmu_phone_file(cmu_phone_file)
    vowels = phone_types["vowel"]
    transcripts = read_cmu_file_bh(cmu_file)
    final_consonants = word_final_codas(transcripts, consonants)
    initial_consonants = get_legal_onsets(transcripts,vowels, counts=True)
    output_counts(output_file, initial_consonants, final_consonants)

if __name__ == "__main__":
    main()





