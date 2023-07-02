import csv
from BYUSyllabification import *


#Given a dictionary of the form cluster (tuple of string) => list of MedialSyllabification objects
#Outputs a CSV with the format:
#Cluster1
#''''Syllabification1''''Prop. Responses
#''''Syllabification2''''Prop. Responses
#''''Syllabification3'''Prop.Responses...
#Cluster2
#''''Syllabification1''''Prop. Responses
#''''Syllabification2''''Prop. Responses
#''''Syllabification3'''Prop.Responses...
#Where each syllabification is defined by the coda and onset, separated by '.'
#predictions: predictions of probability models. a dictionary from model name (string) to a dictionary from cluster (tuple of string) to dictionaries of syllabification (tuple of tuple of string)
# to predicted value (e.g. number)
#if predictions is defined, also outputs a column with predicted values
#if separate_words is True, has an additional column with the word
#and byu_dict's keys must be tuples of the form (word, cluster)
#If raw_num, outputs number of responses instead of proportion of responses

def output_to_csv(byu_dict, predictions=None, separate_words = False,
                  raw_num = False,
                  fn = "eddington_prop_syllabifications_long.csv" ):
    #byu_dict = {cluster: consolidate_words(cluster, byu_dict[cluster]) for cluster in byu_dict}
    fields = ["Cluster", "Syllabification"]
    if raw_num:
        fields = fields + ["Num Responses"]
    else:
        fields = fields + ["Prop Responses"]
    if separate_words:
        fields = ["Word"] + fields

    if predictions:
        fields += predictions.keys()
    output_file = open(fn, "w+", newline='')
    output = csv.DictWriter(output_file, fieldnames=fields)
    output.writeheader()
    for cluster in byu_dict:
        row = {}
        if separate_words:
            #print("key:",cluster)
            word = cluster[0]
            cluster = cluster[1]
            row["Word"] = word
            #print(word, cluster)
        row["Cluster"] = " ".join(cluster)
        output.writerow(row)
        syllabifications = byu_dict[cluster] if not separate_words else byu_dict[(word, cluster)]
        for syllabification in syllabifications:
            #print(syllabification, syllabification.coda, syllabification.onset)
            row = {}
            if syllabification.coda != None and syllabification.onset != None:
                str_syll = " ".join(syllabification.coda) + "." + " ".join(syllabification.onset)
                row["Syllabification"] = str_syll
                if raw_num:
                    row["Num Responses"] = syllabification.numResponses
                else:
                    row["Prop Responses"] = syllabification.propResponses
                if predictions and tuple(syllabification.coda) != tuple("?"):
                    onset = tuple(syllabification.onset)
                    coda = tuple(syllabification.coda)
                    for model in predictions:
                        if not separate_words:
                            pred = predictions[model][cluster][(coda, onset)]
                        else:
                            pred = predictions[model][(word, cluster)][(coda, onset)]
                        row[model] = pred




    output_file.close()

#byu_dict: (word string, cluster tuple of string) => list of MedialSyllabification objects
#Also has an additional column for choice, in case onehot isn't wanted
#If split_rows, each row corresponds to a single individual's response
def output_to_csv_onehot(byu_dict, predictions=None,
                  fn = "eddington_prop_syllabifications_long_onehot.csv", split_rows=True):
    fields = ["Cluster", "Word", "Response"] + [code.name for code in BoundaryCode]
    if predictions:
        fields += predictions.keys()

    output_file = open(fn, "w+", newline='')
    output = csv.DictWriter(output_file, fieldnames=fields)
    output.writeheader()

    for key in byu_dict:
        word = key[0]
        cluster = key[1]
        syllabifications = byu_dict[(word,cluster)]
        for syllabification in syllabifications:
            #print(syllabification, syllabification.coda, syllabification.onset)
            if syllabification.coda != None and syllabification.onset != None:
                numResponses = syllabification.numResponses
                response = syllabification.boundary
                for i in range(int(numResponses)):
                    row = { "Cluster": cluster,
                            "Word":word,
                            "Response":response}
                    for code in [code.name for code in BoundaryCode]:
                        row[code] = 1 if code == response else 0
                    if predictions and tuple(syllabification.coda) != tuple("?"):
                        onset = tuple(syllabification.onset)
                        coda = tuple(syllabification.coda)
                        for model in predictions:
                            pred = predictions[model][(word, cluster)][(coda, onset)]
                            row[model] = pred
                    output.writerow(row)
    output_file.close()


