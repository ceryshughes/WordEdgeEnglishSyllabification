from count_word_edges import word_final_codas, compute_prob_model2
from read_byu_syllables import read_byu_transcribed, consolidate_words
from BYUSyllabification import BoundaryCode, coda_onset
from BYUFormatOutput import output_to_csv, output_to_csv_onehot, output_to_csv_logmodel
from format_corpus import read_cmu_phone_file, get_legal_onsets, read_cmu_file_bh, syllabify
from add_transcriptions_byu import read_cmu_file
from morpheme_boundaries import morpheme_predictor
import math

#Returns word-initial and word-final consonant cluster counts from Bruce Hayes's version of CMU
# returns two dictionaries, each of the form (tuple of consonant strings) => count number
def get_counts(trimmed=True):
    # Get transcriptions from Bruce Hayes's version of CMU
    transcriptions = read_cmu_file_bh("CMUDictionaryEditedWithCELEXFrequenciesPublicVersion2.xls",trimmed=trimmed)

    #Get consonant and vowel symbols
    phone_types, consonants = read_cmu_phone_file("cmudict-0.7b.phones.txt")
    vowels = phone_types["vowel"]

    #Get word-initial and word-final counts
    onset_counts = get_legal_onsets(transcriptions,vowels, counts=True)
    coda_counts = word_final_codas(transcriptions, consonants)

    return onset_counts, coda_counts

#cluster: tuple of string (consonants)
#onset_dist: dictionary of form (tuple of string) => number, where each tuple of string represents onset consonants
#coda_dist: dictionary of form (tuple of string) => number, where each tuple of string represents onset consonants
#
#returns dictionary of form (tuple of (tuple of string)) => number,
# where the first element of each key is the coda (consonant cluster, tuple of string)
# of a syllabification and the second the onset of the syllabification (consonant cluster, tuple of string)
# and the value is the predicted probability of that cluster under the assumption that they're combined
# independently: the product of the probability of the onset and the probability of the coda
#
# Unseen clusters are assumed to have a probability of 0
#
# If normalize_conditional = True, then normalizes probabilities of all possible coda, onset pairs for this cluster
# so that they sum to 1
# If separate_probs, stores probabilities for onset and coda separately as a (coda, onset, joint) tuple
def predict_sylls_ind(cluster, onset_dist, coda_dist, normalize_conditional = True, separate_probs = False):
    predictions = {}
    #Go through each possible syllabification
    for code in BoundaryCode:
        #print(code)
        coda,onset = coda_onset(code.name, cluster)
        if coda != ["?"]: #Ignore unknown syllabification responses
            coda = tuple(coda)
            onset = tuple(onset)
            # if len(cluster) == 1:
            #     print(onset, coda)
            #     print(onset_dist[onset], coda_dist[coda])
            #     exit()
            # if onset not in onset_dist:
            #     print("Unseen onset", onset)
            # if coda not in coda_dist:
            #     print("Unseen coda", coda)
            coda_prob = coda_dist.get(coda, 0)
            onset_prob = onset_dist.get(onset, 0)
            #Multiply coda and onset probabilities together
            predictions[(coda, onset)] = coda_prob * onset_prob
            #TODO: add option to return these separately as well
            if separate_probs:
                predictions[(coda,onset)] = (coda_prob, onset_prob, coda_prob * onset_prob)
    if normalize_conditional:
        if separate_probs:
            sum_coda = sum([prob[0] for syll, prob in predictions.items()])
            if sum_coda == 0: print("Codas all 0", cluster)
            sum_onset = sum([prob[1] for syll, prob in predictions.items()])
            if sum_onset == 0: print("Onsets all 0", cluster)
            sum_joint = sum([prob[2] for syll, prob in predictions.items()])
            if sum_joint == 0:
                print("Joint probs all 0", cluster)
                print(predictions)
                print(coda_dist.get(('M','Z'),0))
                exit()

            for syllabification in predictions:
                coda_prob, onset_prob, joint_prob = predictions[syllabification]
                print(cluster,syllabification, ":", onset_prob, ":", sum_onset, ":",onset_prob/sum_onset)
                if sum_coda != 0: coda_prob = coda_prob/sum_coda
                if sum_onset != 0: onset_prob = onset_prob/sum_onset
                if sum_joint != 0: joint_prob = joint_prob/sum_joint
                predictions[syllabification] = (coda_prob, onset_prob, joint_prob)

        else:
            sum_predictions = sum([prob for syll, prob in predictions.items()])
            if sum_predictions == 0:
                print("Unseens create no possible syllabification",cluster, predictions)
                #TODO: account for unseens
            else:
                predictions = {syll:prob/sum_predictions for syll, prob in predictions.items()}
    return predictions

