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
#Each row corresponds to a single individual's response
def output_to_csv_onehot(byu_dict, predictions=None,
                  fn = "eddington_prop_syllabifications_long_onehot.csv"):
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
            print(syllabification, syllabification.coda, syllabification.onset)
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
#Each row corresponds to a single individual's response
def output_to_csv_logmodel(byu_dict, stat_model, onset_max,
                  fn = "eddington_prop_syllabifications_multinom_format.csv"):
    fields = ["Cluster", "Word", "Response"] + ["jP_"+code.name for code in BoundaryCode if code.name != 'X'] + ["OnsetMax"]

    output_file = open(fn, "w+", newline='')
    output = csv.DictWriter(output_file, fieldnames=fields)
    output.writeheader()

    for key in byu_dict:
        word = key[0]
        cluster = key[1]
        syllabifications = byu_dict[(word,cluster)]
        for syllabification in syllabifications:
            print(syllabification, syllabification.coda, syllabification.onset)
            if syllabification.coda != None and syllabification.onset != None:
                numResponses = syllabification.numResponses
                response = syllabification.boundary
                for i in range(int(numResponses)):
                    row = { "Cluster": cluster,
                            "Word":word,
                            "Response":response}
                    for code in [code.name for code in BoundaryCode]:
                        if code != 'X':
                            coda, onset = coda_onset(code, cluster)
                            if len(code) <= len(cluster) + 1:
                                row["jP_"+code] = stat_model[(word, cluster)][(coda, onset)]
                            else:
                                row["jP_"+code] = 0
                            if onset_max[(word, cluster)][(coda, onset)] == 1:
                                row["OnsetMax"] = code
                    output.writerow(row)
    output_file.close()
