from enum import Enum

class MedialSyllabification:
    def __init__(self, transcription, cluster, coda, onset, boundary, numResponses, propResponses):
        self.transcription = transcription #List of string
        self.cluster = cluster #List of string
        self.coda = coda  # List of string  - coda of first syllable
        self.onset = onset #List of string - onset of second syllable
        #self.vowel = vowel #String
        #self.syll1 = syll1
        #self.syll2 = syll2
        self.boundary = boundary #BoundaryCode enum
        self.numResponses = numResponses
        self.propResponses = propResponses

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