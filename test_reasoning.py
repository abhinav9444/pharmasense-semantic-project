from rdflib import Graph, Namespace, RDF
from owlrl import DeductiveClosure, OWLRL_Semantics

PHARMA = Namespace("http://example.org/pharmasense#")
ONTOLOGY_FILE = "ontology/pharmasense.ttl"
g = Graph()
g.parse(ONTOLOGY_FILE, format="turtle")

drug = PHARMA.Lepirudin
g.add((drug, RDF.type, PHARMA.Drug))
g.add((drug, PHARMA.hasDrugType, PHARMA.BiotechType))
g.add((drug, PHARMA.hasCategory, PHARMA.Anticoagulants))

print("Before reasoning:")
for triple in g:
    if triple[0] == drug:
        print(triple)

DeductiveClosure(OWLRL_Semantics).expand(g)

print("\nAfter reasoning:")
for drug_type in g.objects(drug, RDF.type):
    print(drug_type)

print("\nInference test:")
print("BiotechDrug:", (drug, RDF.type, PHARMA.BiotechDrug) in g)
print("AnticoagulantDrug:", (drug, RDF.type, PHARMA.AnticoagulantDrug) in g)
