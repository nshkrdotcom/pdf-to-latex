-- PostgreSQL Schema (pdf_to_latex_db)

CREATE TABLE Documents (
    doc_id SERIAL PRIMARY KEY,
    filename TEXT,
    source_pdf BYTEA
);

CREATE TABLE Pages (
    page_id SERIAL PRIMARY KEY,
    doc_id INTEGER REFERENCES Documents(doc_id),
    page_number INTEGER,
    width FLOAT,
    height FLOAT
);

CREATE TABLE Blocks (
    block_id SERIAL PRIMARY KEY,
    page_id INTEGER REFERENCES Pages(page_id),
    block_type TEXT,  -- 'text', 'image', 'table', 'equation'
    x FLOAT,
    y FLOAT,
    width FLOAT,
    height FLOAT
);

CREATE TABLE TextBlocks (
    block_id INTEGER PRIMARY KEY REFERENCES Blocks(block_id),
    text_content TEXT,
    font_family TEXT,
    font_size FLOAT,
    style TEXT -- 'bold', 'italic', etc.
);

CREATE TABLE ImageBlocks (
    block_id INTEGER PRIMARY KEY REFERENCES Blocks(block_id),
    image_data BYTEA
);

CREATE TABLE Tables (
    table_id SERIAL PRIMARY KEY,
    block_id INTEGER REFERENCES Blocks(block_id)
    -- Add columns for table structure (rows, columns, cells) as needed
);

CREATE TABLE Equations (
    equation_id SERIAL PRIMARY KEY,
    block_id INTEGER REFERENCES Blocks(block_id),
    latex_representation TEXT,
    mathml_representation TEXT  -- Optional
);


-- Neo4j Schema (pdf_to_latex_graph)

-- Node labels: Document, Page, Block
-- Properties on nodes will match the corresponding PostgreSQL tables.
-- Relationships:
--     (Document)-[:CONTAINS]->(Page)
--     (Page)-[:CONTAINS]->(Block)
--     (Block)-[:FOLLOWS]->(Block)  -- For reading order
--     (Block)-[:REFERS_TO]->(Block) -- For cross-references, etc.


-- Example of creating constraints in Neo4j (using Cypher):

CREATE CONSTRAINT doc_id_unique ON (d:Document) ASSERT d.doc_id IS UNIQUE;
CREATE CONSTRAINT page_id_unique ON (p:Page) ASSERT p.page_id IS UNIQUE;
CREATE CONSTRAINT block_id_unique ON (b:Block) ASSERT b.block_id IS UNIQUE;
