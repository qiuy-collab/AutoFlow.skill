import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


RENDERER_MAP = {
    "flowchart": "mermaid",
    "er_diagram": "mermaid",
    "mindmap": "mermaid",
    "timeline": "mermaid",
    "gantt_chart": "mermaid",
    "data_flow_diagram": "d2",
    "function_diagram": "d2",
    "architecture_diagram": "d2",
    "module_diagram": "d2",
    "database_schema_diagram": "d2",
    "table_structure_diagram": "d2",
    "network_topology": "d2",
    "dependency_graph": "d2",
    "wbs_diagram": "d2",
    "file_tree_diagram": "d2",
    "use_case_diagram": "plantuml",
    "class_diagram": "plantuml",
    "sequence_diagram": "plantuml",
    "activity_diagram": "plantuml",
    "state_diagram": "plantuml",
    "component_diagram": "plantuml",
    "deployment_diagram": "plantuml",
    "uml_diagram": "plantuml",
}

INSTALL_HINTS = {
    "mermaid": "Install Mermaid CLI with: npm install -g @mermaid-js/mermaid-cli",
    "d2": "Install D2 with: winget install Terrastruct.D2",
    "plantuml": "Install PlantUML with: winget install PlantUML.PlantUML",
}

EXECUTABLE_CANDIDATES = {
    "mermaid": ["mmdc", "mmdc.cmd"],
    "d2": ["d2", "d2.exe"],
    "plantuml": ["plantuml", "plantuml.cmd", "plantuml.bat"],
}


def parse_args():
    parser = argparse.ArgumentParser(description="Generate DSL-driven diagram assets for auto-lab.")
    parser.add_argument("--workflow", help="Path to workflow.json")
    parser.add_argument("--check", action="store_true", help="Check whether required renderers are available.")
    args = parser.parse_args()
    if not args.check and not args.workflow:
        parser.error("--workflow is required unless --check is used")
    return args


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str):
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def escape_label(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "<br/>")


def plain_text(text: str) -> str:
    return str(text).replace("\n", " ").strip()


def safe_alias(raw: str, prefix: str = "n") -> str:
    reserved = {"end", "class", "style", "linkstyle", "subgraph", "click", "default"}
    token = re.sub(r"\W+", "_", str(raw).strip())
    token = token.strip("_")
    if not token:
        token = prefix
    if token[0].isdigit():
        token = f"{prefix}_{token}"
    if token.lower() in reserved:
        token = f"{prefix}_{token}"
    return token


def require_fields(obj: dict, fields: list[str], context: str):
    missing = [field for field in fields if field not in obj or obj[field] in (None, "", [])]
    if missing:
        raise SystemExit(f"{context} is missing required field(s): {', '.join(missing)}")


def require_list(obj: dict, field: str, context: str):
    value = obj.get(field)
    if not isinstance(value, list) or not value:
        raise SystemExit(f"{context} requires non-empty list field: {field}")
    return value


def mermaid_direction(raw_direction: str) -> str:
    value = (raw_direction or "").strip().upper()
    return value if value in {"TD", "TB", "LR", "RL", "BT"} else "TD"


def d2_direction(raw_direction: str) -> str:
    value = (raw_direction or "").strip().upper()
    mapping = {
        "TD": "down",
        "TB": "down",
        "BT": "up",
        "LR": "right",
        "RL": "left",
        "RIGHT": "right",
        "LEFT": "left",
        "DOWN": "down",
        "UP": "up",
    }
    return mapping.get(value, "right")


def mermaid_node(node: dict, alias: str) -> str:
    label = escape_label(node.get("label", node.get("id", alias)))
    shape = node.get("shape", "process")
    if shape in {"start", "end"}:
        return f'{alias}(["{label}"])'
    if shape == "decision":
        return f'{alias}{{"{label}"}}'
    if shape == "data":
        return f'{alias}[/"{label}"/]'
    if shape == "subprocess":
        return f'{alias}[["{label}"]]'
    return f'{alias}["{label}"]'


def d2_shape(shape: str, fallback: str = "rectangle") -> str:
    mapping = {
        "actor": "person",
        "user": "person",
        "person": "person",
        "start": "oval",
        "end": "oval",
        "process": "rectangle",
        "service": "rectangle",
        "component": "rectangle",
        "module": "rectangle",
        "decision": "diamond",
        "data": "parallelogram",
        "store": "cylinder",
        "database": "cylinder",
        "queue": "queue",
        "cloud": "cloud",
        "server": "rectangle",
        "folder": "rectangle",
        "file": "page",
        "table": "sql_table",
    }
    return mapping.get(shape, fallback)


