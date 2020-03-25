import glob
import nltk
import pandas as pd

from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords 
from nltk import pos_tag

import spacy
import en_core_web_lg
nlp = en_core_web_lg.load()

from py2neo import *
from itertools import *
from pprint import pprint


class Connect:
    '''Host neo4j to specific account'''
    def __init__(self, uri, user, password):
        self.graph = Graph(uri, auth=(user, password))

    def start(self):
        self.tx = self.graph.begin()
        print('Connected...')
    
    def feed(self, path):
        self.dir = path
        for filename in glob.glob(self.dir):
            with open(filename, 'r') as f:
                file_contents = f.read()
                
    def run(self, *args, **kwargs):
        return self.graph.run(*args, **kwargs)
    
    def end(self):
        self.graph.close()
        print('Disconnected...')
        

class GraphSetup:

    def __init__(self, host):
        self.graph = host
        schema_query = '''
        CALL ga.nlp.createSchema()
        UNION
        CALL ga.nlp.config.setDefaultLanguage('en')
        '''
        self.graph.run(schema_query)
    
    def process(self):
        processor_query = '''
        CALL ga.nlp.processor.addPipeline({textProcessor: 'com.graphaware.nlp.processor.stanford.StanfordTextProcessor', \
        name: 'EN_process', processingSteps: {tokenize: true, ner: true, dependency: true, sentiment: true}, \
        threadNumber: 20})
        UNION
        CALL ga.nlp.processor.pipeline.default('EN_process')
        '''
        self.graph.run(processor_query)
        
        annotate_query = '''
        CALL apoc.periodic.iterate(
        "MATCH (n:News) RETURN n",
        "CALL ga.nlp.annotate({text: n.text, id: id(n)})
        YIELD result MERGE (n)-[:HAS_ANNOTATED_TEXT]->(result)", {batchSize:1, iterateList:true})
        '''
        self.graph.run(annotate_query)
        
    def enrich(self):
        enrich_query = ''' 
        MATCH (n:Tag)
        CALL ga.nlp.enrich.concept({enricher: 'conceptnet5', tag: n, depth:2, admittedRelationships:["IsA","PartOf"]})
        YIELD result
        RETURN result
        '''
        self.graph.run(enrich_query)
    
    def keyword_extract(self):
        step1 = '''
        MATCH (a:AnnotatedText)
        CALL ga.nlp.ml.textRank({annotatedText: a, useDependencies: true})
        YIELD result RETURN result
        '''
        step2 = '''
        CREATE INDEX ON :Keyword(numTerms)
        CREATE INDEX ON :Keyword(value)
        '''
        step3 = '''
        CALL ga.nlp.ml.textRank.postprocess({keywordLabel: "Keyword", method: "subgroups"})
        YIELD result
        RETURN result
        '''
        step4 = '''
        CALL apoc.periodic.iterate(
        'MATCH (n:AnnotatedText) RETURN n',
        'CALL ga.nlp.ml.textRank.postprocess({annotatedText: n, method:"subgroups"}) \
        YIELD result RETURN count(n)',
        {batchSize: 1, iterateList:false})
        '''
        self.graph.run(step1)
        self.graph.run(step2)
        self.graph.run(step3)
        self.graph.run(step4)
    
    def summarize(self):
        summary_query = '''
        MATCH (a:AnnotatedText)
        CALL ga.nlp.ml.textRank.summarize({annotatedText: a}) YIELD result
        RETURN result
        '''
        self.graph.run(summary_query)

# Establish connection
Host = Connect('bolt://localhost:7687','neo4j','gdb')
Host.start()

# Graph creation and processing
GraphSetup.process()

# Call the other class methods for enrichment, keyword extraction, and text summarization