# ==============================================================
# Fully AI Generated Knowledge Graph Visualiser for PharmaSense 
# ==============================================================

from pathlib import Path
from collections import defaultdict, Counter
from rdflib import Graph, URIRef, Literal, RDF, RDFS, OWL
import json
import webbrowser

# ============================================================
# Configuration
# ============================================================

RDF_FILE = Path("C:\\Users\\abhinav.aq.singh\\VS Code\\New\\pharmasense-semantic-project\\pharmasense_kg.ttl")
OUTPUT_FILE = Path("knowledge_graph.html")


# ============================================================
# Load RDF
# ============================================================

if not RDF_FILE.exists():
    raise FileNotFoundError(
        f"RDF file not found: {RDF_FILE.resolve()}"
    )

g = Graph()
g.parse(RDF_FILE, format="turtle")

print(f"Loaded triples: {len(g)}")


# ============================================================
# Helpers
# ============================================================

def local_name(uri):
    """Return readable name from a URI."""
    value = str(uri)

    if "#" in value:
        return value.rsplit("#", 1)[-1]

    return value.rstrip("/").rsplit("/", 1)[-1]


def readable_label(uri):
    """Create a readable label for a KG resource."""
    value = local_name(uri)

    # Keep identifiers such as Drug_DB00001 readable.
    return value.replace("_", " ")


# ============================================================
# Ontology/schema resources
# ============================================================

SCHEMA_TYPES = {
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
    RDF.Property,
}

SCHEMA_PREDICATES = {
    RDFS.subClassOf,
    RDFS.subPropertyOf,
    RDFS.domain,
    RDFS.range,
    OWL.inverseOf,
    OWL.equivalentClass,
    OWL.equivalentProperty,
    OWL.disjointWith,
}


# Find resources used as ontology definitions.
schema_resources = set()

for s, p, o in g:

    if p == RDF.type and o in SCHEMA_TYPES:
        schema_resources.add(s)

    if p in SCHEMA_PREDICATES:

        if isinstance(s, URIRef):
            schema_resources.add(s)

        if isinstance(o, URIRef):
            schema_resources.add(o)


# ============================================================
# Find actual data resources
# ============================================================

data_nodes = set()

for s, p, o in g:

    if isinstance(s, URIRef) and s not in schema_resources:
        data_nodes.add(s)

    if isinstance(o, URIRef) and o not in schema_resources:
        data_nodes.add(o)


# Remove obvious RDF/OWL vocabulary.
vocabulary = {
    "Class",
    "ObjectProperty",
    "DatatypeProperty",
    "AnnotationProperty",
    "Property",
    "Resource",
    "Thing",
    "type",
    "domain",
    "range",
    "subClassOf",
    "subPropertyOf",
    "inverseOf",
    "equivalentClass",
    "equivalentProperty",
}

data_nodes = {
    node for node in data_nodes
    if local_name(node) not in vocabulary
}


# ============================================================
# Labels
# ============================================================

labels = {}

for s, p, o in g:

    if s not in data_nodes:
        continue

    if p == RDFS.label and isinstance(o, Literal):
        labels[str(s)] = str(o)


for node in data_nodes:

    node_id = str(node)

    if node_id not in labels:
        labels[node_id] = readable_label(node)


# ============================================================
# Explicit RDF types
# ============================================================

node_types = defaultdict(set)

for s, p, o in g:

    if s not in data_nodes:
        continue

    if p != RDF.type:
        continue

    if not isinstance(o, URIRef):
        continue

    type_name = local_name(o)

    if type_name not in vocabulary:
        node_types[str(s)].add(type_name)


# ============================================================
# Relationship-based type inference
# ============================================================

relationship_types = {

    "hasTarget": "ProteinTarget",
    "targetsProtein": "ProteinTarget",

    "hasCategory": "DrugCategory",

    "hasDrugType": "DrugType",

    "hasATCClassification": "ATCClassification",

    "participatesInPathway": "Pathway",
    "associatedWithPathway": "Pathway",

}


for s, p, o in g:

    if not isinstance(o, URIRef):
        continue

    if s not in data_nodes or o not in data_nodes:
        continue

    relation = local_name(p)

    inferred_type = relationship_types.get(relation)

    if inferred_type:
        node_types[str(o)].add(inferred_type)


# ============================================================
# URI-based fallback classification
# ============================================================

def infer_from_uri(node_id):

    name = local_name(node_id).lower()

    if name.startswith("drug_"):
        return "Drug"

    if name.startswith("target_"):
        return "ProteinTarget"

    if name.startswith("pathway_"):
        return "Pathway"

    if "atc" in name:
        return "ATCClassification"

    return None