#cluster: tuple of string
#legal_onsets: list of attested word-initial onsets
#consonants: list of consonant symbols from CMU
#Translates onset maximization's syllabification prediction into a distribution over boundary codes
#Returns a dictionary from syllabification (pair of tuple) to probability
def onset_maximization_prob(cluster, legal_onsets, consonants):
    #print(cluster, legal_onsets, consonants)
    transcrip = "I0 "+" ".join(cluster) + " I0"
    transcrip = tuple(transcrip.split(" "))
    syllabified = syllabify(set(legal_onsets), transcrip, consonants).split('+')
    syllabified = syllabified[1:-1]
    syllabified[0] = syllabified[0][1:]
    syllabified[1] = syllabified[1][:-1]

    cluster_1 = tuple(syllabified[0].split(" ")[1:-1])
    cluster_2 = tuple(syllabified[1].split(" ")[1:-1])
    distribution= {(cluster_1, cluster_2):1}
    for boundary in BoundaryCode:
        boundary_place = boundary.value
        if boundary_place != len(cluster_1):
            distribution[(cluster[0:boundary_place], cluster[boundary_place:])] = 0

    return distribution

#syllabifications: list of MedialSyllabification objects
#prob_model: dictionary from clusters (tuple of string) to dictionary of (onset, coda) pairs to probability
#computes sum of log probabilities
#If a cluster in syllabifications isn't in prob_model, assumes uniform distribution over syllabifications
def data_log_likelihood(syllabifications,prob_model):
    print("Computing log likelihood")
    total = 0
    print(set([syll.cluster for syll in syllabifications]))
    for syll in syllabifications:
        if syll.coda != ['?']: #Ignore unknown responses
            if syll.cluster in prob_model:
                #Get probability of syllabification under model
                prob = prob_model[syll.cluster][(syll.coda, syll.onset)]
            else:
                print("Cluster not in model", cluster)
                prob = 0.25 #Uniform distribution for unseens
            num = int(syll.numResponses) #Number of people who responded with this syllabification
            #print(syll.cluster, prob, num, prob ** num, math.log(prob)*num)
            total += math.log(prob) * num #Sum log probabilities (one for every response)
    return total

#cluster_probs: dictionary from cluster (tuple of string) to dictionary from
# syllabification (tuple of tuple of string) to probability (float)
# l: number
# alphabet: list of string
def add_l_smooth(cluster_probs,l,alphabet, maxlen=4):
    #clusters = generate_combinations(alphabet, [], maxlen)
    print("Smoothing")
    for cluster in cluster_probs:
        #print(cluster)
        for code in BoundaryCode:
            coda, onset = coda_onset(code.name, cluster)
            if coda != ['?']:
                cluster_probs[cluster][(coda, onset)] = cluster_probs[cluster].get((coda,onset), 0) + l
        #print([cluster_probs[cluster]])
        norm = sum([cluster_probs[cluster][syll] for syll in cluster_probs[cluster]])
        cluster_probs[cluster] = {syll:cluster_probs[cluster][syll]/norm for syll in cluster_probs[cluster]}
        #print(cluster_probs[cluster])

#Generates all possible lists of alphabet that start with prefix and have a length <= maxlen
def generate_combinations(alphabet, prefix, maxlen=4):
    if len(prefix) < maxlen:
        combos = []
        for s in alphabet:
            for i in range(1,maxlen+1):
                combos += generate_combinations(alphabet, prefix+[s], maxlen)
        return combos
    elif len(prefix) == maxlen:
        return [prefix]
    else:
        return []





