setwd("~/GP2")
library(tidyverse)
library(ggplot2)
install.packages("bayestestR")
install.packages("DescTools")
library(DescTools)
library(bayestestR)
install.packages("moments")
library(moments)

#Install MaxEnt R tool
if (!require(devtools)) {
  install.packages("devtools", repos = "http://cran.us.r-project.org")
}
if (!require(maxent.ot)) {
  devtools::install_github("connormayer/maxent.ot")
}

library(maxent.ot)

####Set up data####
remove_string <- function(vec, str) {
  vec <- vec[vec != str]
  return(vec)
}

#Takes expanded predictors (jP_XC, jP_CX, jP_CCX, MorphXC,etc) and
#returns a new df where they're reduced to one predictor that matches the Output column
reduce_predictors <- function(df){
 result <- df %>%
    mutate(jP = case_when(
      Output == "CX" ~ jP_CX,
      Output == "XC" ~ jP_XC,
      Output == "CCX" ~ jP_CCX,
      Output == "CCCX" ~ jP_CCCX
    ))
 result <- result %>%
   mutate(Morph = case_when(
     Output == "CX" ~ Morph_CX,
     Output == "XC" ~ Morph_XC,
     Output == "CCX" ~ Morph_CCX,
     Output == "CCCX" ~ Morph_CCCX
   ))
 result$OnsetMax <- ifelse(result$OnsetMax != result$Output, 0,1)
 result$Morph <- ifelse(result$Output == "XC" & result$Morph_XC == 1, 1,
                            ifelse(result$Output == "CX" & result$Morph_CX == 1, 1,
                                   ifelse(result$Output == "CCX" & result$Morph_CCX == 1, 1,
                                          ifelse(result$Output == "CCCX" & result$Morph_CCCX == 1, 1, 0))))
 #Remove extra columns
 #TODO: keep stress column
 result <- select(result, -c("jP_CX", "jP_XC", "jP_CCX", "jP_CCCX"))
 result <- select(result, -c("Morph_CX", "Morph_XC", "Morph_CCX", "Morph_CCCX"))
 result
}

#Given tableau (df) with constraints for ViolMorph, ViolOnsetMax, and ViolJP,
#Formatted with Input, Output, and Frequency as first 3 columns
#Fits multiple MaxEnt models of syllabification data to measure
#contribution of each constraint
#Returns list of models:
#1: joint prob model only
#2: max onset only
#3: morph boundary and stress only
#4: morph boundary and stress and max onset
#5: morph boundary and stress and joint prob
#6: morph boundary, stress, max onset, and joint prob
compare_edge_max_morph <- function(df){
  #Add stress to models (like morpheme boundary was in all models)
  df_joint <- select(df, Input, Output, Frequency, ViolJP)
  df_max <- select(df, Input, Output, Frequency, ViolOnsetMax)
  df_morph <- select(df, Input, Output, Frequency, ViolMorph, ViolStress)
  df_morph_max <- select(df, Input, Output, Frequency, ViolMorph, ViolStress, ViolOnsetMax) 
  df_morph_joint <- select(df, Input, Output, Frequency, ViolMorph,ViolStress, ViolJP) 
  df_morph_max_joint <- select(df, Input, Output, Frequency, ViolMorph, ViolStress, ViolOnsetMax, ViolJP)
  df_morph_max_ons <- select(df, Input, Output, Frequency, ViolMorph, ViolStress, ViolOnsetMax,ViolOnsetP)
  df_morph_max_coda <- select(df, Input, Output, Frequency, ViolMorph, ViolStress, ViolOnsetMax,ViolCodaP)
  df_morph_max_ons_coda <- select(df, Input, Output, Frequency, ViolMorph, ViolStress, ViolOnsetMax,ViolOnsetP, ViolCodaP)
  df_morph_max_ons_coda_joint <- select(df, Input, Output, Frequency, ViolMorph, ViolStress, ViolOnsetMax,ViolOnsetP, ViolCodaP, ViolJP)
  df_morph_max_ons
  df_ons <- select(df, Input, Output, Frequency,ViolOnsetP)
  optimize_weights(df_ons)
  #Usually want to compare subsets and supersets
  #joint <- optimize_weights(df_joint)
  #max <- optimize_weights(df_max)
  #morph <- optimize_weights(df_morph)
  #morph_max <- optimize_weights(df_morph_max)
  #morph_joint <- optimize_weights(df_morph_joint)
  #morph_max_joint <- optimize_weights(df_morph_max_joint)
  #morph_max_ons <- optimize_weights(df_morph_max_ons)
  #morph_max_coda <- optimize_weights(df_morph_max_coda)
  #morph_max_ons_coda <- optimize_weights(df_morph_max_ons_coda)
  #morph_max_ons_coda_joint <- optimize_weights(df_morph_max_ons_coda_joint)
  #comparison <- compare_models(joint, max, morph, morph_max, morph_joint, morph_max_joint, 
  #                             morph_max_ons, morph_max_coda, morph_max_ons_coda,
  #                             morph_max_ons_coda_joint,
  #                             method="bic")
  #list(comparison,joint,max,morph,morph_max, morph_joint,morph_max_joint,
  #     morph_max_ons, morph_max_coda,morph_max_ons_coda,morph_max_ons_coda_joint)
  
}


