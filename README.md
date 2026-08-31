# PharmaSense Semantic Project

## Overview

A small semantic-web project built from 200 DrugBank Lite records scraped from TogoDB.

The project converts the source data into an OWL ontology and RDF knowledge graph, then uses SPARQL for the five required research queries. Query 5 uses OWL-RL reasoning. A small semantic layer maps natural-language questions to the validated queries or generates a read-only SPARQL query for other questions.

## Structure

```text
pharmasense-semantic-layer-project/
├── data/
│   └── scraped_drugbank_1_200.json
├── ontology/
│   └── pharmasense.ttl
├── query_results/
│   ├── query1.txt
│   ├── query2.txt
│   ├── query3.txt
│   ├── query4.txt
│   └── query5.txt
├── drugbank_scraper.py
├── populate_graph.py
├── pharmasense_kg.ttl
├── queries.sparql
├── run_all_queries.py
├── semantic_layer.py
├── semantic_layer_demo.txt
├── test_reasoning.py
├── validate_ontology.py
├── verify_graph.py
└── requirements.txt
```

## Project Flow

```text
DrugBank Lite
   ↓
JSON
   ↓
OWL Ontology
   ↓
RDF Knowledge Graph
   ↓
SPARQL Queries
   ↓
OWL-RL reasoning for Query 5
   ↓
Semantic Layer
   ↓
Grounded Answer
```

## What was done

### Phase 1

Scraped IDs 1–200 and stored the key-value data in JSON. Created a hand-authored OWL ontology with the required classes, object properties, datatype properties, inverse properties and a transitive property.

The ontology also defines restrictions that allow `BiotechDrug`, `SmallMoleculeDrug` and `AnticoagulantDrug` to be inferred from existing properties.

### Phase 2

Converted the 200 JSON records into RDF using the ontology. Only relationships useful to the assignment were retained instead of carrying the complete source export into the graph.

### Phase 3

Implemented and executed the five required SPARQL queries. Query results are stored under `query_results/`.

### Phase 4

`semantic_layer.py` accepts natural-language questions.

For the five known assignment questions:

```text
Question → validated query → RDF graph → grounded result
```

For other questions:

```text
Question → Gemma → SPARQL → RDF graph → results → natural-language answer
```

The generated SPARQL and actual results are shown for custom questions. A sample run is stored in `semantic_layer_demo.txt`.

### Knowledge Graph Visualization

The generated RDF knowledge graph can be visualized as an interactive network graph using Python libraries such as RDFLib and PyVis.

The visualization represents:

- Drugs as graph nodes
- Protein targets as graph nodes
- Pathways as graph nodes
- Categories and drug types as graph nodes
- RDF properties such as `hasTarget`, `hasCategory`, `hasDrugType` and `participatesInPathway` as directed edges

This provides a visual way to inspect how drugs, targets, pathways and classifications are connected in the PharmaSense knowledge graph.

## Main problems and fixes

- **Ontology reasoning initially failed:** OWL equivalence restrictions were added so the expected drug classes could be inferred.
- **Category labels:** used standard `rdfs:label` instead of creating a custom label property.
- **SPARQL loading:** prefix handling was fixed when extracting the five queries from one file.
- **Query 2 was initially empty:** pathway extraction captured only one pathway from a multi-value field. The parser was corrected to retain all pathway IDs.
- **Query 1 returned empty rows:** optional target fields caused unrelated drugs to appear. The query was tightened to require the shared target and its details.
- **Custom semantic-layer questions:** Gemma could return explanatory text instead of SPARQL, so the response parser now extracts the first `SELECT` or `ASK` query and rejects write operations.

## Current checks

- 200 drug records
- 152 ontology triples
- 4,002 knowledge-graph triples
- 5 validated SPARQL queries
- 4,673 triples after OWL-RL reasoning in the latest reasoning run

## Run

```bash
pip install -r requirements.txt
python validate_ontology.py
python populate_graph.py
python verify_graph.py
python run_all_queries.py
python semantic_layer.py
```

For custom natural-language questions, Ollama with Gemma 3 4B is required:

```bash
ollama pull gemma3:4b
```