for node in data_nodes:

    node_id = str(node)

    if node_types[node_id]:
        continue

    inferred = infer_from_uri(node_id)

    if inferred:
        node_types[node_id].add(inferred)


# ============================================================
# Label-based fallback classification
# ============================================================

for node in data_nodes:

    node_id = str(node)

    if node_types[node_id]:
        continue

    text = (
        labels.get(node_id, "") +
        " " +
        local_name(node)
    ).lower()

    if "pathway" in text:
        node_types[node_id].add("Pathway")

    elif "category" in text:
        node_types[node_id].add("DrugCategory")

    elif "atc" in text:
        node_types[node_id].add("ATCClassification")

    elif "target" in text or "protein" in text:
        node_types[node_id].add("ProteinTarget")

    elif "drug" in text:
        node_types[node_id].add("Drug")

    else:
        node_types[node_id].add("Other")


# ============================================================
# Build edges
# ============================================================

edges = []
seen_edges = set()

for s, p, o in g:

    # Both ends must be actual KG resources.
    if s not in data_nodes:
        continue

    if not isinstance(o, URIRef):
        continue

    if o not in data_nodes:
        continue

    # Do NOT remove normal application relationships.
    if p in SCHEMA_PREDICATES:
        continue

    relation = local_name(p)

    # Avoid RDF type edges.
    if p == RDF.type:
        continue

    key = (
        str(s),
        str(o),
        relation
    )

    if key in seen_edges:
        continue

    seen_edges.add(key)

    edges.append({
        "source": str(s),
        "target": str(o),
        "label": relation
    })


# ============================================================
# Build node JSON
# ============================================================

nodes = []

for node in data_nodes:

    node_id = str(node)

    types = list(
        node_types.get(
            node_id,
            {"Other"}
        )
    )

    node_type = types[0]

    nodes.append({
        "id": node_id,
        "label": labels[node_id],
        "type": node_type
    })


# ============================================================
# Statistics
# ============================================================

type_counts = Counter(
    node["type"]
    for node in nodes
)

print()
print("=" * 45)
print("        PharmaSense Knowledge Graph")
print("=" * 45)
print(f"RDF triples       : {len(g)}")
print(f"KG nodes          : {len(nodes)}")
print(f"KG relationships  : {len(edges)}")
print()
print("Node types:")

for name, count in sorted(type_counts.items()):
    print(f"  {name:<25} {count}")

print("=" * 45)


# ============================================================
# Convert data to JSON
# ============================================================

nodes_json = json.dumps(
    nodes,
    ensure_ascii=False
)

edges_json = json.dumps(
    edges,
    ensure_ascii=False
)


# ============================================================
# HTML
# ============================================================