#All data together
judgements <- read.csv("SyllablePhonotactics/bh_untrimmed_eddington_prop_syllabifications_multinom_format_unsplit_stress_separateprobs.csv")

#Coding preceding stress as a violation:
#If preceding stress and no coda(so .C),violation
#Because the theory is preceding stress wants to have a coda
#TODO: should also take into account lax vs tense vowel?
judgements <- judgements %>% mutate(ViolStress = ifelse(Response=="XC" & P_stress=="True" & P_lax=="True",1,0))
judgements <- select(judgements, -c(P_stress, P_lax))


#Filter out unknown responses
judgements <- judgements %>% filter(Response!="X")
#TODO: maybe don't filter out unknowns? That's data about how uncertain people are

#Convert column names to MaxEnt tool format
judgements <- rename(judgements, Output=Response)
judgements <- rename(judgements, Input=Word) #input as word or cluster?
#Condense predictors
judgements <- reduce_predictors(judgements)

#Make OnsetMax, Morph, and jP be constraint violation(bigger = worse)
judgements$OnsetMax <- ifelse(judgements$OnsetMax == 1, 0,1)
judgements$Morph <- ifelse(judgements$Morph == 0, 1, 0)
judgements$jP <- 1 - judgements$jP #Numbers are violations, so need bigger probability = less violating
#Do we want this to be linear or log linear? Bigger differences by .5? Loose choice, scale matters
judgements$codaP <- 1 - judgements$codaP
judgements$onsetP <- 1 - judgements$onsetP

judgements <- rename(judgements, ViolOnsetMax = OnsetMax)
judgements <- rename(judgements, ViolMorph = Morph)
judgements <-rename(judgements, ViolJP = jP)
judgements <-rename(judgements, ViolCodaP = codaP)
judgements <-rename(judgements, ViolOnsetP = onsetP)




#Split data up by length
length(str_split(judgements$Cluster, ","))
judgements <- judgements %>% mutate(split = str_split(Cluster, ",")) #Count length of clusters (with string processing)
judgements$split <- lapply(judgements$split, remove_string, str = ")")
judgements <- judgements %>% mutate(len = sapply(split, length))
judgements_lengths <- split(judgements, f=judgements$len)

#Save dataframe for each length, ignoring 'Cluster' column for analysis
col_names <- c('Input', 'Output', 'Frequency','ViolJP','ViolOnsetMax', 'ViolMorph', 'ViolStress','ViolOnsetP','ViolCodaP')
j_1 <- judgements_lengths$'1'[,col_names]
j_2 <- judgements_lengths$'2'[,col_names]
j_3 <- judgements_lengths$'3'[,col_names]
j_4 <- judgements_lengths$'4'[,col_names]

#Try it out with the sample dataframe
sample <- read.csv("sample_data_frame.csv")
sample_model <- optimize_weights(sample)
summary(sample_model)




#j_1 <- select(j_1, -c("Cluster")) #Remove extra column
#Compress individual responses into frequency counts
#j_1 <- j_1 %>%
#  group_by_all() %>%
#  summarize(Frequency = n()) %>%
#  ungroup()

#Just focus on length 1 (j_1) for a moment
j_1_limited <- select(j_1, Input, Output, Frequency, ViolMorph, ViolOnsetMax)

simple_model <- optimize_weights(j_1_limited)
simple_model$weights
complex_model <- optimize_weights(j_1)
complex_model$weights
compare_models(simple_model, complex_model, method="bic")

#Do analysis for rest of lengths
#analysis[[1]] is model comparison with BIC
#analysis[[2]] is Joint Prob only-model, analysis[[3]] is OM-only, + so on
#up to analysis[[7]]
analysis_len1 <- compare_edge_max_morph(j_1)
analysis_len2 <-compare_edge_max_morph(j_2)
analysis_len3 <-compare_edge_max_morph(j_3)
analysis_len4 <-compare_edge_max_morph(j_4)
input <- judgements[,c("Input","Output","Frequency","ViolJP")]
just_jp <- optimize_weights(judgements[,c("Input","Output","Frequency","ViolJP")])
analysis_combined <- compare_edge_max_morph(judgements[,col_names])