if __name__ == "__main__":
    separate_words = True
    split_ers = True
    onehot = False
    loglikelihood = False
    multinom = True
    morph_boundaries = True
    split_rows = False
    stress_predictor = True
    separate_probs = True
    bh_trimmed = False
    fn = "eddington_predictions_separate.csv" if separate_words else "eddington_predictions.csv"
    fn = "split_ers_"+fn if split_ers else fn


    #Get onset and coda probability distributions
    onset_counts, coda_counts = get_counts(bh_trimmed)
    onset_dist_unsmoothed = compute_prob_model2(onset_counts, length_smooth=0)
    coda_dist_unsmoothed = compute_prob_model2(coda_counts, length_smooth=0)
    sorted_onsets = sorted(onset_dist_unsmoothed.items(), key=lambda pair: pair[1])
    # for onset in onset_dist_unsmoothed:
    #     print(onset, onset_dist_unsmoothed[onset])
    # exit()
    #print(onset_dist_unsmoothed)

    #Get Eddington clusters
    # Get consonant and vowel symbols
    phone_types, cmu_consonants = read_cmu_phone_file("cmudict-0.7b.phones.txt")
    cmu_vowels = phone_types["vowel"]
    eddington_cluster_syllabs = read_byu_transcribed("BYU Syllabification Survey Transcriptions.csv", cmu_vowels,
                                                     cmu_consonants,
                                                     separate_words=separate_words, check_stress=stress_predictor)
    if not separate_words:
        eddington_cluster_syllabs = {cluster: consolidate_words(cluster, eddington_cluster_syllabs[cluster]) for cluster in eddington_cluster_syllabs}

    predictions = {}
    for cluster in eddington_cluster_syllabs.keys():
        if separate_words:
            word = cluster[0]
            cluster = cluster[1]
        pred = predict_sylls_ind(cluster, onset_dist_unsmoothed, coda_dist_unsmoothed,separate_probs=separate_probs)
        if separate_words:
            predictions[(word, cluster)] = pred
        else:
            predictions[cluster] = pred
    exit()
    #print(predictions)

    #Get max onset probabilities
    onset_max_preds = {}
    word_transcripts = read_cmu_file_bh("CMUDictionaryEditedWithCELEXFrequenciesPublicVersion2.xls", split_ers=split_ers)
    onsets = get_legal_onsets(word_transcripts, cmu_vowels)
    for cluster in eddington_cluster_syllabs.keys():
        if separate_words:
            word = cluster[0]
            cluster = cluster[1]
        pred = onset_maximization_prob(cluster, onsets, cmu_consonants)
        if separate_words:
            onset_max_preds[(word, cluster)] = pred
        else:
            onset_max_preds[cluster] = pred

    #Get morphme predictions
    if morph_boundaries:
        #todo: switch this to Bruce Hayes's CMU by making an orth=> transcription dictionary
        transcrips = read_cmu_file("cmudict-0.7b.txt")
        print("Getting morph boundaries")
        morpheme_preds = morpheme_predictor(transcriptions=transcrips)
        print(morpheme_preds)

    else:
        morpheme_preds = None

    if loglikelihood:
        l = .00000000000001
        print("Edge", [predictions[prediction] for prediction in predictions])

        #Do add-lambda smoothing to onset max and word edge models
        add_l_smooth(predictions,l,cmu_consonants)
        add_l_smooth(onset_max_preds, l, cmu_consonants)

        print("Edge",[predictions[prediction] for prediction in predictions])
        #Remove by-cluster dictionary structure of experimental data
        flat_data = []
        for cluster in eddington_cluster_syllabs:
            flat_data += [syll for syll in eddington_cluster_syllabs[cluster]]

        #Print log likelihood of experimental data under each model
        print("Word edge likelihood:",data_log_likelihood(flat_data, predictions))
        print("Onset max likelihood:",data_log_likelihood(flat_data, onset_max_preds))
    else:
        if onehot:
            output_to_csv_onehot(eddington_cluster_syllabs, {"Simple joint edge model": predictions, "Onset max preds":onset_max_preds})
        if multinom:
            filename = "eddington_prop_syllabifications_multinom_format"
            if not bh_trimmed:
                filename = "bh_untrimmed_" + filename
            if not split_rows:
                filename = filename + "_unsplit"
            if stress_predictor:
                filename = filename + "_stress"
            if separate_probs:
                filename = filename + "_separateprobs"
            filename = filename + ".csv"
            output_to_csv_logmodel(eddington_cluster_syllabs, predictions, onset_max_preds,
                                   morphemes=morpheme_preds, fn=filename, split_rows=split_rows,
                                   stress=stress_predictor,separate_probs=separate_probs
                                   )
        else:
            output_to_csv(eddington_cluster_syllabs, {"Simple joint edge model": predictions, "Onset max preds":onset_max_preds}, separate_words=separate_words, fn=fn)





