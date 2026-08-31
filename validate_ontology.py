from rdflib import Graph

ONTOLOGY_FILE = "ontology/pharmasense.ttl"

g = Graph()

try:
    g.parse(ONTOLOGY_FILE, format="turtle")

    print("Ontology parsed successfully.")
    print(f"Triple count: {len(g)}")

except Exception as e:
    print("Ontology validation failed.")
    print(e)