#Compute Bayes factors
all_predictors_bic <- analysis_combined[[1]][1,]$bic
morph_max_bic <- analysis_combined[[1]][2,]$bic
morph_jp_bic <-analysis_combined[[1]][3,]$bic

#Bayes factor for with max vs without
bayestestR::bic_to_bf(c(morph_jp_bic, all_predictors_bic),morph_jp_bic)
bayestestR::bic_to_bf(c(morph_max_bic, all_predictors_bic),morph_max_bic)



#Make predictions for individual lexical items
jp_max_morph <- predict_probabilities(select(judgements[,col_names], 
                                                  Input, Output, Frequency,
                                                  ViolMorph, ViolOnsetMax, ViolJP), 
                                           analysis_combined[[7]]$weights)

jp_morph <- predict_probabilities(select(judgements[,col_names],
                                         Input, Output, Frequency,
                                         ViolMorph,ViolJP), 
                                  analysis_combined[[6]]$weights)

max_morph <- predict_probabilities(select(judgements[,col_names],
                                          Input, Output, Frequency,
                                          ViolMorph,ViolOnsetMax),
                                   analysis_combined[[5]]$weights)
jp_max_morph_pred <- jp_max_morph$predictions
jp_morph_pred <- jp_morph$predictions
max_morph_pred <- max_morph$predictions

#Make combined dataframe to output error of max_morph, jp_max_morph, and jp_morph
#to a csv file
temp_jp_max_morph <- rename(jp_max_morph_pred, Error_combined=Error)
temp_max_morph <- rename(max_morph_pred, Error_max=Error)
temp_jp_morph <- rename(jp_morph_pred, Error_jp=Error)

temp_jp_max_morph <- rename(temp_jp_max_morph, Pred_combined=Predicted)
temp_max_morph <- rename(temp_max_morph, Predicted_max=Predicted)
temp_jp_morph <- rename(temp_jp_morph, Predicted_jp=Predicted)
combined_preds <-merge(temp_jp_max_morph, temp_max_morph, by=c("Input", "Output","Observed","Freq","ViolMorph","ViolOnsetMax"),
                        suffixes=c("_combined", "_max"))
combined_preds <-merge(combined_preds, temp_jp_morph, by=c("Input", "Output","Observed","Freq","ViolMorph","ViolJP"),
                       )
write.csv(combined_preds, "maxent_model_predictions.csv")

#Plot predictions vs observed
pred_observed <- ggplot(jp_max_morph_pred, aes(Predicted,Observed,color=ViolJP)) + geom_point(alpha=0.07)
pred_observed + ggtitle("Model Predictions With All Data and Predictors")
#Split by onset max and morpheme boundary
pred_observed <- pred_observed + facet_grid(vars(ViolOnsetMax), vars(ViolMorph), labeller=label_both)

#Plot predictions with jP vs without
jp_pred_change <- ggplot(combined_preds, aes(Predicted_max, Pred_combined, color=ViolJP)) + geom_point()
jp_pred_change <- jp_pred_change + facet_grid(vars(ViolOnsetMax), vars(ViolMorph), labeller = label_both)
jp_pred_change

#ViolJP vs predictions vs observed for different onset max values
ggplot(combined_preds, aes(ViolJP,Pred_combined,color=Observed)) + geom_point() + facet_grid(vars(ViolOnsetMax), vars(ViolMorph), labeller = label_both)

#Do the same for error
ggplot(combined_preds, aes(ViolJP,Error_combined,color=Observed)) + geom_point() + facet_grid(vars(ViolOnsetMax), vars(ViolMorph), labeller = label_both)
#Error for model without JP vs JP
ggplot(combined_preds, aes(ViolJP,Error_max,color=Observed)) + geom_point() + facet_grid(vars(ViolOnsetMax), vars(ViolMorph), labeller = label_both)
#Error for model without OnsetMax vs Onset Max
ggplot(combined_preds, aes(as.factor(ViolOnsetMax),Error_jp)) + geom_violin() + facet_grid(vars(ViolMorph), labeller = label_both)

#Plot predictions with OnsetMax vs without
max_pred_change <- ggplot(combined_preds, aes(Predicted_jp, Pred_combined, color=ViolOnsetMax)) + geom_point()
max_pred_change <- max_pred_change + facet_wrap(vars(ViolMorph))
max_pred_change

