import re
from collections import defaultdict

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
def get_legal_onsets(transcripts, vowels, remove_exotics = False):
    onsets = defaultdict(lambda: 0)
    for transcrip in transcripts:
        onset = []
        for phone in transcrip:
            if ''.join([char for char in phone if not char.isdigit()]) in vowels:
                break
            else:
                onset.append(phone)
        onsets[(tuple(onset))] += 1
    if "" in onsets:
        onsets.remove("")
        print("Removed empty string")
    if remove_exotics:
        onsets = {onset: freq for onset, freq in onsets.items() if freq > 1}
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
def syllabify_cmu(remove_exotics = False):
    word_transcripts = read_cmu_file("cmudict-0.7b.txt")
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




def prettyprint_cmu():
    word_transcripts = read_cmu_file("cmudict-0.7b.txt")
    word_transcripts = [" ".join(transcript) for transcript in word_transcripts]
    return word_transcripts

def write_output(filename, strings):
    file = open(filename, "w+")
    for string in strings:
        file.write(string+"\n")
    file.close()

if __name__ == "__main__":
    syllabified = True
    just_onsets = True
    just_initials = True
    remove_exotics = True #Whether to include rare word initial onsets in syllabification

    if not syllabified:
        output_fn = "unsyllabified_cmu.txt"
        plain_transcriptions = prettyprint_cmu()
        write_output(output_fn, plain_transcriptions)
    elif not just_onsets:
        label_str = "_no_exotics" if remove_exotics else ""
        output_fn = "syllabified_cmu_max_onset"+label_str+".txt"
        syllabified_transcriptions = syllabify_cmu(remove_exotics=remove_exotics)
        write_output(output_fn, syllabified_transcriptions)
    elif just_initials:
        label_str = "_no_exotics" if remove_exotics else ""
        output_fn = "just_word_initial_onsets_cmu"+label_str+".txt"
        syllabified_transcriptions = syllabify_cmu(remove_exotics=remove_exotics)
        word_init_onsets = transcribe_onsets_only(syllabified_transcriptions, initial_only=True)
        write_output(output_fn, word_init_onsets)
    else:
        label_str = "_no_exotics" if remove_exotics else ""
        output_fn = "just_onsets_cmu"+label_str+".txt"
        syllabified_transcriptions = syllabify_cmu(remove_exotics=remove_exotics)
        onsets = transcribe_onsets_only(syllabified_transcriptions, initial_only=False)
        write_output(output_fn, onsets)

