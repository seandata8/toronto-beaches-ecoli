# Story Outline

## Introduction
- importance of measuring e. coli at beaches
- the two questions we are answering with the data
- let the reader know what's in each section

## Data Section
- where the data comes from and the context (already have this sentence)
- explanation of what columns are in the dataset and how they were measured (explain <=10 and >=1000)
- how the data was cleaned--justify the decisions (two beaches and one point removed), refer to the figure in this section (all-raw-results)
- methods: geomeans were taken for each beach-day where there were at least 4 measurements

## Results
- histograms of beach-days, make points about the difference between the beaches (show beach-day-histogram)
- statistical comparison of beaches with 95% CI (show beach-estimates)
- analysis of consecutive day, show confusion matrix

## Discussion
- summarize data and results briefly
- speculate on why some beaches are worse than others and suggest further analyses of data to test
- point out that the current testing method misses most bad days and puts up unnecessary warning most of the time. discuss ways this could be improved--prediction model based on weather, qPCR for same day testing
