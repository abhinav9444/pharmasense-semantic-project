from pathlib import Path

from rdflib import Graph
from owlrl import DeductiveClosure, OWLRL_Semantics

GRAPH_FILE = "pharmasense_kg.ttl"
QUERY_FILE = "queries.sparql"
RESULTS_DIR = Path("query_results")


def load_queries(text):
    prefixes = "\n".join(
        line for line in text.splitlines()
        if line.strip().upper().startswith("PREFIX ")
    )

    queries = []
    for section in text.split("#################################################################"):
        select_position = section.find("SELECT")
        if select_position == -1:
            continue
        queries.append(prefixes + "\n\n" + section[select_position:].strip())

    return queries


def execute_query(graph, query, output_file):
    results = graph.query(query)
    with open(output_file, "w", encoding="utf-8") as file:
        for row in results:
            file.write(" | ".join(str(value) for value in row) + "\n")


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    print("Loading queries...")
    query_text = Path(QUERY_FILE).read_text(encoding="utf-8")
    queries = load_queries(query_text)
    print(f"Queries found: {len(queries)}")

    if len(queries) != 5:
        raise ValueError(f"Expected 5 queries, found {len(queries)}")

    graph = Graph()
    print("\nLoading knowledge graph...")
    graph.parse(GRAPH_FILE, format="turtle")
    print(f"Graph triples: {len(graph)}")

    for number in range(4):
        output_file = RESULTS_DIR / f"query{number + 1}.txt"
        print(f"\nExecuting Query {number + 1}...")
        execute_query(graph, queries[number], output_file)
        print(f"Saved: {output_file}")

    print("\nPreparing graph for Query 5...")
    reasoning_graph = Graph()
    reasoning_graph.parse(GRAPH_FILE, format="turtle")
    print(f"Original triples: {len(reasoning_graph)}")
    print("Applying OWL-RL reasoning...")
    DeductiveClosure(OWLRL_Semantics).expand(reasoning_graph)
    print(f"Triples after reasoning: {len(reasoning_graph)}")

    output_file = RESULTS_DIR / "query5.txt"
    print("\nExecuting Query 5...")
    execute_query(reasoning_graph, queries[4], output_file)
    print(f"Saved: {output_file}")

    print("\n====================================")
    print("All queries executed successfully")
    print("====================================")


if __name__ == "__main__":
    main()
