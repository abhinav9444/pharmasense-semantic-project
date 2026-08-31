from rdflib import Graph
from owlrl import DeductiveClosure, OWLRL_Semantics

GRAPH_FILE = "pharmasense_kg.ttl"
QUERY_FILE = "queries.sparql"

g = Graph()
g.parse(GRAPH_FILE, format="turtle")

print(f"Original triples: {len(g)}")
print("Applying OWL-RL reasoning...")
DeductiveClosure(OWLRL_Semantics).expand(g)
print(f"Triples after reasoning: {len(g)}")

queries = []
text = open(QUERY_FILE, encoding="utf-8").read()
prefixes = "\n".join(
    line.strip() for line in text.splitlines()
    if line.strip().upper().startswith("PREFIX ")
)
for section in text.split("#################################################################"):
    start = section.find("SELECT")
    if start >= 0:
        queries.append(prefixes + "\n\n" + section[start:].strip())

print("Executing Query 5...")
for row in g.query(queries[4]):
    print(" | ".join(str(value) for value in row))