#Plot observed responses for high vs low JP
combined_preds$highJP <- ifelse(combined_preds$ViolJP < 0.5,1,0)
ggplot(combined_preds, aes(Freq)) + geom_histogram() +
  facet_grid(vars(ViolOnsetMax), vars(highJP),labeller = label_both)


#Compute predicted vs observed Somers D correlations for each model

#OnsetMax+Morph
SomersDelta(max_morph_pred$Predicted, max_morph_pred$Observed)

#JP+Morph
SomersDelta(jp_morph_pred$Predicted, jp_morph_pred$Observed)


#Full model
SomersDelta(jp_max_morph_pred$Predicted, jp_max_morph_pred$Observed)


##Reorganizing tibbles

#Split combined predictions by length for visualization
judgements_select <- judgements %>% select(Input, Cluster, len)
combined_pred_lens <- left_join(combined_preds, judgements_select, by = "Input")

#Get a tibble with just the highest probability syllabification per word
grouped_tibble <- combined_pred_lens %>% group_by(Input)
max_jp_tibble <- grouped_tibble %>% slice(which.min(ViolJP))
min_jp_tibble <- grouped_tibble %>% slice(which.max(ViolJP))
min_jp_tibble$BestJP <- 1
max_jp_tibble$BestJP <- 0
min_max_jp_tibble <- bind_rows(min_jp_tibble, max_jp_tibble)

#Get a tibble with one candidate removed per word: XC (all lengths have it)
#(to remove redundancy in calculating Somers' D)
non_redundant <- combined_pred_lens %>% filter(Output != "XC")

#Somers' D attempt 2: removed redundancy
SomersDelta(non_redundant$Predicted_max, non_redundant$Observed)
SomersDelta(non_redundant$Predicted_jp, non_redundant$Observed)#Doesn't terminate
SomersDelta(non_redundant$Pred_combined, non_redundant$Observed)#Doesn't terminate

#Response histograms for best vs worst JP candidate for given MaxEnt violation
ggplot(min_max_jp_tibble, aes(Freq)) + geom_histogram() +
  facet_grid(vars(ViolOnsetMax), vars(BestJP),labeller = label_both)



#Plot frequency vs violJP for clusters of length 2 and 3
len2preds <- combined_pred_lens %>% filter(len == 2) %>% distinct()
len3preds <- combined_pred_lens %>% filter(len == 3)
ggplot(len2preds, aes(ViolJP, Freq)) + geom_point() + facet_grid(vars(Output))



#Overall distribution of joint prob violations across candidates
ggplot(len3preds, aes(ViolJP)) + geom_histogram(bins=100)+ facet_grid(vars(Output))
ggplot(len2preds, aes(ViolJP)) + geom_histogram(bins=100)+ facet_grid(vars(Output))


#Frequency of the highest-JP candidate for each word vs
#the difference between the highest JP and lowest JP for that
#word
#For clusters of length 2
len2preds_g <- len2preds %>% 
  group_by(Input) %>%
  mutate(diff_prob = Entropy(ViolJP))
  


len2_diff <- len2preds_g %>%
  filter(ViolJP == max(ViolJP)) %>%
  distinct()
ggplot(len2_diff, aes(1 - ViolJP, Freq)) + geom_point()+ facet_grid(vars(Output))
ggplot(len2_diff, aes(diff_prob, Freq)) + geom_point()+ facet_grid(vars(Output), vars(ViolOnsetMax))

#Frequency difference between the highest JP candidate and lowest JP candidate
prob_freq_diffs <- len2preds %>%
  group_by(Input) %>%
  filter(ViolJP == max(ViolJP) | ViolJP == min(ViolJP)) %>%
  summarize(Output = Output[ViolJP == min(ViolJP)],
            ViolOnsetMax = ViolOnsetMax[ViolJP == min(ViolJP)],
            max_prob = nth(ViolJP,1),
            min_prob = min(ViolJP),
            prob_diff = max_prob-min_prob,
            min_freq = Freq[ViolJP == min(ViolJP)],
            max_freq = Freq[ViolJP == nth(ViolJP,1)],
            diff_freq = Freq[ViolJP == min(ViolJP)] - 
              Freq[ViolJP == nth(ViolJP,1)]) %>%
  ungroup() %>%
  arrange(Input)