#byu_dict: (word string, cluster tuple of string) => list of MedialSyllabification objects
#Also has an additional column for choice, in case onehot isn't wanted
#If split_rows, each row corresponds to a single individual's response
#Otherwise, each row has a Frequency column containing the number of responses
#morphemes (optional): dictionary from (word, cluster) to dictionary from (coda, onset) to boolean identifying
#whether there's a morpheme boundary there
#if morphemes is defined, includes morpheme columns
# if stress is True, then the MedialSyllabification objects in byu_dict must have a non-None preceding_stres
#   field; an additional column is added to the csv for preceding stress and whether the preceding vowel is lax
# if separate_probs, outputs additional columns for onset and coda probabilities; stat_model must have (coda, onset, joint)
# probability tuple
def output_to_csv_logmodel(byu_dict, stat_model, onset_max, morphemes = None,
                  fn = "eddington_prop_syllabifications_multinom_format.csv", split_rows = True, stress=False,
                           separate_probs=False):
    fields = ["Cluster", "Word", "Response"] + ["jP_"+code.name for code in BoundaryCode if code.name != 'X'] + ["OnsetMax"]
    print("Outputting")
    if morphemes:
        print("Outputting morphemes")
        fields = fields + ["Morph_"+code.name for code in BoundaryCode if code.name != 'X']
    if not split_rows:
        fields.append("Frequency")
    if stress:
        fields.append("P_stress")
        fields.append("P_lax")
    if separate_probs:
        fields += ["codaP", "onsetP"]
    #TODO: add coda and onset prob separate fields


    output_file = open(fn, "w+", newline='')
    output = csv.DictWriter(output_file, fieldnames=fields)
    output.writeheader()

    for key in byu_dict:
        word = key[0]
        cluster = key[1]
        syllabifications = byu_dict[(word,cluster)]
        for syllabification in syllabifications:
            #print(syllabification, syllabification.coda, syllabification.onset)
            if syllabification.coda != None and syllabification.onset != None:
                numResponses = syllabification.numResponses
                response = syllabification.boundary
                row = { "Cluster": cluster,
                            "Word":word,
                            "Response":response}
                if stress:
                    row["P_stress"] = syllabification.preceding_stress
                    row["P_lax"] = syllabification.lax_vowel
                if separate_probs and response != "X":
                    #print(response)
                    syll_coda, syll_onset = tuple(syllabification.coda), tuple(syllabification.onset)
                    coda_prob, onset_prob, joint_prob = stat_model[(word,cluster)][(syll_coda,syll_onset)]
                    row["codaP"] = coda_prob
                    row["onsetP"] = onset_prob

                for code in [code.name for code in BoundaryCode]:
                    if code != 'X':
                        coda, onset = coda_onset(code, cluster)
                        if morphemes:
                            if (word, cluster) in morphemes:
                                if word == 'whitish':
                                    print(word, cluster, coda, onset, morphemes[(word, cluster)][
                                    (coda, onset)])
                                row["Morph_" + code] = morphemes[(word, cluster)][
                                    (coda, onset)]  # Todo: fix this to make sense for different lengths
                            else:
                                #print("Missing morpheme annotation", word)
                                row["Morph_" + code] = 0.25

                        if len(code) <= len(cluster) + 1:
                            if separate_probs:
                                row["jP_"+code] = stat_model[(word,cluster)][(coda,onset)][2]
                            else:
                                row["jP_"+code] = stat_model[(word, cluster)][(coda, onset)]

                            # TODO: add separate onset and coda probability fields
                        else:
                            row["jP_"+code] = 0
                            row["Morph_"+code] = 0
                            # TODO: add separate onset and coda probability field


                        if onset_max[(word, cluster)][(coda, onset)] == 1:
                            row["OnsetMax"] = code
                if split_rows:
                    for i in range(int(numResponses)):
                        output.writerow(row)
                else:
                    row["Frequency"] = numResponses
                    output.writerow(row)
    output_file.close()
