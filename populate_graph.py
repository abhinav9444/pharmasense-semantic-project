import html
import json
import re
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF
from rdflib.namespace import RDFS, XSD

JSON_FILE = Path("data/scraped_drugbank_1_200.json")
ONTOLOGY_FILE = Path("ontology/pharmasense.ttl")
OUTPUT_FILE = Path("pharmasense_kg.ttl")
PHARMA = Namespace("http://example.org/pharmasense#")


def clean(value):
    if value is None:
        return ""
    value = html.unescape(str(value))
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[ \t]+", " ", value)
    return re.sub(r"\n+", "\n", value).strip()


def values(value):
    return [x.strip() for x in clean(value).split("\n") if x.strip()]


def uri(value):
    return re.sub(r"[^A-Za-z0-9_]+", "_", clean(value)).strip("_")


def add(g, s, p, value):
    value = clean(value)
    if value and value.lower() not in {"not available", "n/a", "-"}:
        g.add((s, p, Literal(value, datatype=XSD.string)))


def target_id(fields, number):
    prefix = f"Drug_Target_{number}_"
    return clean(fields.get(prefix + "SwissProt_ID")) or clean(fields.get(prefix + "ID"))


def pathway_ids(value):
    return list(dict.fromkeys(
        x.upper() for x in re.findall(r"SMP\d+", clean(value), re.I)
    ))


def main():
    graph = Graph()
    graph.parse(ONTOLOGY_FILE, format="turtle")
    ontology_triples = len(graph)

    with open(JSON_FILE, encoding="utf-8") as f:
        records = json.load(f).get("drugs", [])

    if len(records) < 200:
        raise ValueError("At least 200 drug records are required.")

    for record in records[:200]:
        fields = record.get("fields", {})
        db_id = clean(fields.get("Primary_Accession_No")) or f"SOURCE_{record.get('source_id')}"
        drug = PHARMA[f"Drug_{uri(db_id)}"]
        graph.add((drug, RDF.type, PHARMA.Drug))
        add(graph, drug, PHARMA.drugBankId, db_id)
        add(graph, drug, PHARMA.drugName, fields.get("Generic_Name"))

        for drug_type in values(fields.get("Drug_Type")):
            if drug_type.lower() == "biotech":
                graph.add((drug, PHARMA.hasDrugType, PHARMA.BiotechType))
            elif drug_type.lower() == "small molecule":
                graph.add((drug, PHARMA.hasDrugType, PHARMA.SmallMoleculeType))

        categories = values(fields.get("Drug_Category"))
        for category in categories:
            category_uri = (
                PHARMA.Anticoagulants
                if category.lower() == "anticoagulants"
                else PHARMA[f"Category_{uri(category)}"]
            )
            if category_uri != PHARMA.Anticoagulants:
                graph.add((category_uri, RDF.type, PHARMA.DrugCategory))
                graph.add((category_uri, RDFS.label, Literal(category, datatype=XSD.string)))
            graph.add((drug, PHARMA.hasCategory, category_uri))

        for pathway in pathway_ids(fields.get("Pathways")):
            graph.add((drug, PHARMA.participatesInPathway, PHARMA[f"Pathway_{pathway}"]))

        mechanism = clean(fields.get("Mechanism_Of_Action"))
        if "thrombin" in mechanism.lower():
            add(graph, drug, PHARMA.mechanismOfAction, mechanism)
            for code in values(fields.get("ATC_Codes")):
                add(graph, drug, PHARMA.atcCode, code)

        toxicity = clean(fields.get("Toxicity"))
        if "bleeding" in toxicity.lower() and len(categories) > 1:
            add(graph, drug, PHARMA.toxicity, toxicity)

        for n in range(1, 4):
            target = target_id(fields, n)
            if not target:
                continue
            prefix = f"Drug_Target_{n}_"
            target_uri = PHARMA[f"Target_{uri(target)}"]
            graph.add((target_uri, RDF.type, PHARMA.ProteinTarget))
            graph.add((drug, PHARMA.hasTarget, target_uri))
            add(graph, target_uri, PHARMA.geneName, fields.get(prefix + "Gene_Name"))
            add(graph, target_uri, PHARMA.generalFunction, fields.get(prefix + "General_Function"))
            add(graph, target_uri, PHARMA.specificFunction, fields.get(prefix + "Specific_Function"))

            # Target pathways are needed for pathway co-membership.
            for pathway in pathway_ids(fields.get(prefix + "Pathway")):
                graph.add((target_uri, PHARMA.associatedWithPathway,
                           PHARMA[f"Pathway_{pathway}"]))

    graph.serialize(OUTPUT_FILE, format="turtle")
    data_triples = len(graph) - ontology_triples

    print("Drugs processed: 200")
    print(f"Ontology triples: {ontology_triples}")
    print(f"Data triples: {data_triples}")
    print(f"Total triples: {len(graph)}")
    print(f"Output: {OUTPUT_FILE}")

    if data_triples < 500:
        raise ValueError("Minimum 500 data triples not reached.")


if __name__ == "__main__":
    main()
