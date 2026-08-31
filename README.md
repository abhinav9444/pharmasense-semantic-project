# PharmaSense Semantic Project

Converts DrugBank Lite data into an OWL ontology, RDF knowledge graph and SPARQL query layer.

## Flow

DrugBank Lite → JSON → OWL Ontology → RDF Graph → SPARQL → OWL-RL reasoning → Semantic Layer

## Project Structure

```text
pharmasense-semantic-project/
├── data/
├── ontology/
├── query_results/
├── drugbank_scraper.py
├── populate_graph.py
├── pharmasense_kg.ttl
├── queries.sparql
├── run_all_queries.py
├── run_reasoning_query.py
├── semantic_layer.py
├── semantic_layer_demo.txt
├── test_reasoning.py
├── validate_ontology.py
├── verify_graph.py
└── requirements.txt
```

## What was done

1. Scraped 200 DrugBank Lite records (IDs 1–200) and stored the source data as JSON.
2. Created a hand-authored OWL ontology with the required classes, object properties, datatype properties, inverse relationships and transitive property.
3. Added OWL restrictions so drug types and anticoagulant classification can be inferred.
4. Converted the JSON records into RDF triples and generated `pharmasense_kg.ttl`.
5. Wrote and tested the five required SPARQL queries.
6. Added OWL-RL reasoning for the inference query.
7. Built `semantic_layer.py` so the five assignment questions use validated SPARQL, while other questions can be converted to read-only SPARQL through local Ollama/Gemma.
8. Kept SPARQL results visible in the semantic-layer output to show grounding.

## Problems and fixes

- SPARQL parsing failed because query sections and prefixes were not preserved correctly. Query loading was corrected.
- Query 5 initially failed on the `pharma` prefix. Prefix handling was fixed.
- Category labels were changed to standard `rdfs:label`.
- The first reasoning test did not infer the required classes. OWL equivalent-class restrictions were added and reasoning then passed.
- Query 2 was initially empty because pathway IDs were only partially extracted. Pathway extraction was corrected and target-associated pathways were retained.
- Query 1 initially returned unrelated rows with empty target fields. The query was tightened to require a real shared target.
- Custom semantic-layer questions could be misclassified as one of the five validated queries. The five assignment questions are now matched explicitly; other questions use the custom path.
- Docker was considered for the enterprise deployment stage but is deferred because Docker is not currently available on the development machine.

## Current validation

- Records: **200**
- Ontology triples: **152**
- Knowledge graph triples: **4,002**
- SPARQL queries: **5**
- OWL-RL inference tested successfully
- Sample semantic-layer output: `semantic_layer_demo.txt`

## Run

```bash
pip install -r requirements.txt
python validate_ontology.py
python populate_graph.py
python verify_graph.py
python run_all_queries.py
python test_reasoning.py
python semantic_layer.py
```

For custom semantic-layer questions, Ollama must be running with Gemma 3 4B:

```bash
ollama pull gemma3:4b
```

## Notes

The project focuses on the required RDF/OWL/SPARQL modelling rather than a UI. The stored query results and semantic-layer demo provide reproducible evidence of the work.
