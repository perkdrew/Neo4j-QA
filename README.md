# Neo4j-QA

My thesis project at Seavus is a question-answering system leveraged by Neo4j that processes large, unstructured text data and fetches results for natural language processing (NLP) tasks ranging from keyword extraction to sentiment analysis. These tasks were made possible in Neo4j through the [GraphAware NLP framework](https://github.com/graphaware/neo4j-nlp). 

### Setup

In order for this framework to function properly, you first need to add a few JAR plugins from both [GraphAware](https://products.graphaware.com/) and the [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/). You will also want to download the graph algorithm library [APOC](https://neo4j.com/developer/neo4j-apoc/) that is freely available in Neo4j. It is required for some of the NLP tasks as well. 

Requirements:
* Neo4j 3.5.6 (or earlier)
* `graphaware-server-enterprise-all`
* `nlp`
* `nlp-stanfordnlp` 
* `stanford-english-corenlp`
* `apoc`

Once the above plugins are placed in `neo4j.plugins` in `NEO4J_HOME/plugins/`, these lines are required in the `neo4j.conf` file in `NEO4J_HOME/conf/`:

```
dbms.unmanaged_extension_classes=com.graphaware.server=/graphaware
com.graphaware.runtime.enabled=true
dbms.security.procedures.whitelist=ga.nlp.*, apoc.*
dbms.security.procedures.unrestricted=ga.nlp.*, apoc.*
```

You will also need to allocate an appropriate heap size and page cache for Neo4j:

```
dbms.memory.heap.initial_size=3000m
dbms.memory.heap.max_size=5000m
```

### Data

The BBC dataset used in these experiments were taken from the examples [here](https://neo4j.com/blog/accelerating-towards-natural-language-search-graphs/). They are in archived format and they can be processed in the `news_processing.ipynb`, which feeds the news articles into the graph database and defines the schema of the knowledge graph. 

## Named-Entity Linking

In the GraphAware NLP framework, one key component missing from the Stanford CoreNLP is named-entity linking (NEL). By designing my own NEL component to predict the best candidates, my goal is to incorporate it into the final version of named-entity linking. As of right now, this component works separately. I will update soon with how I plan to accomplish this. Currently, the model training is being performed on Colab and the model testing on Azure.
