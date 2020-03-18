'''GO ETL'''

import logging
from ontobio import OntologyFactory
from etl import ETL
from transactors import CSVTransactor, Neo4jTransactor


class GOETL(ETL):
    '''GO ETL'''

    logger = logging.getLogger(__name__)

    query_template = """
        USING PERIODIC COMMIT %s
        LOAD CSV WITH HEADERS FROM \'file:///%s\' as row

        //Create the GOTerm node and set properties. primaryKey is required.
        CREATE (g:GOTerm:Ontology {primaryKey:row.oid})
            SET g.definition = row.definition,
             g.type = row.type,
             g.name = row.name ,
             g.subset = row.subset,
             g.nameKey = row.name_key,
             g.isObsolete = row.is_obsolete,
             g.href = row.href 
            MERGE (g)-[ggcg:IS_A_PART_OF_CLOSURE]->(g)"""

    goterm_isas_template = """
        USING PERIODIC COMMIT %s
        LOAD CSV WITH HEADERS FROM \'file:///%s\' AS row

            MATCH (g1:GOTerm {primaryKey:row.primary_id})
            MERGE (g2:GOTerm:Ontology {primaryKey:row.primary_id2})
            MERGE (g1)-[aka:IS_A]->(g2) """

    goterm_partofs_template = """
        USING PERIODIC COMMIT %s
        LOAD CSV WITH HEADERS FROM \'file:///%s\' AS row

            MATCH (g1:GOTerm {primaryKey:row.primary_id})
            MERGE (g2:GOTerm:Ontology {primaryKey:row.primary_id2})
            MERGE (g1)-[aka:PART_OF]->(g2) """

    goterm_synonyms_template = """
        USING PERIODIC COMMIT %s
        LOAD CSV WITH HEADERS FROM \'file:///%s\' AS row

            MATCH (g:GOTerm {primaryKey:row.primary_id})
            
            MERGE(syn:Synonym:Identifier {primaryKey:row.synonym})
                SET syn.name = row.synonym
            MERGE (g)-[aka2:ALSO_KNOWN_AS]->(syn) """

    goterm_regulates_template = """
        USING PERIODIC COMMIT %s
        LOAD CSV WITH HEADERS FROM \'file:///%s\' AS row

            MATCH (g1:GOTerm {primaryKey:row.primary_id})
            MERGE (g2:GOTerm:Ontology {primaryKey:row.primary_id2})
            MERGE (g1)-[aka:REGULATES]->(g2) """
    
    goterm_negatively_regulates_template = """
        USING PERIODIC COMMIT %s
        LOAD CSV WITH HEADERS FROM \'file:///%s\' AS row

            MATCH (g1:GOTerm {primaryKey:row.primary_id})
            MERGE (g2:GOTerm:Ontology {primaryKey:row.primary_id2})
            MERGE (g1)-[aka:NEGATIVELY_REGULATES]->(g2) """
            
    goterm_positively_regulates_template = """
        USING PERIODIC COMMIT %s
        LOAD CSV WITH HEADERS FROM \'file:///%s\' AS row

            MATCH (g1:GOTerm {primaryKey:row.primary_id})
            MERGE (g2:GOTerm:Ontology {primaryKey:row.primary_id2})
            MERGE (g1)-[aka:POSITIVELY_REGULATES]->(g2) """


    def __init__(self, config):
        super().__init__()
        self.data_type_config = config


    def _load_and_process_data(self):

        filepath = self.data_type_config.get_single_filepath()

        commit_size = self.data_type_config.get_neo4j_commit_size()
        batch_size = self.data_type_config.get_generator_batch_size()

        generators = self.get_generators(filepath, batch_size)

        query_list = [
            [GOETL.query_template, commit_size, "go_term_data.csv"],
            [GOETL.goterm_isas_template, commit_size, "go_isas_data.csv"],
            [GOETL.goterm_partofs_template, commit_size, "go_partofs_data.csv"],
            [GOETL.goterm_synonyms_template, commit_size, "go_synonym_data.csv"],
            [GOETL.goterm_regulates_template, commit_size, "go_regulates_data.csv"],
            [GOETL.goterm_negatively_regulates_template, commit_size, "go_negatively_regulates_data.csv"],
            [GOETL.goterm_positively_regulates_template, commit_size, "go_positively_regulates_data.csv"],
        ]

        query_and_file_list = self.process_query_params(query_list)
        CSVTransactor.save_file_static(generators, query_and_file_list)
        Neo4jTransactor.execute_query_batch(query_and_file_list)


    def get_generators(self, filepath, batch_size):
        '''Create Generators'''

        ont = OntologyFactory().create(filepath)
        parsed_line = ont.graph.copy().node

        go_term_list = []
        go_isas_list = []
        go_partofs_list = []
        go_synonyms_list = []
        go_regulates_list = []
        go_negatively_regulates_list = []
        go_positively_regulates_list = []
        counter = 0

        # Convert parsed obo term into a schema-friendly AGR dictionary.
        for key in parsed_line.items():
            counter = counter + 1
            node = ont.graph.node[key]
            if len(node) == 0:
                continue
            if node.get('type') == 'PROPERTY':
                continue

            ### Switching id to curie form and saving URI in "uri"
            ### might wildly break things later on???
            node["uri"] = node["id"]
            node["id"] = key

            subset = []
            definition = ""
            is_obsolete = "false"

            if "meta" in node:
                meta = node.get('meta')
                basic_property_values = meta.get('basicPropertyValues')
                for property_value_map in basic_property_values:
                    pred = property_value_map['pred']
                    val = property_value_map['val']
                    if pred == 'OIO:hasOBONamespace':
                        term_type = val
                if "synonyms" in node["meta"]:
                    syns = [s["val"] for s in node["meta"]["synonyms"]]
                    for synonym in syns:
                        go_synonym = {
                            "primary_id": key,
                            "synonym": synonym
                        }
                        go_synonyms_list.append(go_synonym)
                if node["meta"].get('is_obsolete'):
                    is_obsolete = "true"
                elif node["meta"].get('deprecated'):
                    is_obsolete = "true"
                if "definition" in node["meta"]:
                    definition = node["meta"]["definition"]["val"]
                if "subsets" in node["meta"]:
                    new_subset = node['meta'].get('subsets')
                    if isinstance(new_subset, (list, tuple)):
                        subset = new_subset
                    else:
                        if new_subset is not None:
                            subset.append(new_subset)
                if len(subset) > 1:
                    converted_subsets = []
                    for subset_str in subset:
                        if "#" in subset_str:
                            subset_str = subset_str.split("#")[-1]
                        converted_subsets.append(subset_str)
                    subset = converted_subsets

            all_parents = ont.parents(key)
            all_parents.append(key)

            # Improves performance when traversing relations
            all_parents_subont = ont.subontology(all_parents)
            isas_without_names = all_parents_subont.parents(key, relations=['subClassOf'])
            for item in isas_without_names:
                dictionary = {
                    "primary_id": key,
                    "primary_id2": item
                }
                go_isas_list.append(dictionary)

            partofs_without_names = all_parents_subont.parents(key, relations=['BFO:0000050'])
            for item in partofs_without_names:
                dictionary = {
                    "primary_id": key,
                    "primary_id2": item
                }
                go_partofs_list.append(dictionary)

            regulates = all_parents_subont.parents(key, relations=['RO:0002211'])

            for item in regulates:
                dictionary = {
                    "primary_id": key,
                    "primary_id2": item
                }
                go_regulates_list.append(dictionary)

            negatively_regulates = all_parents_subont.parents(key, relations=['RO:0002212'])
            for item in negatively_regulates:
                dictionary = {
                    "primary_id": key,
                    "primary_id2": item
                }
                go_negatively_regulates_list.append(dictionary)

            positively_regulates = all_parents_subont.parents(key, relations=['RO:0002213'])
            for item in positively_regulates:
                dictionary = {
                    "primary_id": key,
                    "primary_id2": item
                }
                go_positively_regulates_list.append(dictionary)


            dict_to_append = {
                'oid': key,
                'definition': definition,
                'type': term_type,
                'name': node.get('label'),
                'subset': subset,
                'name_key': node.get('label'),
                'is_obsolete': is_obsolete,
                'href': 'http://amigo.geneontology.org/amigo/term/' + node['id'],
            }

            go_term_list.append(dict_to_append)

            if counter == batch_size:
                yield [go_term_list,
                       go_isas_list,
                       go_partofs_list,
                       go_synonyms_list,
                       go_regulates_list,
                       go_negatively_regulates_list,
                       go_positively_regulates_list]
                go_term_list = []
                go_isas_list = []
                go_partofs_list = []
                go_synonyms_list = []
                go_regulates_list = []
                go_negatively_regulates_list = []
                go_positively_regulates_list = []
                counter = 0

        if counter > 0:
            yield [go_term_list,
                   go_isas_list,
                   go_partofs_list,
                   go_synonyms_list,
                   go_regulates_list,
                   go_negatively_regulates_list,
                   go_positively_regulates_list]
