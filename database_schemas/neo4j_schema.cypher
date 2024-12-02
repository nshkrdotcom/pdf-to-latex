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
content_copy
Use code with caution.
Python

Neo4j Setup Procedure

Installation: Download and install Neo4j Desktop or Neo4j Server Community Edition (for production).

Create a Database: In Neo4j Desktop, create a new project and add a local DBMS. Alternatively, if you are using Neo4j Server, a database will be created when the server starts.

Connect to the Database: Note the connection details (URI, username, password). The default uri is usually bolt://localhost:7687. The default username is neo4j, and the default password you will have set during the installation process.

Create Constraints (Important): Connect to your Neo4j database (using the Neo4j Browser or a Python driver) and execute the Cypher commands from the schema file to create the uniqueness constraints:

CREATE CONSTRAINT doc_id_unique ON (d:Document) ASSERT d.doc_id IS UNIQUE;
CREATE CONSTRAINT page_id_unique ON (p:Page) ASSERT p.page_id IS UNIQUE;
CREATE CONSTRAINT block_id_unique ON (b:Block) ASSERT b.block_id IS UNIQUE;
content_copy
Use code with caution.
Cypher

Integrate with your Python Code: Use the py2neo library in your Python code to connect to the database and interact with it (as shown in the persistence_layer.py example).

Key improvements in persistence_layer.py:

**kwargs for create_block_node: The create_block_node function now accepts **kwargs. This allows you to pass additional properties to the block nodes dynamically, such as text_content, font_family, etc., depending on the block_type. This makes the function much more flexible.

Clearer Example: The example usage is more complete and shows how to create nodes and a relationship.

clear_database() function: A helper function to clear all nodes and relationships in the database was added. This is useful for testing and resetting the database to a clean state.

Error Handling (Important – Add this): The provided code lacks robust error handling. You must add error handling (e.g., try...except blocks) to gracefully handle potential issues like connection errors, invalid queries, or data integrity violations.

This improved code and setup procedure provide a better starting point for interacting with Neo4j in your PDF-to-LaTeX pipeline. Remember to tailor the schema, code, and setup to your specific needs, and always prioritize robust error handling and data validation.
