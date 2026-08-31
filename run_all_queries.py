from pathlib import Path
from rdflib import Graph
from owlrl import DeductiveClosure, OWLRL_Semantics

GRAPH_FILE = "pharmasense_kg.ttl"
QUERY_FILE = "queries.sparql"
RESULT_DIR = Path("query_results")


def load_queries():
    text = Path(QUERY_FILE).read_text(encoding="utf-8")
    prefixes = "\n".join(
        line.strip() for line in text.splitlines()
        if line.strip().upper().startswith("PREFIX ")
    )
    sections = text.split("#################################################################")
    queries = []
    for section in sections:
        start = section.find("SELECT")
        if start >= 0:
            queries.append(prefixes + "\n\n" + section[start:].strip())
    if len(queries) != 5:
        raise ValueError(f"Expected 5 queries, found {len(queries)}")
    return queries


def execute(graph, query, output_file):
    results = graph.query(query)
    with open(output_file, "w", encoding="utf-8") as file:
        for row in results:
            file.write(" | ".join(str(value) for value in row) + "\n")
    print(f"Saved: {output_file}")


def main():
    print("Loading queries...")
    queries = load_queries()
    print(f"Queries found: {len(queries)}\n")

    print("Loading knowledge graph...")
    graph = Graph()
    graph.parse(GRAPH_FILE, format="turtle")
    print(f"Graph triples: {len(graph)}\n")

    RESULT_DIR.mkdir(exist_ok=True)

    for number in range(1, 5):
        print(f"Executing Query {number}...")
        execute(graph, queries[number - 1], RESULT_DIR / f"query{number}.txt")

    print("\nPreparing graph for Query 5...")
    inferred = Graph()
    for triple in graph:
        inferred.add(triple)
    print(f"Original triples: {len(graph)}")
    print("Applying OWL-RL reasoning...")
    DeductiveClosure(OWLRL_Semantics).expand(inferred)
    print(f"Triples after reasoning: {len(inferred)}\n")

    print("Executing Query 5...")
    execute(inferred, queries[4], RESULT_DIR / "query5.txt")

    print("\n====================================")
    print("All queries executed successfully")
    print("====================================")


if __name__ == "__main__":
    main()
