#Convert syllabification data to longer format so probability distributions can be calculated more easily
from format_corpus import read_cmu_phone_file, syllabify
import csv
import re
from format_corpus import read_cmu_phone_file
from collections import defaultdict
from BYUSyllabification import *
from BYUFormatOutput import *



#Returns a dictionary from orthographic word(string) to its transcription(tuple of string)
def word_transcriptions(byu_fn):
    byu_file = open(byu_fn, encoding='utf-8-sig', newline="")
    byu_reader = csv.DictReader(byu_file)
    transcriptions = {}
    for row in byu_reader:
        transcriptions[row["Word"]] = row["Transcription"]
    return transcriptions

#Given a transcription (list of string), returns the medial cluster (list of string)
#Returns None if no cluster
def get_cluster(transcrip, cmu_vowels, cmu_consonants):
    print(transcrip, type(transcrip))
    transcrip = " ".join(transcrip)
    transcrip = re.sub(r'\d', "", transcrip)
    vowel_re = "(" + "|".join(cmu_vowels) + ")"
    consonants_re = "(" + "|".join([cons + " " for cons in cmu_consonants]) + ")"
    cluster_re = vowel_re + " (" + consonants_re + "+)" + vowel_re
    #print(cluster_re, transcrip)
    cluster = re.search(cluster_re, transcrip)
    if cluster:
        cluster = cluster.group(2).split(' ')[:-1]
    return cluster




#Given the Eddington corpus filename (byu_fn),
#A list of cmu vowel symbols (cmu_vowels, list of string)
#A list of CMU consonant symbols (cmu_consonants)
#Returns a dictionary of the form:
# cluster (tuple of string) => syllabifications (list of MedialSyllabification objects)
# where each cluster is a unique medial consonant cluster from the Eddington corpus
# and the syllabifications are datapoints about each syllabification offered to the participants
#If separate_words = True, then the keys of the returned dictionary will be a tuple of the word and cluster:
#they will be of the form (string, tuple of string)
#check_stress: If True, the returned MedialSyllabification objects will have a field preceding_stress, which will
#   be True iff the vowel preceding the cluster is stressed (has a non-zero digit in the CMU transcription)
#   and will have a stressed_transcription field that contains the transcription without stress removed
def read_byu_transcribed(byu_fn, cmu_vowels, cmu_consonants, separate_words = False, check_stress = False):
    byu_dict = defaultdict(lambda: []) #Dictionary from string (orthography) => list of MedialSyllabification objects
    byu_file = open(byu_fn, encoding='utf-8-sig', newline="")
    #byu_fields = ["Word", "Transcription", "# of Medial Consonants", "# of .C*", "# of C.*", "# of CC.*", "# of CCC.*", "# of ?",
                 # "prop. of .C*", "prop. of C.*", "prop. of CC.*", "prop. of CCC.*", "prop. of ?"]
    byu_reader = csv.DictReader(byu_file)

    boundary_codes = [".C", "C.", "CC.", "CCC.", "?"]
    for row in byu_reader:
        orth = row["Word"]
        if row["Transcription"]:
            stressed_transcrip = row["Transcription"]

            transcrip = re.sub(r'\d', "", stressed_transcrip)
            vowel_re = "("+"|".join(cmu_vowels)+")"
            consonants_re = "("+"|".join([cons + " " for cons in cmu_consonants])+")"
            cluster_re = vowel_re + " (" + consonants_re + "+)" + vowel_re
            cluster = re.search(cluster_re, transcrip)
            if cluster:
                cluster = cluster.group(2).split(' ')[:-1]
                # Identify preceding vowel
                if check_stress:
                    vowel_match = re.search('([A-Z]+)(\d) (?='+" ".join(cluster)+')', stressed_transcrip)
                    if vowel_match:
                        vowel_stress = int(vowel_match.group(2))
                        vowel_stress = True if vowel_stress > 0 else False
                        vowel_quality = vowel_match.group(1)
                        lax_vowel = vowel_quality in ["AE", "AH", "AO", "UH", "EH", "IH", "AX"]
                    else:
                        print("Error, no vowel", stressed_transcrip, transcrip, " ".join(cluster))
                        exit()

                # if cluster == ['M', 'S', 'T']:
                #     print(transcrip, cluster)
                # Only look at syllabifications that are possible given this cluster's length
                for code in [code for code in boundary_codes if len(code) <= len(cluster) + 1]:
                    num_string = "# of " + code
                    prop_string = "prop. of " + code
                    if code != "?":
                        num_string = num_string + "*"
                        prop_string = prop_string + "*"
                        boundary_code = re.sub('\.', 'X', code)
                    else:
                        boundary_code = 'X'
                    coda, onset = coda_onset(boundary_code, cluster)
                    #print(cluster, code, coda, onset)
                    num_syllabifications = row[num_string]
                    prop_syllabifcations = row[prop_string]
                    #print(coda, onset, boundary_code, num_syllabifications, prop_syllabifcations)
                    syllabification = MedialSyllabification(transcrip, cluster, coda, onset, boundary_code,
                                                              num_syllabifications, prop_syllabifcations)
                    if check_stress:
                        syllabification.preceding_stress = vowel_stress
                        syllabification.lax_vowel = lax_vowel
                        syllabification.stress_transcription = stressed_transcrip
                    if not separate_words:
                        byu_dict[tuple(cluster)].append(syllabification)
                    else:
                        byu_dict[(orth, tuple(cluster))].append(syllabification)
                        #print(orth, tuple(cluster))
    byu_file.close()
    return byu_dict