def build_mermaid_flowchart(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    nodes = require_list(diagram, "nodes", context)
    edges = require_list(diagram, "edges", context)
    alias_map = {}
    for node in nodes:
        require_fields(node, ["id"], f"{context} node")
        alias_map[node["id"]] = safe_alias(node["id"], "node")

    lines = [f"flowchart {mermaid_direction(diagram.get('direction', 'TD'))}"]
    if diagram.get("title"):
        lines.append(f"    %% {plain_text(diagram['title'])}")
    for node in nodes:
        lines.append(f"    {mermaid_node(node, alias_map[node['id']])}")
    for edge in edges:
        require_fields(edge, ["from", "to"], f"{context} edge")
        if edge["from"] not in alias_map or edge["to"] not in alias_map:
            raise SystemExit(f"{context} edge references unknown node: {edge['from']} -> {edge['to']}")
        label = str(edge.get("label", "")).strip()
        if label:
            lines.append(f'    {alias_map[edge["from"]]} -->|{escape_label(label)}| {alias_map[edge["to"]]}')
        else:
            lines.append(f'    {alias_map[edge["from"]]} --> {alias_map[edge["to"]]}')
    return "\n".join(lines)


def build_mermaid_er(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    entities = require_list(diagram, "entities", context)
    relations = require_list(diagram, "relations", context)
    entity_names = set()
    lines = ["erDiagram"]
    for entity in entities:
        require_fields(entity, ["name", "attributes"], f"{context} entity")
        entity_name = safe_alias(entity["name"], "ENTITY").upper()
        entity_names.add(entity_name)
        lines.append(f"    {entity_name} {{")
        for attr in entity["attributes"]:
            if isinstance(attr, dict):
                require_fields(attr, ["name"], f"{context} entity attribute")
                attr_type = attr.get("type", "string")
                attr_key = f" {attr['key']}" if attr.get("key") else ""
                lines.append(f"        {attr_type} {attr['name']}{attr_key}")
            else:
                lines.append(f"        string {str(attr)}")
        lines.append("    }")
    for relation in relations:
        require_fields(relation, ["from", "to"], f"{context} relation")
        source = safe_alias(relation["from"], "ENTITY").upper()
        target = safe_alias(relation["to"], "ENTITY").upper()
        if source not in entity_names or target not in entity_names:
            raise SystemExit(f"{context} relation references unknown entity: {relation['from']} -> {relation['to']}")
        relation_type = relation.get("type", "||--o{")
        label = escape_label(relation.get("label", "relates"))
        lines.append(f'    {source} {relation_type} {target} : "{label}"')
    return "\n".join(lines)


def append_mindmap(lines: list[str], node: dict, depth: int):
    require_fields(node, ["label"], "mindmap node")
    text = plain_text(node["label"])
    if not text:
        raise SystemExit("mindmap node label cannot be empty")
    lines.append(f'{"    " * depth}{text}')
    for child in node.get("children", []):
        append_mindmap(lines, child, depth + 1)


def build_mermaid_mindmap(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    root = diagram.get("root")
    if not isinstance(root, dict):
        raise SystemExit(f"{context} requires object field: root")
    lines = ["mindmap"]
    append_mindmap(lines, root, 1)
    return "\n".join(lines)


def build_mermaid_timeline(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    events = require_list(diagram, "events", context)
    lines = ["timeline"]
    if diagram.get("title"):
        lines.append(f"    title {plain_text(diagram['title'])}")
    for event in events:
        require_fields(event, ["period", "label"], f"{context} event")
        lines.append(f"    {plain_text(event['period'])} : {plain_text(event['label'])}")
    return "\n".join(lines)


def build_mermaid_gantt(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    tasks = require_list(diagram, "tasks", context)
    lines = ["gantt"]
    lines.append(f"    title {plain_text(diagram.get('title', diagram.get('name', 'Gantt Chart')))}")
    lines.append(f"    dateFormat {diagram.get('date_format', 'YYYY-MM-DD')}")
    lines.append(f"    axisFormat {diagram.get('axis_format', '%m/%d')}")
    current_section = None
    for task in tasks:
        require_fields(task, ["name", "start"], f"{context} task")
        section = task.get("section", "Plan")
        if section != current_section:
            current_section = section
            lines.append(f"    section {plain_text(section)}")
        parts = []
        if task.get("status"):
            parts.append(task["status"])
        if task.get("id"):
            parts.append(safe_alias(task["id"], "task"))
        parts.append(task["start"])
        if task.get("duration"):
            parts.append(task["duration"])
        elif task.get("end"):
            parts.append(task["end"])
        else:
            raise SystemExit(f"{context} task '{task['name']}' requires duration or end")
        lines.append(f"    {plain_text(task['name'])} : {', '.join(parts)}")
    return "\n".join(lines)


def append_d2_node(lines: list[str], alias: str, label: str, shape: str):
    lines.append(f'{alias}: "{escape_label(label)}"')
    lines.append(f"{alias}.shape: {shape}")


def build_d2_node_edge_diagram(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    nodes = require_list(diagram, "nodes", context)
    edges = require_list(diagram, "edges", context)
    alias_map = {}
    lines = [f"direction: {d2_direction(diagram.get('direction', 'LR'))}"]
    for node in nodes:
        require_fields(node, ["id"], f"{context} node")
        alias = safe_alias(node["id"], "node")
        alias_map[node["id"]] = alias
        append_d2_node(lines, alias, node.get("label", node["id"]), d2_shape(node.get("shape", "process")))
    for edge in edges:
        require_fields(edge, ["from", "to"], f"{context} edge")
        if edge["from"] not in alias_map or edge["to"] not in alias_map:
            raise SystemExit(f"{context} edge references unknown node: {edge['from']} -> {edge['to']}")
        label = str(edge.get("label", "")).strip()
        if label:
            lines.append(f'{alias_map[edge["from"]]} -> {alias_map[edge["to"]]}: "{escape_label(label)}"')
        else:
            lines.append(f'{alias_map[edge["from"]]} -> {alias_map[edge["to"]]}')
    return "\n".join(lines)


def build_d2_dfd(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    entities = require_list(diagram, "entities", context)
    processes = require_list(diagram, "processes", context)
    stores = require_list(diagram, "stores", context)
    flows = require_list(diagram, "flows", context)
    alias_map = {}
    lines = [f"direction: {d2_direction(diagram.get('direction', 'LR'))}"]
    for group, shape in ((entities, "person"), (processes, "oval"), (stores, "cylinder")):
        for item in group:
            require_fields(item, ["id"], f"{context} node")
            alias = safe_alias(item["id"], "node")
            alias_map[item["id"]] = alias
            append_d2_node(lines, alias, item.get("label", item["id"]), shape)
    for flow in flows:
        require_fields(flow, ["from", "to"], f"{context} flow")
        if flow["from"] not in alias_map or flow["to"] not in alias_map:
            raise SystemExit(f"{context} flow references unknown node: {flow['from']} -> {flow['to']}")
        label = str(flow.get("label", "")).strip()
        if label:
            lines.append(f'{alias_map[flow["from"]]} -> {alias_map[flow["to"]]}: "{escape_label(label)}"')
        else:
            lines.append(f'{alias_map[flow["from"]]} -> {alias_map[flow["to"]]}')
    return "\n".join(lines)


def build_d2_database_schema(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    tables = require_list(diagram, "tables", context)
    relations = require_list(diagram, "relations", context)
    alias_map = {}
    lines = [f"direction: {d2_direction(diagram.get('direction', 'LR'))}"]
    for table in tables:
        require_fields(table, ["name", "columns"], f"{context} table")
        alias = safe_alias(table["name"], "table")
        alias_map[table["name"]] = alias
        lines.append(f"{alias}: {{")
        lines.append("  shape: sql_table")
        for column in table["columns"]:
            if isinstance(column, dict):
                require_fields(column, ["name"], f"{context} table column")
                col_name = column["name"]
                col_type = column.get("type", "string")
                col_flags = []
                if column.get("key"):
                    col_flags.append(column["key"])
                if column.get("nullable") is False:
                    col_flags.append("NOT NULL")
                suffix = f" ({', '.join(col_flags)})" if col_flags else ""
                lines.append(f'  {safe_alias(col_name, "col")}: "{escape_label(col_name)} : {escape_label(col_type)}{suffix}"')
            else:
                lines.append(f'  {safe_alias(str(column), "col")}: "{escape_label(str(column))}"')
        lines.append("}")
    for relation in relations:
        require_fields(relation, ["from", "to"], f"{context} relation")
        if relation["from"] not in alias_map or relation["to"] not in alias_map:
            raise SystemExit(f"{context} relation references unknown table: {relation['from']} -> {relation['to']}")
        label = str(relation.get("label", relation.get("type", "FK"))).strip()
        lines.append(f'{alias_map[relation["from"]]} -> {alias_map[relation["to"]]}: "{escape_label(label)}"')
    return "\n".join(lines)


def build_d2_table_structure(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    require_fields(diagram, ["table_name", "columns"], context)
    lines = [f"direction: {d2_direction(diagram.get('direction', 'TD'))}"]
    alias = safe_alias(diagram["table_name"], "table")
    lines.append(f"{alias}: {{")
    lines.append("  shape: sql_table")
    for column in diagram["columns"]:
        if isinstance(column, dict):
            require_fields(column, ["name"], f"{context} column")
            parts = [column["name"], column.get("type", "string")]
            if column.get("key"):
                parts.append(column["key"])
            lines.append(f'  {safe_alias(column["name"], "col")}: "{escape_label(" | ".join(parts))}"')
        else:
            lines.append(f'  {safe_alias(str(column), "col")}: "{escape_label(str(column))}"')
    lines.append("}")
    return "\n".join(lines)


def append_d2_tree(lines: list[str], node: dict, depth: int):
    require_fields(node, ["name"], "tree node")
    indent = "  " * depth
    label = escape_label(node["name"])
    children = node.get("children", [])
    if children:
        lines.append(f'{indent}"{label}": {{')
        for child in children:
            append_d2_tree(lines, child, depth + 1)
        lines.append(f"{indent}}}")
    else:
        lines.append(f'{indent}"{label}"')


def build_d2_tree_diagram(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    root = diagram.get("root")
    if not isinstance(root, dict):
        raise SystemExit(f"{context} requires object field: root")
    lines = []
    append_d2_tree(lines, root, 0)
    return "\n".join(lines)


def build_plantuml_use_case(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    actors = require_list(diagram, "actors", context)
    use_cases = require_list(diagram, "use_cases", context)
    associations = require_list(diagram, "associations", context)
    actor_alias = {}
    case_alias = {}
    lines = ["@startuml", "skinparam backgroundColor transparent", "left to right direction"]
    if diagram.get("title"):
        lines.append(f"title {plain_text(diagram['title'])}")
    for actor in actors:
        require_fields(actor, ["name"], f"{context} actor")
        alias = safe_alias(actor.get("id", actor["name"]), "actor")
        actor_alias[actor["name"]] = alias
        lines.append(f'actor "{escape_label(actor["name"])}" as {alias}')
    for use_case in use_cases:
        require_fields(use_case, ["name"], f"{context} use case")
        alias = safe_alias(use_case.get("id", use_case["name"]), "uc")
        case_alias[use_case["name"]] = alias
        lines.append(f'usecase "{escape_label(use_case["name"])}" as {alias}')
    for association in associations:
        require_fields(association, ["from", "to"], f"{context} association")
        source = actor_alias.get(association["from"], case_alias.get(association["from"]))
        target = actor_alias.get(association["to"], case_alias.get(association["to"]))
        if not source or not target:
            raise SystemExit(f"{context} association references unknown element: {association['from']} -> {association['to']}")
        arrow = association.get("type", "-->")
        label = str(association.get("label", "")).strip()
        if label:
            lines.append(f"{source} {arrow} {target} : {escape_label(label)}")
        else:
            lines.append(f"{source} {arrow} {target}")
    lines.append("@enduml")
    return "\n".join(lines)


def build_plantuml_class(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    classes = require_list(diagram, "classes", context)
    relations = require_list(diagram, "relations", context)
    alias_map = {}
    lines = ["@startuml", "skinparam backgroundColor transparent"]
    if diagram.get("title"):
        lines.append(f"title {plain_text(diagram['title'])}")
    for item in classes:
        require_fields(item, ["name"], f"{context} class")
        alias = safe_alias(item.get("id", item["name"]), "cls")
        alias_map[item["name"]] = alias
        class_type = item.get("type", "class")
        lines.append(f'{class_type} "{escape_label(item["name"])}" as {alias} {{')
        for field in item.get("fields", []):
            lines.append(f"  {field}")
        for method in item.get("methods", []):
            lines.append(f"  {method}")
        lines.append("}")
    for relation in relations:
        require_fields(relation, ["from", "to"], f"{context} relation")
        if relation["from"] not in alias_map or relation["to"] not in alias_map:
            raise SystemExit(f"{context} relation references unknown class: {relation['from']} -> {relation['to']}")
        rel_type = relation.get("type", "-->")
        relation_core = f'{alias_map[relation["from"]]} {rel_type} {alias_map[relation["to"]]}'
        rel_parts = str(rel_type).split()
        if len(rel_parts) == 3 and ("-" in rel_parts[1] or "." in rel_parts[1]):
            relation_core = f'{alias_map[relation["from"]]} "{rel_parts[0]}" {rel_parts[1]} "{rel_parts[2]}" {alias_map[relation["to"]]}'
        label = str(relation.get("label", "")).strip()
        if label:
            lines.append(f"{relation_core} : {escape_label(label)}")
        else:
            lines.append(relation_core)
    lines.append("@enduml")
    return "\n".join(lines)


def build_plantuml_sequence(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    participants = require_list(diagram, "participants", context)
    messages = require_list(diagram, "messages", context)
    alias_map = {}
    lines = ["@startuml", "skinparam backgroundColor transparent"]
    if diagram.get("title"):
        lines.append(f"title {plain_text(diagram['title'])}")
    for participant in participants:
        require_fields(participant, ["name"], f"{context} participant")
        alias = safe_alias(participant.get("id", participant["name"]), "p")
        alias_map[participant["name"]] = alias
        kind = participant.get("type", "participant")
        lines.append(f'{kind} "{escape_label(participant["name"])}" as {alias}')
    for message in messages:
        require_fields(message, ["from", "to", "label"], f"{context} message")
        if message["from"] not in alias_map or message["to"] not in alias_map:
            raise SystemExit(f"{context} message references unknown participant: {message['from']} -> {message['to']}")
        arrow = message.get("type", "->")
        lines.append(f'{alias_map[message["from"]]} {arrow} {alias_map[message["to"]]} : {escape_label(message["label"])}')
    lines.append("@enduml")
    return "\n".join(lines)


def build_plantuml_activity(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    actions = require_list(diagram, "actions", context)
    lines = ["@startuml", "skinparam backgroundColor transparent"]
    if diagram.get("title"):
        lines.append(f"title {plain_text(diagram['title'])}")
    lines.append("start")
    for action in actions:
        lines.append(f":{escape_label(str(action))};")
    lines.append("stop")
    lines.append("@enduml")
    return "\n".join(lines)


def build_plantuml_state(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    states = require_list(diagram, "states", context)
    transitions = require_list(diagram, "transitions", context)
    alias_map = {}
    lines = ["@startuml", "skinparam backgroundColor transparent"]
    if diagram.get("title"):
        lines.append(f"title {plain_text(diagram['title'])}")
    for state in states:
        require_fields(state, ["name"], f"{context} state")
        alias = safe_alias(state.get("id", state["name"]), "state")
        alias_map[state["name"]] = alias
        lines.append(f'state "{escape_label(state["name"])}" as {alias}')
    for transition in transitions:
        require_fields(transition, ["from", "to"], f"{context} transition")
        source = "[*]" if transition["from"] == "[*]" else alias_map.get(transition["from"])
        target = "[*]" if transition["to"] == "[*]" else alias_map.get(transition["to"])
        if not source or not target:
            raise SystemExit(f"{context} transition references unknown state: {transition['from']} -> {transition['to']}")
        label = str(transition.get("label", "")).strip()
        if label:
            lines.append(f"{source} --> {target} : {escape_label(label)}")
        else:
            lines.append(f"{source} --> {target}")
    lines.append("@enduml")
    return "\n".join(lines)


def build_plantuml_component(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    components = require_list(diagram, "components", context)
    dependencies = require_list(diagram, "dependencies", context)
    alias_map = {}
    lines = ["@startuml", "skinparam backgroundColor transparent"]
    if diagram.get("title"):
        lines.append(f"title {plain_text(diagram['title'])}")
    for component in components:
        require_fields(component, ["name"], f"{context} component")
        alias = safe_alias(component.get("id", component["name"]), "cmp")
        alias_map[component["name"]] = alias
        keyword = component.get("type", "component")
        lines.append(f'{keyword} "{escape_label(component["name"])}" as {alias}')
    for dependency in dependencies:
        require_fields(dependency, ["from", "to"], f"{context} dependency")
        if dependency["from"] not in alias_map or dependency["to"] not in alias_map:
            raise SystemExit(f"{context} dependency references unknown component: {dependency['from']} -> {dependency['to']}")
        arrow = dependency.get("type", "-->")
        label = str(dependency.get("label", "")).strip()
        if label:
            lines.append(f'{alias_map[dependency["from"]]} {arrow} {alias_map[dependency["to"]]} : {escape_label(label)}')
        else:
            lines.append(f'{alias_map[dependency["from"]]} {arrow} {alias_map[dependency["to"]]}')
    lines.append("@enduml")
    return "\n".join(lines)


def build_plantuml_deployment(diagram: dict) -> str:
    context = f"diagram '{diagram.get('name', '<unnamed>')}' ({diagram.get('kind')})"
    nodes = require_list(diagram, "nodes", context)
    connections = require_list(diagram, "connections", context)
    alias_map = {}
    lines = ["@startuml", "skinparam backgroundColor transparent"]
    if diagram.get("title"):
        lines.append(f"title {plain_text(diagram['title'])}")
    for node in nodes:
        require_fields(node, ["name"], f"{context} deployment node")
        alias = safe_alias(node.get("id", node["name"]), "dep")
        alias_map[node["name"]] = alias
        keyword = node.get("type", "node")
        lines.append(f'{keyword} "{escape_label(node["name"])}" as {alias}')
    for connection in connections:
        require_fields(connection, ["from", "to"], f"{context} deployment connection")
        if connection["from"] not in alias_map or connection["to"] not in alias_map:
            raise SystemExit(f"{context} deployment connection references unknown node: {connection['from']} -> {connection['to']}")
        arrow = connection.get("type", "-->")
        label = str(connection.get("label", "")).strip()
        if label:
            lines.append(f'{alias_map[connection["from"]]} {arrow} {alias_map[connection["to"]]} : {escape_label(label)}')
        else:
            lines.append(f'{alias_map[connection["from"]]} {arrow} {alias_map[connection["to"]]}')
    lines.append("@enduml")
    return "\n".join(lines)


def build_plantuml_generic(diagram: dict) -> str:
    if diagram.get("participants") and diagram.get("messages"):
        return build_plantuml_sequence(diagram)
    if diagram.get("classes") and diagram.get("relations"):
        return build_plantuml_class(diagram)
    if diagram.get("components") and diagram.get("dependencies"):
        return build_plantuml_component(diagram)
    raise SystemExit(f"diagram '{diagram.get('name', '<unnamed>')}' (uml_diagram) needs sequence/class/component style fields")


def build_source(diagram: dict) -> tuple[str, str]:
    kind = diagram.get("kind")
    if kind not in RENDERER_MAP:
        supported = ", ".join(sorted(RENDERER_MAP))
        raise SystemExit(f"Unsupported diagram kind: {kind}. Supported kinds: {supported}")
    renderer = RENDERER_MAP[kind]
    if renderer == "mermaid":
        if kind == "er_diagram":
            return build_mermaid_er(diagram), ".mmd"
        if kind == "mindmap":
            return build_mermaid_mindmap(diagram), ".mmd"
        if kind == "timeline":
            return build_mermaid_timeline(diagram), ".mmd"
        if kind == "gantt_chart":
            return build_mermaid_gantt(diagram), ".mmd"
        return build_mermaid_flowchart(diagram), ".mmd"
    if renderer == "d2":
        if kind == "data_flow_diagram":
            return build_d2_dfd(diagram), ".d2"
        if kind == "database_schema_diagram":
            return build_d2_database_schema(diagram), ".d2"
        if kind == "table_structure_diagram":
            return build_d2_table_structure(diagram), ".d2"
        if kind in {"wbs_diagram", "file_tree_diagram"}:
            return build_d2_tree_diagram(diagram), ".d2"
        return build_d2_node_edge_diagram(diagram), ".d2"
    if kind == "use_case_diagram":
        return build_plantuml_use_case(diagram), ".puml"
    if kind == "class_diagram":
        return build_plantuml_class(diagram), ".puml"
    if kind == "sequence_diagram":
        return build_plantuml_sequence(diagram), ".puml"
    if kind == "activity_diagram":
        return build_plantuml_activity(diagram), ".puml"
    if kind == "state_diagram":
        return build_plantuml_state(diagram), ".puml"
    if kind == "component_diagram":
        return build_plantuml_component(diagram), ".puml"
    if kind == "deployment_diagram":
        return build_plantuml_deployment(diagram), ".puml"
    return build_plantuml_generic(diagram), ".puml"


def resolve_executable(renderer: str) -> str | None:
    for candidate in EXECUTABLE_CANDIDATES[renderer]:
        hit = shutil.which(candidate)
        if hit:
            return hit
    return None


def run_command(command: list[str], description: str, cwd: Path | None = None):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd) if cwd else None,
    )
    if result.returncode != 0:
        details = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        raise SystemExit(f"{description} failed.\nCommand: {' '.join(command)}\n{details}".rstrip())


def render_mermaid(executable: str, source_path: Path, svg_path: Path, png_path: Path):
    run_command([executable, "-i", str(source_path), "-o", str(svg_path), "-b", "transparent"], "Mermaid SVG render")
    run_command([executable, "-i", str(source_path), "-o", str(png_path), "-b", "white"], "Mermaid PNG render")


def render_d2(executable: str, source_path: Path, svg_path: Path, png_path: Path):
    run_command([executable, str(source_path), str(svg_path)], "D2 SVG render")
    run_command([executable, str(source_path), str(png_path)], "D2 PNG render")


def render_plantuml(executable: str, source_path: Path, svg_path: Path, png_path: Path):
    run_command([executable, "-charset", "UTF-8", "-tsvg", source_path.name], "PlantUML SVG render", cwd=source_path.parent)
    run_command([executable, "-charset", "UTF-8", "-tpng", source_path.name], "PlantUML PNG render", cwd=source_path.parent)
    expected_svg = source_path.with_suffix(".svg")
    expected_png = source_path.with_suffix(".png")
    if expected_svg.exists() and expected_svg != svg_path:
        expected_svg.replace(svg_path)
    if expected_png.exists() and expected_png != png_path:
        expected_png.replace(png_path)


def render_source(renderer: str, source_path: Path, svg_path: Path, png_path: Path):
    executable = resolve_executable(renderer)
    if not executable:
        raise SystemExit(
            f"Missing renderer for {renderer}. {INSTALL_HINTS[renderer]}\n"
            f"Source file has been written to: {source_path}"
        )
    if renderer == "mermaid":
        render_mermaid(executable, source_path, svg_path, png_path)
    elif renderer == "d2":
        render_d2(executable, source_path, svg_path, png_path)
    else:
        render_plantuml(executable, source_path, svg_path, png_path)


def check_environment() -> int:
    missing = []
    for renderer in ("mermaid", "d2", "plantuml"):
        executable = resolve_executable(renderer)
        if executable:
            print(f"[OK] {renderer}: {executable}")
        else:
            missing.append(renderer)
            print(f"[WARN] {renderer}: missing")
            print(f"       {INSTALL_HINTS[renderer]}")
    return 0 if not missing else 1


def main():
    args = parse_args()
    if args.check:
        sys.exit(check_environment())

    workflow = load_json(Path(args.workflow).expanduser().resolve())
    diagram_plan = load_json(Path(workflow["diagram_plan_path"]))
    output_dir = Path(workflow["images_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    if not diagram_plan.get("enabled", False):
        raise SystemExit("diagram_plan.json is not enabled")

    diagrams = diagram_plan.get("diagrams", [])
    if not diagrams:
        raise SystemExit("diagram_plan.json has no diagrams")

    generated = []
    for diagram in diagrams:
        name = diagram.get("name")
        if not name:
            raise SystemExit("Each diagram entry must include a name")
        source_text, extension = build_source(diagram)
        source_path = output_dir / f"{name}{extension}"
        svg_path = output_dir / f"{name}.svg"
        png_path = output_dir / f"{name}.png"
        renderer = RENDERER_MAP[diagram["kind"]]
        write_text(source_path, source_text)
        render_source(renderer, source_path, svg_path, png_path)
        generated.append(
            {
                "name": name,
                "kind": diagram["kind"],
                "renderer": renderer,
                "source": str(source_path),
                "svg": str(svg_path),
                "png": str(png_path),
            }
        )
        print(f"Generated diagram asset: {png_path}")
        print(f"Generated diagram source: {source_path}")

    report_path = output_dir / "diagram_generation_report.json"
    report_path.write_text(json.dumps({"generated": generated}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Diagram report: {report_path}")


if __name__ == "__main__":
    main()
