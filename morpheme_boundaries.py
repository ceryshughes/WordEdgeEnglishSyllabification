import csv
from BYUSyllabification import *
import add_transcriptions_byu
from format_corpus import read_cmu_phone_file
from read_byu_syllables import get_cluster
from add_transcriptions_byu import read_cmu_file


# Returns a dictionary from orthographic word to the index of the morpheme boundary in the transcription, e.g.
# a+bed
# {"abed":2}
#If there's no morpheme boundary, the value is None
#transcriptions: dictionary from orthography to phonetic transcriptions
def read_morpheme_file(transcriptions):
    annotations_file = open("morpheme_boundary_format.csv")
    affix_file = open("affix_lengths.csv")
    affix_lengths = {}
    morphemes = {}

    affix_reader = csv.DictReader(affix_file)
    for row in affix_reader:
        affix_lengths[row["Affix"]] = int(row["Length"])

    reader = csv.DictReader(annotations_file)
    for row in reader:
        boundary_loc = None
        if row["Word"] in transcriptions:
            if row["Morph1"] and row["Morph2"] and row["Word"] and row["Word"] != "informed":
                morph1 = row["Morph1"]
                morph2 = row["Morph2"]
                if morph1 in affix_lengths:
                    boundary_loc = affix_lengths[morph1]
                elif morph2 in affix_lengths:
                    boundary_loc = len(transcriptions[row["Word"]]) - affix_lengths[morph2]
                elif morph1 in transcriptions:
                    boundary_loc = len(transcriptions[morph1])
                elif morph2 in transcriptions:
                    boundary_loc = len(transcriptions[row["Word"]]) - len(transcriptions[morph2])
                else:
                    print("No morpheme solution for this word", row["Word"])
            morphemes[row["Word"]] = boundary_loc
    return morphemes

#transcriptions: dictionary from orthography to phonetic transcriptions (list of string)
#returns dictionary from (word, cluster) to dictionary of MedialSyllabification probability predictions
def morpheme_predictor(transcriptions):
    predictions = {}
    morphemes = read_morpheme_file(transcriptions)
    phone_types, cmu_consonants = read_cmu_phone_file("cmudict-0.7b.phones.txt")
    cmu_vowels = phone_types["vowel"]
    for word in morphemes:
        transcrip = transcriptions[word]
        cluster = get_cluster(transcrip,cmu_vowels,cmu_consonants)
        if cluster:
            cluster = tuple(cluster)
            predictions[(word,cluster)] = morpheme_predict_word(word, transcrip, cluster, morphemes)
        else:
            print("No cluster", word)
    return predictions

#Returns start and end index of sublist (sl) in list (l)
def find_sub_list(sl,l):
    sll=len(sl)
    for ind in (i for i,e in enumerate(l) if e==sl[0]):
        if l[ind:ind+sll]==sl:
            return ind,ind+sll-1

#Returns dictionary of the form tuple of tuple of string (coda, onset) => probability from a model that
#assigns 1 if the syllabification boundary aligns with a morpheme boudary and 0 to all other syllabifications,
#or a uniform distribution if there are no morpheme boundaries
#orth_word: orthographic form of the word
#morphemes: dictionary from orthographic form of the word to transcription location of boundary
#cluster: transcription of medial cluster
#transcription: transcription of whole word
def morpheme_predict_word(orth_word, transcription, cluster, morphemes):
    dist = {}
    morph_loc = morphemes.get(orth_word, -1)
    print(transcription, cluster, morph_loc)
    morph_loc_in_cluster = morph_loc - find_sub_list(list(cluster), transcription)[0] if morph_loc else None
    print(morph_loc_in_cluster)
    for code in BoundaryCode:
        #print("Orth_word", orth_word,"Code", code.name, "Cluster", cluster)
        coda, onset = coda_onset(code.name,cluster)
        coda = tuple(coda)
        onset = tuple(onset)
        if morph_loc_in_cluster is not None:
            if len(coda) == morph_loc_in_cluster and coda!= ('?',):
                dist[(coda, onset)] = 1
            else:
                dist[(coda, onset)] = 0
        else: #Uniform distribution prediction if no morpheme boundary
            dist[(coda, onset)] = 1.0/(len(BoundaryCode)-1)
            dist[(('?',),('?',))] = 0
            if morph_loc:
                print("Bug?", orth_word, transcription, morph_loc, morph_loc_in_cluster, onset, coda, len(coda))
    return dist

if __name__ == "__main__":
    phone_types, cmu_consonants = read_cmu_phone_file("cmudict-0.7b.phones.txt")
    cmu_vowels = phone_types["vowel"]
    transcriptions = read_cmu_file("cmudict-0.7b.txt")
    #words = word_transcriptions("BYU Syllabification Survey Transcriptions.csv")
    morph_boundaries = read_morpheme_file(transcriptions)
    for word in morph_boundaries:
        loc = morph_boundaries[word]
        transc = transcriptions[word]
        print(word, loc, transc[0:loc] if loc else transc, transc[loc:] if loc else "")

    predictions = morpheme_predictor(transcriptions)
    for pair in predictions:
        print(pair[0], pair[1])
        print(predictions[pair])
        print()