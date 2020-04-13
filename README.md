# Neo4j-QA

My thesis project at Seavus is a question-answering system leveraged by Neo4j that processes large, unstructured text data and fetches results for natural language processing (NLP) tasks ranging from keyword extraction to sentiment analysis. These tasks were made possible in Neo4j through the [GraphAware NLP framework](https://github.com/graphaware/neo4j-nlp). 

### Setup

In order for this framework to function properly, you first need to add a few JAR plugins from both [GraphAware](https://products.graphaware.com/) and the [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/). You will also want to download the graph algorithm library [APOC](https://neo4j.com/developer/neo4j-apoc/) that is freely available in Neo4j. It is required for some of the NLP tasks as well. 

Requirements:
* Neo4j 3.5.11 (or earlier)
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

### Python Driver

In order to connect between Python and Neo4j, change the credentials in `text_processor.py` and `query_pipeline.py` to your specifics. 

Example:
```
uri = 'bolt://localhost:7687'
username = 'neo4j'
password = 'gdb'
```

### Data

The BBC dataset used in these experiments were taken from the examples [here](https://neo4j.com/blog/accelerating-towards-natural-language-search-graphs/). They are in archived format and can be processed in `text_processor.py`, which feeds the news articles into the graph database and defines the schema of the knowledge graph. There are additional methods to call for enrichment, keyword extraction, and text summarization. 

### Demo

After the text is proccessed in Neo4j, simply test out the `demo_pipeline` with the `query_pipeline` in the same folder:

<p align="center">
  <img width="460" height="200" src="https://drive.google.com/uc?export=view&id=1b9eZzt5B4t-6fSTQpLtH_gaLxSD-x8Cq">
</p>