html = """
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>PharmaSense Knowledge Graph</title>

<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    font-family: Arial, sans-serif;
}

#graph {
    width: 100%;
    height: 100%;
    background: #fafafa;
}

.title {
    position: absolute;
    top: 18px;
    left: 20px;

    z-index: 10;

    background: white;

    padding: 13px 20px;

    border-radius: 8px;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.15);

    font-size: 22px;
    font-weight: bold;
}

.legend {
    position: absolute;
    top: 82px;
    left: 20px;

    z-index: 10;

    background: white;

    padding: 14px 16px;

    border-radius: 8px;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.15);

    font-size: 14px;
}

.legend-item {
    margin: 7px 0;
}

.dot {
    display: inline-block;

    width: 13px;
    height: 13px;

    border-radius: 50%;

    margin-right: 7px;
}

.info {
    position: absolute;

    top: 20px;
    right: 20px;

    width: 330px;
    max-height: 80vh;

    overflow-y: auto;

    z-index: 20;

    background: white;

    padding: 17px;

    border-radius: 8px;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.15);

    display: none;
}

.info h3 {
    margin-top: 0;
}

.uri {
    font-size: 11px;

    color: #555;

    word-break: break-all;
}

.edge {
    stroke: #999;

    stroke-opacity: 0.45;

    stroke-width: 1;
}

.edge-label {
    font-size: 8px;

    fill: #555;

    pointer-events: none;
}

.node {
    stroke: #333;

    stroke-width: 1.2px;

    cursor: pointer;
}

.node-label {
    font-size: 9px;

    pointer-events: none;
}

</style>

</head>


<body>


<div class="title">
    PharmaSense Knowledge Graph
</div>


<div class="legend">

    <div class="legend-item">
        <span class="dot"
              style="background:#4e79a7"></span>
        Drug
    </div>

    <div class="legend-item">
        <span class="dot"
              style="background:#59a14f"></span>
        Protein Target
    </div>

    <div class="legend-item">
        <span class="dot"
              style="background:#f28e2b"></span>
        Pathway
    </div>

    <div class="legend-item">
        <span class="dot"
              style="background:#b07aa1"></span>
        Drug Category
    </div>

    <div class="legend-item">
        <span class="dot"
              style="background:#9c755f"></span>
        Drug Type
    </div>

    <div class="legend-item">
        <span class="dot"
              style="background:#edc948"></span>
        ATC Classification
    </div>

    <div class="legend-item">
        <span class="dot"
              style="background:#e15759"></span>
        Other
    </div>

</div>


<div id="info" class="info"></div>


<svg id="graph"></svg>


<script>


const nodes = __NODES__;

const links = __EDGES__;


const svg = d3.select("#graph");

let width = window.innerWidth;

let height = window.innerHeight;


svg
    .attr("width", width)
    .attr("height", height);


const container = svg.append("g");


// ============================================================
// Zoom
// ============================================================

svg.call(

    d3.zoom()
        .scaleExtent([0.1, 6])

        .on("zoom", function(event) {

            container.attr(
                "transform",
                event.transform
            );

        })

);


// ============================================================
// Arrow
// ============================================================

svg.append("defs")

    .append("marker")

    .attr("id", "arrow")

    .attr("viewBox", "0 -5 10 10")

    .attr("refX", 23)

    .attr("refY", 0)

    .attr("markerWidth", 6)

    .attr("markerHeight", 6)

    .attr("orient", "auto")

    .append("path")

    .attr("d", "M0,-5L10,0L0,5")

    .attr("fill", "#999");


// ============================================================
// Colors
// ============================================================

function nodeColor(type) {

    const t = type.toLowerCase();

    if (t === "drug")
        return "#4e79a7";

    if (
        t.includes("protein") ||
        t.includes("target")
    )
        return "#59a14f";

    if (t.includes("pathway"))
        return "#f28e2b";

    if (t.includes("category"))
        return "#b07aa1";

    if (t.includes("drugtype"))
        return "#9c755f";

    if (t.includes("atc"))
        return "#edc948";

    return "#e15759";
}


// ============================================================
// Force simulation
// ============================================================

const simulation = d3.forceSimulation(nodes)

    .force(
        "link",

        d3.forceLink(links)
            .id(function(d) {
                return d.id;
            })
            .distance(120)
            .strength(0.35)
    )

    .force(
        "charge",

        d3.forceManyBody()
            .strength(-80)
    )

    .force(
        "center",

        d3.forceCenter(
            width / 2,
            height / 2
        )
    )

    .force(
        "collision",

        d3.forceCollide()
            .radius(18)
    );


// ============================================================
// Edges
// ============================================================

const link = container

    .append("g")

    .selectAll("line")

    .data(links)

    .enter()

    .append("line")

    .attr("class", "edge")

    .attr(
        "marker-end",
        "url(#arrow)"
    );


// ============================================================
// Edge labels
// ============================================================

const edgeLabel = container

    .append("g")

    .selectAll("text")

    .data(links)

    .enter()

    .append("text")

    .attr(
        "class",
        "edge-label"
    )

    .text(function(d) {
        return d.label;
    });


// ============================================================
// Nodes
// ============================================================

const node = container

    .append("g")

    .selectAll("circle")

    .data(nodes)

    .enter()

    .append("circle")

    .attr(
        "class",
        "node"
    )

    .attr(
        "r",
        function(d) {

            return d.type === "Drug"
                ? 10
                : 7;

        }
    )

    .attr(
        "fill",
        function(d) {

            return nodeColor(
                d.type
            );

        }
    )

    .call(

        d3.drag()

            .on(
                "start",
                dragStarted
            )

            .on(
                "drag",
                dragged
            )

            .on(
                "end",
                dragEnded
            )

    );


// ============================================================
// Node labels
// ============================================================

const label = container

    .append("g")

    .selectAll("text")

    .data(nodes)

    .enter()

    .append("text")

    .attr(
        "class",
        "node-label"
    )

    .attr("dx", 10)

    .attr("dy", 4)

    .text(function(d) {
        return d.label;
    });


// ============================================================
// Tooltip
// ============================================================

node.append("title")

    .text(function(d) {

        return (
            d.label +
            "\\nType: " +
            d.type
        );

    });


// ============================================================
// Click node
// ============================================================

node.on(
    "click",
    function(event, selected) {

        const connected =
            new Set();

        connected.add(
            selected.id
        );


        links.forEach(
            function(link) {

                if (
                    link.source.id === selected.id ||
                    link.target.id === selected.id
                ) {

                    connected.add(
                        link.source.id
                    );

                    connected.add(
                        link.target.id
                    );

                }

            }
        );


        // Fade unrelated nodes.

        node.attr(
            "opacity",
            function(d) {

                return connected.has(
                    d.id
                )
                    ? 1
                    : 0.08;

            }
        );


        label.attr(
            "opacity",
            function(d) {

                return connected.has(
                    d.id
                )
                    ? 1
                    : 0.08;

            }
        );


        link.attr(
            "opacity",
            function(d) {

                return (
                    d.source.id === selected.id ||
                    d.target.id === selected.id
                )
                    ? 1
                    : 0.05;

            }
        );


        edgeLabel.attr(
            "opacity",
            function(d) {

                return (
                    d.source.id === selected.id ||
                    d.target.id === selected.id
                )
                    ? 1
                    : 0.05;

            }
        );


        // Grounding information.

        const relationships = links

            .filter(
                function(link) {

                    return (
                        link.source.id === selected.id ||
                        link.target.id === selected.id
                    );

                }
            )

            .map(
                function(link) {

                    const outgoing =
                        link.source.id === selected.id;

                    const other =
                        outgoing
                            ? link.target
                            : link.source;

                    return `
                        <div style="margin:8px 0">
                            <b>
                                ${outgoing ? "→" : "←"}
                                ${link.label}
                            </b>
                            <br>
                            ${other.label}
                        </div>
                    `;

                }
            )

            .join("");


        const info =
            document.getElementById(
                "info"
            );


        info.innerHTML = `

            <h3>
                ${selected.label}
            </h3>

            <p>
                <b>Type:</b>
                ${selected.type}
            </p>

            <p>
                <b>Grounding URI:</b>
            </p>

            <div class="uri">
                ${selected.id}
            </div>

            <hr>

            <b>
                Relationships
            </b>

            ${relationships}

        `;


        info.style.display = "block";

    }
);


// ============================================================
// Background click
// ============================================================

svg.on(
    "click",
    function(event) {

        if (
            event.target.tagName === "svg"
        ) {

            node.attr(
                "opacity",
                1
            );

            label.attr(
                "opacity",
                1
            );

            link.attr(
                "opacity",
                1
            );

            edgeLabel.attr(
                "opacity",
                1
            );

            document.getElementById(
                "info"
            ).style.display = "none";

        }

    }
);


// ============================================================
// Simulation
// ============================================================

simulation.on(
    "tick",
    function() {

        link

            .attr(
                "x1",
                function(d) {
                    return d.source.x;
                }
            )

            .attr(
                "y1",
                function(d) {
                    return d.source.y;
                }
            )

            .attr(
                "x2",
                function(d) {
                    return d.target.x;
                }
            )

            .attr(
                "y2",
                function(d) {
                    return d.target.y;
                }
            );


        edgeLabel

            .attr(
                "x",
                function(d) {

                    return (
                        d.source.x +
                        d.target.x
                    ) / 2;

                }
            )

            .attr(
                "y",
                function(d) {

                    return (
                        d.source.y +
                        d.target.y
                    ) / 2;

                }
            );


        node

            .attr(
                "cx",
                function(d) {
                    return d.x;
                }
            )

            .attr(
                "cy",
                function(d) {
                    return d.y;
                }
            );


        label

            .attr(
                "x",
                function(d) {
                    return d.x;
                }
            )

            .attr(
                "y",
                function(d) {
                    return d.y;
                }
            );

    }
);


// ============================================================
// Drag
// ============================================================

function dragStarted(event, d) {

    if (!event.active)
        simulation
            .alphaTarget(0.3)
            .restart();

    d.fx = d.x;
    d.fy = d.y;
}


function dragged(event, d) {

    d.fx = event.x;
    d.fy = event.y;
}


function dragEnded(event, d) {

    if (!event.active)
        simulation
            .alphaTarget(0);

    d.fx = null;
    d.fy = null;
}


// ============================================================
// Resize
// ============================================================

window.addEventListener(
    "resize",
    function() {

        width = window.innerWidth;
        height = window.innerHeight;

        svg

            .attr(
                "width",
                width
            )

            .attr(
                "height",
                height
            );

        simulation

            .force(
                "center",
                d3.forceCenter(
                    width / 2,
                    height / 2
                )
            )

            .alpha(0.2)

            .restart();

    }
);

</script>

</body>

</html>
"""


# ============================================================
# Insert JSON safely
# ============================================================

html = html.replace(
    "__NODES__",
    nodes_json
)

html = html.replace(
    "__EDGES__",
    edges_json
)


# ============================================================
# Save
# ============================================================

OUTPUT_FILE.write_text(
    html,
    encoding="utf-8"
)


print(
    f"\nGenerated: "
    f"{OUTPUT_FILE.resolve()}"
)


# Open browser
webbrowser.open(
    OUTPUT_FILE.resolve().as_uri()
)