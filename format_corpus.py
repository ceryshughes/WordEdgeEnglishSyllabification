import re
from collections import defaultdict
import pandas as pd

#file_name: name of file of transcriptions adhering to CMUDict format
# Returns a list of transcriptions(each a list of string) from CMU pronunciation dictionary (in order)
def read_cmu_file(file_name):
    transcriptions = []
    for line in open(file_name):
        line = line.strip('\n')
        if len(line) > 0 and not line.startswith(";;;"):
            line = line.split("  ")
            transcrip = line[1].split(" ")
            transcriptions.append(transcrip)
    return transcriptions

#file_name: name of xls file of transcriptions hand-cleaned from Bruce Hayes
#trimmed: whether to exclude words based on BH's criteria
# get freqs: whether to return a list of transcriptions (False) or a dictionary from transcriptions to frequencies (True)
# Returns a tuple=>int dictionary of transcriptions(each a tuple of string) from CMU pronunciation dictionary
# and their CELEX counts OR a list of transcriptions (each a list of string)
def read_cmu_file_bh(file_name, trimmed = True, get_freqs = False, split_ers = False):
    df = pd.read_excel(file_name, sheet_name="Main (CMU with CELEX > 0)")
    transcript_col = "Corrected and trimmed" if trimmed else "Corrected only"
    freq_col = "CELEX Lemma Frequency"

    if get_freqs:
        #{row# -> {column -> value}}
        rows = df[[transcript_col, "CELEX Lemma Frequency"]].to_dict('index')
        #{tuple of string transcription -> int frequency}
        transcripts = {tuple(values[transcript_col].split(' ')): values[freq_col] for row, values in rows.items()}
    else:
        transcripts = list(df[transcript_col])
        if split_ers:
            transcripts = [re.sub(r'ER([012])', r'UH\1 R', transcrip) for transcrip in transcripts if type(transcrip) == str]
        transcripts = [transcript.split(' ') for transcript in transcripts if type(transcript) == str]
    return transcripts



# file_name: name of CMU phone file
# Returns a dictionary of phone types from CMU dictionary
#   Keys are manners of articulation(string), values are lists of phones(string)
# Returns a set of consonants
def read_cmu_phone_file(file_name):
    phone_types = {}
    consonants = set([])
    phone_file = open(file_name)
    for line in phone_file:
        line = line.strip('\n')
        fields = line.split('\t')
        phone = fields[0]
        manner = fields[1]
        if manner not in phone_types:
            phone_types[fields[1]] = []
        phone_types[manner].append(phone)
        if manner != "vowel":
            consonants.add(phone)
    return phone_types, consonants

# transcripts: a list of pronunciations(each is a list of string)
# vowels: a set of string of phones that are vowels
# remove_exotics: boolean, whether to remove onsets that only appear once
# returns a set of legal onsets(each is a tuple of string)
# if counts=True, returns a dictionary of word-initial onsets to their counts
def get_legal_onsets(transcripts, vowels, remove_exotics = False, counts = False):
    onsets = defaultdict(lambda: 0)
    example_words = {}
    for transcrip in transcripts:
        onset = []
        for phone in transcrip:
            if ''.join([char for char in phone if not char.isdigit()]) in vowels:
                break
            else:
                onset.append(phone)
        onsets[(tuple(onset))] += 1
        if len(onset) == 0:
            print(transcrip)
        if tuple(onset) not in example_words:
            example_words[tuple(onset)] = transcrip
    if "" in onsets:
        onsets.remove("")
        print("Removed empty string")
    if remove_exotics:
        onsets = {onset: freq for onset, freq in onsets.items() if freq > 1}
    if counts:
        # sorted_probs = sorted(onsets.items(),key=lambda pair: pair[1])
        # for onset in sorted_probs:
        #     print(onset[0],onset[1], example_words[onset[0]])
        # exit()
        exit()
        return onsets

    return onsets.keys()




