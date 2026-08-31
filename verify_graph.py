from rdflib import Graph, Namespace, RDF

PHARMA = Namespace("http://example.org/pharmasense#")
GRAPH_FILE = "pharmasense_kg.ttl"
g = Graph()
g.parse(GRAPH_FILE, format="turtle")

print(f"Total triples: {len(g)}")

lepirudin = None
for drug in g.subjects(RDF.type, PHARMA.Drug):
    name = g.value(drug, PHARMA.drugName)
    if name and str(name).lower() == "lepirudin":
        lepirudin = drug
        break

if not lepirudin:
    print("\nLepirudin not found.")
    raise SystemExit

print("\nLepirudin URI:")
print(lepirudin)

print("\nDrug properties:")
for predicate, obj in g.predicate_objects(lepirudin):
    print(f"{predicate} -> {obj}")

print("\nTargets:")
for target in g.objects(lepirudin, PHARMA.hasTarget):
    print(f"\nTarget: {target}")
    for predicate, obj in g.predicate_objects(target):
        print(f"  {predicate} -> {obj}")

print("\nCategories:")
for category in g.objects(lepirudin, PHARMA.hasCategory):
    print(category)

print("\nPathways:")
for pathway in g.objects(lepirudin, PHARMA.participatesInPathway):
    print(pathway)

print("\nATC codes:")
for code in g.objects(lepirudin, PHARMA.atcCode):
    print(code)
