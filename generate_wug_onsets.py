import format_corpus
import random
random.seed(1)
#consonants: list of string of ARPABET consonants
#prefix: list of string of ARPABET consonants of length <= n
#n: integer length of desired onset
# Returns a list of [list of string]:
#   all possible lists of string of length n that start with prefix
# Where each member is one of the strings in consonant
# Old: And two identical consonants are never next to each other (ie *C1C2 if C1 = C2)
# Now: And two identical consonants never appear anywhere in the string (no replacement)
def onset_possibilities(n, prefix, consonants):
    if n == len(prefix):
        return [prefix]
    else:
        possibilities = []
        for cons in consonants: #go through each possible consonant extension
            #if len(prefix) == 0 or cons != prefix[len(prefix) - 1]: #Prevent CC duplicates
            if cons not in prefix: #Prevent duplicates anywhere - decrease the number of possibilities
                possibilities += onset_possibilities(n, prefix + [cons], consonants)
        return possibilities

#sonorites: tuple of int representing values on sonority scale
#Returns "Rise", "Fall", "Nonmonotonic rise", "Nonmonotonic fall", "Plateau", or "Other" depending on the sonority values
def classify_profile(sonorities):
    rise = True
    fall = True
    nonmon_rise = True
    nonmon_fall = True
    plateau = True
    previous_level = sonorities[0]
    for ind, level in enumerate(sonorities):
        if ind > 0:
            if level > previous_level:
                fall = False
                nonmon_fall = False
                plateau = False
            elif level < previous_level:
                rise = False
                nonmon_rise = False
                plateau = False
            else:
                rise = False
                fall = False
    if rise:
        return "rise"
    elif fall:
        return "fall"
    elif plateau:
        return "plateau"
    elif nonmon_fall:
        return "nonmonotonic fall"
    elif nonmon_rise:
        return "nonmonotonic rise"
    else:
        return "other"


if __name__ == "__main__":
    unsyll_dir = "unsyllabified"
    syll_dir = "syllabified"
    onsets_dir = "just_onsets"
    word_init_onsets_dir = "just_word_initial_onsets"
    base_folder = "cleaned/"
    #Get English consonants and vowels
    phone_types, consonants = format_input.read_cmu_phone_file("cmudict-0.7b.phones.txt")
    vowels = [vowel+"2" for vowel in phone_types["vowel"]]

    #Make all possible 4-gram combinations of consonants (no geminate) crossed with each possible monophthong
    #(using recursive function)
    possible_onsets = onset_possibilities(2, [], consonants)
    possible_onsets.sort()
    #Combine each possible onset with each possible vowel
    #wugs = [onset + [vowel] for onset in possible_onsets for vowel in vowels]
    #Sample some of the onsets; all ~30,000 is too much
    #possible_onsets = random.sample(possible_onsets, 3000)
    wugs = [onset + ["IY2"] for onset in possible_onsets]

    #Sample some of the wugs; all ~3million combinations is too much :(
    #wugs = random.sample(wugs, 3000)

    #Output wugs
    wug_file = open(base_folder+unsyll_dir+"/sonority_wugs.txt", "w+")
    wug_file_syll = open(base_folder+syll_dir+"/syll_sonority_wugs.txt", "w+")
    for wug in wugs:
        wug_file.write(" ".join(wug) + "\n")
        wug_file_syll.write("+ "+" ".join(wug) + " +" + "\n")
    #Output onset wugs
    onset_only_wugs_i = open(base_folder+word_init_onsets_dir+"/onset_sonority_wugs.txt", "w+")
    onset_only_wugs_m = open(base_folder+onsets_dir+"/onset_sonority_wugs.txt", "w+")
    for onset in possible_onsets:
        onset_only_wugs_i.write(" ".join(onset) + "\n")
        onset_only_wugs_m.write(" ".join(onset) + "\n")
    wug_file.close()
    wug_file_syll.close()
    onset_only_wugs_i.close()
    onset_only_wugs_m.close()

    #Output wug to sonority mapping
    # Define sonority scale (use enums?)
    # TODO: "HH" listed as an aspirate; what should its sonority be? Check literature
    sonority = {"stop": 1, "affricate": 2, "fricative": 3, "aspirate": 3, "nasal": 4, "liquid": 5, "semivowel": 5, "vowel": 6}

    # Invert phone type dictionary
    manner = {}
    for phone_type in phone_types:
        for phone in phone_types[phone_type]:
            manner[phone] = phone_type


    #Sonority profile for each wug onset
    #Dictionary from string to tuple of (tuple of int of sonority levels,
    # string classification of sonority profile)
    profiles = {}
    for onset in possible_onsets:
        sonority_profile = tuple([sonority[manner[phone]] for phone in onset])
        str_onset = " ".join(onset)
        profiles[str_onset] = (sonority_profile, classify_profile(sonority_profile))

    sonority_key_file = open("sonority_profile_key.txt", "w+")
    for onset in profiles:
        sonority_key_file.write(onset + "\t" + str(profiles[onset][0]) + "\t" + str(profiles[onset][1]))
        sonority_key_file.write("\n")