#cluster: tuple of string (where each is a CMU consonant symbol)
#syllabifications: list of MedialSyllabification objects
#Combines any MedialSyllabification objects in syllabifications
# that have the same onset and coda (e.g. from different word datapoints)
#   -Sums their raw number of responses
#   -Sums their proportion of responses
#   -Renormalizes each unique MedialSyllabification's proportion of responses
#        using the total from all unique onset+coda combinations
# Returns a list of MedialSyllabification objects, each with a unique onset and coda
def consolidate_words(cluster, syllabifications):
    cluster_list = []
    # Only look at syllabifications that are possible given this cluster's length
    for code in [code for code in BoundaryCode if len(code.name) <= len(cluster) + 1]:
        #print(cluster, code)
        coda, onset = coda_onset(code.name, cluster)
        # if coda == ["?"]:
        #     print("unknown")
        #Gather all syllabifications like this (from all words)
        code_sylls = [syll for syll in syllabifications if syll.coda == list(coda)]
        #print([code_syll.coda for code_syll in code_sylls if code_syll.coda == ["?"]])
        syll_total_prop = sum([float(syll.propResponses) for syll in code_sylls])
        syll_total_num = sum([int(syll.numResponses) for syll in code_sylls])
        total_syll = MedialSyllabification(transcription=None, cluster=cluster, onset=onset, coda=coda,
                                           boundary=code,numResponses=syll_total_num,propResponses=syll_total_prop)
        cluster_list.append(total_syll)
    #Renormalize across all possible syllabifications of the cluster, lumping all the words together
    total_prop = sum([syll.propResponses for syll in cluster_list])
    for syll in cluster_list:
        if total_prop != 0:
            syll.propResponses = syll.propResponses / total_prop
    return cluster_list



if __name__ == "__main__":
    separate_words = True
    fn = "eddington_prop_syllabifications_long.csv" if not separate_words else "eddington_prop_syll_separate.csv"
    phone_types, cmu_consonants = read_cmu_phone_file("cmudict-0.7b.phones.txt")
    cmu_vowels = phone_types["vowel"]
    syllabified_counts = read_byu_transcribed("BYU Syllabification Survey Transcriptions.csv", cmu_vowels, cmu_consonants, separate_words=separate_words)
    #for cluster in syllabified_counts:
           #if cluster == ('M','S','T'):
                #(cluster)
                #for syllabification in syllabified_counts[cluster]:
                    #print(syllabification.coda, syllabification.onset, syllabification.propResponses)

    if not separate_words:
        syllabified_counts = {cluster: consolidate_words(cluster, syllabified_counts[cluster]) for cluster in syllabified_counts}




    output_to_csv(syllabified_counts, separate_words=separate_words, fn=fn)










