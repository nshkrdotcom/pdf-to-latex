# persistence_layer.py (Neo4j Interactions)

from py2neo import Graph, Node, Relationship

class Neo4jPersistence:
    def __init__(self, uri, username, password):
        self.graph = Graph(uri, auth=(username, password))

    def create_document_node(self, doc_id, filename):
        """Creates a Document node in Neo4j."""
        node = Node("Document", doc_id=doc_id, filename=filename)
        self.graph.create(node)
        return node

    def create_page_node(self, page_id, doc_id, page_number, width, height):
        """Creates a Page node and links it to a Document."""
        page_node = Node("Page", page_id=page_id, doc_id=doc_id, page_number=page_number, width=width, height=height)
        doc_node = self.graph.nodes.match("Document", doc_id=doc_id).first()
        if doc_node:
            self.graph.create(Relationship(doc_node, "CONTAINS", page_node))
        return page_node

    def create_block_node(self, block_id, page_id, block_type, x, y, width, height, **kwargs):  # Updated
        """Creates a Block node and links it to a Page."""
        block_node = Node("Block", block_id=block_id, page_id=page_id, block_type=block_type, x=x, y=y, width=width, height=height, **kwargs)  # Include additional properties
        page_node = self.graph.nodes.match("Page", page_id=page_id).first()
        if page_node:
            self.graph.create(Relationship(page_node, "CONTAINS", block_node))
        return block_node

    def create_follows_relationship(self, block_id1, block_id2):
        """Creates a FOLLOWS relationship between two blocks."""
        block1 = self.graph.nodes.match("Block", block_id=block_id1).first()
        block2 = self.graph.nodes.match("Block", block_id=block_id2).first()
        if block1 and block2:
            self.graph.create(Relationship(block1, "FOLLOWS", block2))


    # ... (Add other methods for creating relationships, querying, etc.)

    def clear_database(self): # Added this helper to clear the DB
        self.graph.delete_all()


# Example usage (in your main pipeline script)

# ... (Get database credentials from configuration)
neo4j_persistence = Neo4jPersistence(uri, username, password) # Replace with actual DB config

# clear the DB.
neo4j_persistence.clear_database() # Replace with actual DB config

# Example: Create a document and a page
doc_node = neo4j_persistence.create_document_node(1, "my_document.pdf")
page_node = neo4j_persistence.create_page_node(1, 1, 1, 8.5, 11)

# Example: Create some blocks and a FOLLOWS relationship. text_content is passed as **kwargs in this example
block1 = neo4j_persistence.create_block_node(1, 1, "text", 10, 10, 200, 50, text_content="This is the first block.") # Example usage of **kwargs
block2 = neo4j_persistence.create_block_node(2, 1, "image", 10, 70, 300, 200)

neo4j_persistence.create_follows_relationship(1, 2)


# ... (Rest of your pipeline logic)







# persistence_layer.py

import psycopg2  # PostgreSQL library
from py2neo import Graph, Node, Relationship


class PersistenceLayer:
    def __init__(self, pg_conn_str, neo4j_uri, neo4j_username, neo4j_password):
        self.pg_conn = psycopg2.connect(pg_conn_str)
        self.pg_cursor = self.pg_conn.cursor()
        self.neo4j_graph = Graph(neo4j_uri, auth=(neo4j_username, neo4j_password))

    def _pg_execute(self, query, params=None): # Helper to avoid repetition
        try:
            self.pg_cursor.execute(query, params)
            self.pg_conn.commit()
        except psycopg2.Error as e:
            self.pg_conn.rollback() # Handle errors properly. Important!
            raise e # Reraise for now so you see it. Better to log it.

    def create_document(self, filename, source_pdf=None):
        """Creates a document entry in PostgreSQL and a corresponding node in Neo4j."""
        query = "INSERT INTO Documents (filename, source_pdf) VALUES (%s, %s) RETURNING doc_id;"
        self._pg_execute(query, (filename, source_pdf))  # Use parameterized query
        doc_id = self.pg_cursor.fetchone()[0]

        neo4j_node = Node("Document", doc_id=doc_id, filename=filename)
        self.neo4j_graph.create(neo4j_node)
        return doc_id



    def create_page(self, doc_id, page_number, width, height):
        """Creates a page entry in PostgreSQL and a node in Neo4j, linked to the document."""
        query = "INSERT INTO Pages (doc_id, page_number, width, height) VALUES (%s, %s, %s, %s) RETURNING page_id;"
        self._pg_execute(query, (doc_id, page_number, width, height))
        page_id = self.pg_cursor.fetchone()[0]

        neo4j_node = Node("Page", page_id=page_id, doc_id=doc_id, page_number=page_number, width=width, height=height)
        doc_node = self.neo4j_graph.nodes.match("Document", doc_id=doc_id).first()
        self.neo4j_graph.create(Relationship(doc_node, "CONTAINS", neo4j_node)) # Assuming doc_node exists
        return page_id

    def create_block(self, page_id, block_type, x, y, width, height, **kwargs):  # Flexible kwargs
        """Creates a block entry in PostgreSQL and a node in Neo4j, linked to the page."""
        query = "INSERT INTO Blocks (page_id, block_type, x, y, width, height) VALUES (%s, %s, %s, %s, %s, %s) RETURNING block_id;"
        self._pg_execute(query, (page_id, block_type, x, y, width, height))
        block_id = self.pg_cursor.fetchone()[0]

        # Dynamically add properties to Neo4j node based on kwargs
        neo4j_props = {"block_id": block_id, "page_id": page_id, "block_type": block_type, "x": x, "y": y, "width": width, "height": height}
        neo4j_props.update(kwargs) # Handles additional block specific attributes. very important
        neo4j_node = Node("Block", **neo4j_props)
        page_node = self.neo4j_graph.nodes.match("Page", page_id=page_id).first()
        self.neo4j_graph.create(Relationship(page_node, "CONTAINS", neo4j_node))  # Assuming page_node exists

        # Handle specific block types in PostgreSQL (using separate tables for now)
        if block_type == "text":
            # ... insert into TextBlocks table ...
            pass # Implement specific insertion logic in a moment.
        elif block_type == "image":
            # ... insert into ImageBlocks table ...
            pass
        # ... (handle other block types) ...
        return block_id

    def create_follows_relationship(self, block_id1, block_id2): # Neo4j only
        """Creates a FOLLOWS relationship between two blocks in Neo4j."""
        block1 = self.neo4j_graph.nodes.match("Block", block_id=block_id1).first()
        block2 = self.neo4j_graph.nodes.match("Block", block_id=block_id2).first()
        self.neo4j_graph.create(Relationship(block1, "FOLLOWS", block2))  # Assuming both nodes exist

    # ... (Add other methods for creating relationships, querying data, etc.)

    def close(self):  # Clean up resources MUST DO
        self.pg_cursor.close()
        self.pg_conn.close()
