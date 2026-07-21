import sys

sys.path.insert(0, "/opt/AgentCore/backend/services/code-graph-service/src")
from code_graph_service.neo4j_store import Neo4jStore, _lucene_query
from code_graph_service.neo4j.store import Neo4jStore as S2

print("ok", Neo4jStore is S2, _lucene_query("ab cdefg"))
print("methods", hasattr(Neo4jStore, "wipe_scope"), hasattr(Neo4jStore, "rank_symbols_by_degree"))
