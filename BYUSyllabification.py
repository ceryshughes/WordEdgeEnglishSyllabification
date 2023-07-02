from enum import Enum

class MedialSyllabification:
    def __init__(self, transcription, cluster, coda, onset, boundary,
                 numResponses, propResponses, preceding_stress = None, stress_transcription = None, lax_vowel=None):
        self.transcription = transcription #List of string
        self.cluster = cluster #List of string
        self.coda = coda  # List of string  - coda of first syllable
        self.onset = onset #List of string - onset of second syllable
        self.boundary = boundary  # BoundaryCode enum
        self.numResponses = numResponses
        self.propResponses = propResponses
        #self.vowel = vowel #String
        #self.syll1 = syll1
        #self.syll2 = syll2

        #TODO: add preceding stress field, optional
        self.preceding_stress = preceding_stress #Optional: None if undefined, True if the vowel preceding
        #the medial cluster is stressed, False if it's unstressed
        self.stress_transcription = stress_transcription #None if preceding_stress is None, a list of string otherwise
        self.lax_vowel = lax_vowel #True iff the vowel preceding the syllable boundary is lax:
        #AE, AH, AO, UH, EH, IH, AX


#Data file codes for (replace . with X) syllable boundary location
class BoundaryCode(Enum):
    XC = 0 #Syllable boundary is at position 0 of the cluster, e.g. (V).CCC(V)
    CX = 1 #Syllable boundary is at position 1 of the cluster, e.g. (V)C.CC(V)
    CCX = 2 #Syllable boundary is at position 2 of the cluster, e.g. (V)CC.C(V)
    CCCX = 3 #Syllable boundary is at position 3 of the cluster, e.g. (V)CCC.(V)
    X = None #Syllable boundary response is 'unknown'/'?'

#Given a BoundaryCode and a cluster(list of string),
# returns coda (list of string) and onset (list of string)
# when cluster is syllabified with the given BoundaryCode
#If the boundarycode is X(unknown), returns ["?"],["?"]
def coda_onset(boundaryCode, cluster):
    #print(boundaryCode)
    #print(BoundaryCode[boundaryCode])
    boundary_place = BoundaryCode[boundaryCode].value
    # print(boundary_place)
    if boundary_place != None:
        coda = cluster[0:boundary_place]
        onset = cluster[boundary_place:]
    else: #Unknown/"?" response
        coda = ["?"]
        onset = ["?"]
    #(boundaryCode, boundary_place, coda, onset)
    return coda, onset