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


class QA:
    
    def __init__(self, host, question):
        '''Tokenize, label, and set NER parameters for the input question'''
        self.graph = host
        
        question_tokenized = word_tokenize(question)
        stop_words = set(stopwords.words("english", "do")) 
        filtered_question = [w for w in question_tokenized if not w in stop_words]
        filtered_question = []
        for w in question_tokenized:
            if w not in stop_words:
                filtered_question.append(w)
                
        doc = nlp(question)
        ner = [(X.text, X.label_) for X in doc.ents]
        self.tags = pos_tag(filtered_question)
        groups = groupby(self.tags, key=lambda x: x[1])
        names_tagged = [[w for w,_ in words] for tag, words in groups if tag=="NNP"]
        names = [" ".join(name) for name in names_tagged if len(name)>=2]
        
        if len(ner) == 1:
            if (ner[0][1] == "GPE") or (ner[0][1] == "LOC"):
                if (ner[0][0] == "US") or (ner[0][0] == "USA"):
                    location_ = "United States"
                elif (ner[0][0] == "UK"):
                    location_ = "United Kingdom"
                else:
                    location = ner[0][0]
                    self.params = {}
                    self.params["location"] = location
            elif (ner[0][1] == "ORG"):
                org = ner[0][0]
                self.params = {}
                self.params["org"] = org
            elif (ner[0][1] == "PERSON"):
                person = ner[0][0]
                self.params = {}
                self.params["person"] = person
        elif len(ner) > 1:
            name1 = ner[0][0]
            name2 = ner[1][0]
            self.params_2 = {"name1":name1, "name2":name2}
            
    def query_select(self):
        ## Keyword Extraction 
        # Entire Domain
        query1 = '''
        MATCH (k:Keyword)
        RETURN k.value as Keywords
        LIMIT 20
        '''
        # What does person do?
        query2 = ''' 
        MATCH (s:Sentence)-[]-(p:NER_Person)-[]-()-[a:APPOS]->(t:TagOccurrence)\
        -[nm:NMOD]->(o:NE_Organization)
        WHERE (p.value = $person)
        RETURN DISTINCT p.value as Name, o.value as Company, t.value as Position
        '''
        # Where is company located?
        query3 = '''
        MATCH (l:NER_Location)<-[]-(s:Sentence)-[]->(o:NER_Organization),
        (s)-[]->(:NER_Misc)
        WHERE (o.value = $org)
        RETURN o.value as Org, l.value as Location, s.text as Sentence
        '''
        ## How is person related to another via Approximate Nearest Neighbor (ANN)?
        # Similarity measure can be euclidean, jaccard, cosine, etc. 
        query4 = '''
        MATCH (s:Sentence)-[h:HAS_TAG]-(t:NER_Person:Tag)
        WITH {item: id(t), categories: COLLECT(id(s))} as textData
        WITH COLLECT(textData) AS data
        CALL algo.labs.ml.ann.stream('jaccard', data, {similarityCutoff: 0.005})
        YIELD item1, item2, similarity
        RETURN algo.asNode(item1).value AS From, algo.asNode(item2).value AS To, similarity AS Similarity
        ORDER BY From
        '''
    
        # Who is in a specific location? 
        query5 = '''
        MATCH (p:NER_Person)-[w:LIVES_IN]-(l:NER_Location)
        WHERE (l.value = $location)
        RETURN p.value as Person, l.value as Location
        '''

        # Who are people who work at an organization? 
        query6 = '''
        MATCH (s:Sentence)-[]-(p:NER_Person)-[]-()-[a:APPOS]->(t:TagOccurrence)\
        -[nm:NMOD]->(o:NE_Organization{value:$org})
        RETURN p.value as Name, o.value as Company, t.value as Position
        ORDER BY Name
        UNION
        MATCH (o:NE_Organization{value:$org})<-[nm:NMOD]-(p:NE_Person)\
        <-[:NSUBJ]-(r:Root)-[:DOBJ]->()-[]->(t:NER_O)
        WHERE t.value ENDS WITH 'st'
        RETURN DISTINCT p.value as Name, o.value as Company, t.value as Position
        ORDER BY Name
        '''

        #What did someone do (about something)? 
        query7 = '''
        MATCH (t:Tag)<-[h:HAS_TAG]-(s:Sentence)-[o:SENTENCE_TAG_OCCURRENCE]->\
        (p1:TagOccurrence{value:$person})<-[:NSUBJ]-(r:Root)
        WHERE (t.value = $selection)
        RETURN DISTINCT p1.value as Subject, t.value as Keyword, s.text as Sentence
        '''
    
        ##SENTIMENT (Sentiment isn't consistent in neo4j, needs to be improved)
        #What is the frequency?
        query8 = '''
        MATCH (ns: Negative)-[h:HAS_TAG]-(n:NER_Person)
        WHERE n.value = $person
        RETURN n.value as Person, COUNT(n.value) as Frequency
        '''
        query8_1 = '''
        MATCH (ns: Negative)-[h:HAS_TAG]-(o:NER_Organization)
        WHERE o.value = $org
        RETURN o.value as Org, COUNT(o.value) as Frequency
        '''
    
        #How often does entity appear? 
        query9 = '''
        MATCH (n:Tag)
        WHERE (n.value = $person)
        RETURN n.value as Person, SIZE((n)<-[:HAS_TAG]-()) as Frequency
        '''
        query9_1 = '''
        MATCH (n:NER_Organization)
        WHERE (n.value in $org)
        RETURN n.value as Org, SIZE((n)<-[:HAS_TAG]-()) as Frequency
        '''
    
        #Summarize the corpus
        query10 = '''
        MATCH (a:AnnotatedText)-[:CONTAINS_SENTENCE]->(s:Sentence)
        WITH a, count(*) as nSentences
        MATCH (a)-[:CONTAINS_SENTENCE]->(s:Sentence)-[:HAS_TAG]->(t:Tag)
        WITH a, s, count(distinct t) as nTags, (CASE WHEN nSentences*0.1 > 10 THEN 10 ELSE toInteger(nSentences*0.1) END) as nLimit
        WHERE nTags > 4
        WITH a, s, nLimit
        ORDER BY s.summaryRank
        WITH a, COLLECT({text: s.text, pos: s.sentenceNumber})[..nLimit] as summary
        UNWIND summary as sent
        RETURN sent.text as Corpus_Summary
        ORDER BY sent.pos
        '''

        for word,tag in self.tags:
            if word in ["keywords","common","frequent"]:
                print(self.graph.run(query1).to_table())
            elif word in ["work","do"]:
                print(self.graph.run(query2,self.params).to_table())
            elif word in ["located", "reside"]:
                print(self.graph.run(query3,self.params).to_table())
            elif word in ["related","similar", "close"]:
                print(self.graph.run(query4).to_table())
            elif word in ["lives", "live", "resides"]:
                print(self.graph.run(query5,self.params).to_table())
            elif word in ["works", "affiliated", "associated"]:
                print(self.graph.run(query6,self.params).to_table()) 
            elif word in ["said","says","say","speaking","spoke", "think","thought"]:
                self.params["selection"] = word
                print(self.graph.run(query7,self.params).to_table())
            elif word in ["negative", "negation"]:
                print(self.graph.run(query8,self.params).to_table())
            elif word in ["often", "frequently", "frequency"]:
                print(self.graph.run(query9,self.params).to_table())
            elif word in ["summarize","summarise","summary"]:
                print(self.graph.run(query10).to_table())
                
Host = Connect('bolt://localhost:7687','neo4j','gdb')
Host.start()