ggplot(prob_freq_diffs, aes(x=prob_diff, y=diff_freq)) + geom_point() + facet_grid(vars(ViolOnsetMax))
ggplot(len2preds, aes(x=ViolJP, y=Freq)) + geom_point() + facet_grid(vars(ViolOnsetMax))
#Want to show: when you have a high ViolJP relative to the other candidates,
#you tend to have a higher frequency than the other candidates


#Compute variance over probabilities for each candidate type
#for clusters of length 2
len2preds %>% group_by(Output) %>% summarize(Variance = var(ViolJP))
#OK, CX has the highest variance, 0.0813

#Plot model probability vs human frequency for the candidate type with the most variance
cx_tibble <- len3preds %>% filter(Output == "CX")
cx_plot <- ggplot(cx_tibble, aes(ViolJP, Observed)) + geom_point(alpha=0.07)
cx_plot + stat_smooth(method = "lm",
                    geom = "smooth") 
om_split <- cx_plot + facet_grid(vars(ViolOnsetMax), labeller = label_both)+ 
  stat_smooth(method = "lm", geom = "smooth")
#Add r^2 values
cx_lm <- lm(Observed ~ ViolJP, data=cx_tibble)
unsplit_r2 <- summary(cx_lm)$r.squared
cx_plot + stat_smooth(method = "lm",
                      geom = "smooth") +
  annotate("text",label=paste("R^2=",unsplit_r2),x=0.23, y=0.15)
#Split by onset max violation
cx_lm_onsetmax <- lm(Observed ~ ViolJP, data=cx_tibble %>% filter(ViolOnsetMax == 0))
cx_lm_nononsetmax <- lm(Observed ~ ViolJP, data=cx_tibble %>% filter(ViolOnsetMax == 1))
onsetmax_r2 <- summary(cx_lm_onsetmax)$r.squared
nononsetmax_r2 <- summary(cx_lm_nononsetmax)$r.squared
om_text <- data.frame(ViolJP = 0.25,Observed = 0.25,lab = paste("R^2=",onsetmax_r2),
                       ViolOnsetMax = factor(0,levels = c("0","1")))
nom_text <- data.frame(ViolJP = 0.25,Observed = 0.15,lab = paste("R^2=",nononsetmax_r2),
                      ViolOnsetMax = factor(1,levels = c("0","1")))

om_split <- om_split + geom_text(data=om_text, label=paste("R^2=",onsetmax_r2))
om_split
om_split <- om_split + geom_text(data=nom_text, label=paste("R^2=",nononsetmax_r2))
om_split + ggtitle("Word-Edge Probabilities for C.CC Syllabifications") + theme_bw()

#Repeat for length 2
#Plot model probability vs human frequency for the candidate type with the most variance
cx_tibble <- len2preds %>% filter(Output == "CX")
cx_plot <- ggplot(cx_tibble, aes(ViolJP, Observed)) + geom_point(alpha=0.07)
cx_plot + stat_smooth(method = "lm",
                      geom = "smooth") 
om_split <- cx_plot + facet_grid(vars(ViolOnsetMax), labeller = label_both)+ 
  stat_smooth(method = "lm", geom = "smooth")
#Add r^2 values
cx_lm <- lm(Observed ~ ViolJP, data=cx_tibble)
unsplit_r2 <- summary(cx_lm)$r.squared
cx_plot + stat_smooth(method = "lm",
                      geom = "smooth") +
  annotate("text",label=paste("R^2=",unsplit_r2),x=0.23, y=0.15)
#Split by onset max violation
cx_lm_onsetmax <- lm(Observed ~ ViolJP, data=cx_tibble %>% filter(ViolOnsetMax == 0))
cx_lm_nononsetmax <- lm(Observed ~ ViolJP, data=cx_tibble %>% filter(ViolOnsetMax == 1))
onsetmax_r2 <- summary(cx_lm_onsetmax)$r.squared
nononsetmax_r2 <- summary(cx_lm_nononsetmax)$r.squared
om_text <- data.frame(ViolJP = 0.25,Observed = 0.25,lab = paste("R^2=",onsetmax_r2),
                      ViolOnsetMax = factor(0,levels = c("0","1")))
nom_text <- data.frame(ViolJP = 0.25,Observed = 0.15,lab = paste("R^2=",nononsetmax_r2),
                       ViolOnsetMax = factor(1,levels = c("0","1")))

om_split <- om_split + geom_text(data=om_text, label=paste("R^2=",onsetmax_r2))
om_split
om_split <- om_split + geom_text(data=nom_text, label=paste("R^2=",nononsetmax_r2))
om_split + ggtitle("Word-Edge Probabilities for C.C Syllabifications") + theme_bw()



