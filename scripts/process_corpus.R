#!/usr/bin/env Rscript
suppressPackageStartupMessages(library("argparse"))

parser <- ArgumentParser()
parser$add_argument("-i", "--indir", help="directory to text files")
parser$add_argument("-o", "--outdir", help="directory to write processed text files")
args <- parser$parse_args()


library('tm')
#library('qdap')
library('topicmodels')

process_text <- function (data, outdir){
  
  #docs <- system.file("texts", data, package = "tm")
  (corpus <- Corpus(DirSource(data), readerControl = list(language = "eng")))
  
  corpus <- tm_map(corpus, stripWhitespace)
  corpus <- tm_map(corpus, tolower)
  corpus <- tm_map(corpus, removeNumbers)
  corpus <- tm_map(corpus, removeWords, stopwords("english"))
  corpus <- tm_map(corpus, stemDocument, language = "english") 
  corpus <- tm_map(corpus, removePunctuation)
  corpus <- tm_map(corpus, removeWords, c('state','pre','will','presid','unit','also','one','now','can','american','agree','first,','part','two','one','follow'))
  writeCorpus(corpus, path = outdir, filenames = NULL)
}

process_text(args$indir, args$outdir)