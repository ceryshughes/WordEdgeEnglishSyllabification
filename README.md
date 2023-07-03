# WordEdgeEnglishSyllabification
This repository contains the code and data files used for a project examining the influence of word-edge consonant clusters on the word-medial syllabification judgement data provided by Eddington et al. (2014). 
The code and data files are still being organized; check back soon for a more intuitive structure and file naming.
A description of the functions, classes, and runtime behavior of each code file is available at https://docs.google.com/document/d/1wFm7EQCfVx9_8FLb1FjftBfLOzzWiXnnRrWk9TEDGNQ/edit?usp=sharing

Short description of code files:


**BYUSyllabification.py**: Defines the class structure for MedialSyllabification objects, which represent a single syllabification of a word and the Eddington et al. response data.


**add_transcriptions_byu.py**: Reads in CMU pronunciation dictionary transcriptions and outputs the transcribed version of Eddington et al.'s syllabification data, which is originally in orthographic format


**read_byu_syllables.py**: Provides functions for reading the transcribed version of Eddington et al.'s data format into MedialSyllabification objects.


**format_corpus.py**: Processes the CMU pronunciation dictionary and predicts syllabifications based on Onset Maximization. Also counts the occurrences of word-initial consonant sequences.


**count_word_edges.py**: Counts the occurrences of word-final consonant sequences 


**BYUFormatOutput.py**: Provides functions for outputting the predictions of various models for Eddington et al.'s data in a csv.


**predict_syllabification_judgements.py**: Computes the predicted syllabifications of Eddington et al.'s data under various models (e.g. word edge statistics).