# onsets: a set of legal onsets(each is a tuple of string)
# transcription: a phonetic transcription(a tuple of string)
# consonants: a set of consonants (each is a string)
# remove_exotics: not counting consonant sequences that occur word initially only once for word-medial
# onsets (but still allowing when word initial)
#
# returns syllabified transcription(a string with "+" between syllables)
#
# syllabification is one-one with nuclei(marked with numbers in transcription)
#   and maximizes # of consonants in syllable to the right provided they are legal onsets
def syllabify(onsets, transcription, consonants, remove_exotics = False):
    transcription = " ".join(transcription)
    rev_transcript = transcription[::-1] + " "#reverse; onset maximization RE is easier right-to-left
    # The | operator matches from left-to-right regardless of length (it's not greedy).
    # I want greedy behavior to get onset maximization, so I will just make sure
    # left-to-right is longest-to-shortest (by sorting the onsets based on length)
    #(would be faster to do this before passing onsets in, but cleaner this way and not a big deal)
    onsets = list(onsets)
    onsets.sort(key=len, reverse=True)

    rev_onsets = ["(?:"+ " ".join(onset)[::-1]+")" for onset in onsets]
    rev_cons = ["(?:"+cons[::-1]+")" for cons in consonants] #ARPABET consonants and nuceli >1 symbol


    onset_re = "(?:" + "| ".join(rev_onsets) + ")? " #Using this notation for conjunction because multi-character
    cons_re = "(?:(?:" + "|".join(rev_cons) + ") )*"
    nuc_re = "[0-9][A-Z]+"
    max_onset_syll_re = cons_re + nuc_re + onset_re
    #print(rev_transcript,max_onset_syll_re)
    syllables = re.findall(max_onset_syll_re, rev_transcript)
    #print(syllables)
    if remove_exotics:
        #Slurp up any word-initial consonants that might have been left off if exotic
        first_syll = syllables[len(syllables) - 1]
        len_consumed = len("".join(syllables))
        leftover_cons = rev_transcript[len_consumed:len(rev_transcript)]
        first_syll = first_syll + leftover_cons
        syllables[len(syllables)-1] = first_syll


    #print(syllables)
   # syllables = ["+" + syllable for syllable in syllables]
    syllables = "+ ".join(syllables).strip()
    syllables = "+ "+syllables[::-1]+" +" #De-reverse syllables
    #print(syllables)
    return syllables



# Syllabifies transcriptions in CMU dictionary 0.7b
# Returns syllabified transcriptions(list of string), Counter of syllables
# remove_exotics: only count word initial onsets as legal if they occur more than once
def syllabify_cmu(remove_exotics = False, cleaned = False):
    if not cleaned:
        word_transcripts = read_cmu_file("cmudict-0.7b.txt")
    else:
        word_transcripts = read_cmu_file_bh("CMUDictionaryEditedWithCELEXFrequenciesPublicVersion2.xls")
    phone_types, consonants = read_cmu_phone_file("cmudict-0.7b.phones.txt")
    vowels = phone_types["vowel"]
    onsets = get_legal_onsets(word_transcripts, vowels, remove_exotics)
    syllabified_transcriptions = []

    for transcript in word_transcripts:
        syllables = syllabify(onsets, transcript, consonants, remove_exotics)
        syllabified_transcriptions.append(syllables)
    return syllabified_transcriptions


# syllabified_transcriptions: list of string where the syllables in each string are separated by '+'
# initial_only: True if only word medial onsets shouldn't be included
# Returns a list of transcriptions consisting of the onsets in syllabified_transcriptions
# where an onset is all consonants after a '+' and before a vowel, defined by cmu phone file
def transcribe_onsets_only(syllabified_transcriptions, initial_only):
    phone_types, consonants = read_cmu_phone_file("cmudict-0.7b.phones.txt")
    onsets = []
    cons_re = "|".join(['(' + cons + ' )' for cons in consonants])
    #print(cons_re)
    for transcrip in syllabified_transcriptions:
        transcrip = transcrip.split('+')
        for syll in transcrip:
            #print(syll)
            onset = re.match(' ('+cons_re+')+',syll)
            if onset:
                consonants = onset.group(0)
                consonants = consonants[1:-1] #Remove extra space at beginning/end
                onsets.append(consonants)
                #print(onset.group(0))
            if len(syll) > 0 and initial_only:
                break
    return onsets




def prettyprint_cmu(cleaned = False):
    if not cleaned:
        word_transcripts = read_cmu_file("cmudict-0.7b.txt")
    else:
        word_transcripts = read_cmu_file_bh("CMUDictionaryEditedWithCELEXFrequenciesPublicVersion2.xls")
    word_transcripts = [" ".join(transcript) for transcript in word_transcripts]
    return word_transcripts

def write_output(filename, strings):
    file = open(filename, "w+")
    for string in strings:
        file.write(string+"\n")
    file.close()

if __name__ == "__main__":
    cleaned = True
    syllabified = False
    just_onsets = False
    just_initials = False
    remove_exotics = False #Whether to include rare word initial onsets in syllabification

    # Set up output filename
    removal_label = "_no_exotics" if remove_exotics else ""
    if not syllabified:
        output_label = "unsyllabified"+removal_label+"/unsyllabified_cmu"+removal_label
    elif not just_onsets:
        output_label = "syllabified"+removal_label+"/syllabified_cmu"+removal_label
    elif just_initials:
        output_label = "just_word_initial_onsets"+removal_label+"/just_word_initial_onsets_cmu"+removal_label
    else:
        output_label = "just_onsets"+removal_label+"/just_onsets_cmu"+removal_label

    if cleaned:
        output_label = "cleaned/"+output_label
    output_fn = output_label + ".txt"

    #Format transcriptions transcriptions
    if not syllabified:
        transcriptions = prettyprint_cmu(cleaned=cleaned)
    elif not just_onsets:
        transcriptions = syllabify_cmu(remove_exotics=remove_exotics, cleaned=cleaned)
    else:
        syllabified_transcriptions = syllabify_cmu(remove_exotics=remove_exotics, cleaned=cleaned)
        transcriptions = transcribe_onsets_only(syllabified_transcriptions, initial_only=just_initials)

    write_output(output_fn, transcriptions)
