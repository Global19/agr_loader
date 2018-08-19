import os

from loaders import *
from loaders.transactions import *
from loaders.allele_loader import *
from loaders.disease_loader import *
from loaders.geo_loader import *
from loaders.phenotype_loader import *
from loaders.wt_expression_loader import *
from loaders.resource_descriptor_loader import *
from loaders.generic_anatomical_structure_ontology_loader import *
from mods import *
from extractors import *
from extractors.ontology_extractor import *
from test import *
import time
from neo4j.v1 import GraphDatabase
from genedescriptions.config_parser import GenedescConfigParser
from genedescriptions.descriptions_writer import GeneDesc, JsonGDWriter
from test import TestObject
from services.gene_descriptions.descriptions_writer import Neo4jGDWriter
from services.gene_descriptions.descriptions_generator import GeneDescGenerator


class AggregateLoader(object):
    def __init__(self, uri, useTestObject):
        self.graph = GraphDatabase.driver(uri, auth=("neo4j", "neo4j"))
        # Set size of BGI, disease batches extracted from MOD JSON file
        # for creating Python data structure.
        self.batch_size = 5000
        self.mods = [MGI(), Human(), RGD(), SGD(), WormBase(), ZFIN(), FlyBase()]
        #self.mods = [ZFIN()]
        self.testObject = TestObject(useTestObject, self.mods)
        self.dataset = {}

        self.resourceDescriptors = ""
        self.geoMoEntrezIds = ""

        # Check for the use of test data.
        if self.testObject.using_test_data() == True:
            print("WARNING: Test data load enabled.")
            time.sleep(1)

    def create_indices(self):
        print("Creating indices.")
        Indicies(self.graph).create_indices()

    def load_resource_descriptors(self):
        print("extracting resource descriptor")
        self.resourceDescriptors = ResourceDescriptor().get_data()
        print("loading resource descriptor")
        ResourceDescriptorLoader(self.graph).load_resource_descriptor(self.resourceDescriptors)

    #TODO load_from_ontologies could be consolidated into this method, perhaps
    def load_from_ont(self, ontology_path, ontology_to_load, obo_file_name):
        print ("Extraction % data", ontology_to_load)
        self.dataset = OExt().get_data(ontology_path, obo_file_name)
        print("Loading % data into Neo4j.", ontology_to_load)
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.dataset, ontology_to_load+"TERM")

    def load_from_ontologies(self):
        print("Extracting SO data.")
        self.so_dataset = SOExt().get_data()
        print("Extracting GO data.")
        self.go_dataset = OExt().get_data("http://snapshot.geneontology.org/ontology/go.obo", "go.obo")
        print("Extracting DO data.")
        self.do_dataset = OExt().get_data("http://purl.obolibrary.org/obo/doid.obo", "doid.obo")
        #
        # # structure ontologies
        print("Extracting ZFA data.")
        self.zfa_dataset = OExt().get_data("http://purl.obolibrary.org/obo/zfa.obo", "zfa.obo")
        print("Extracting ZFS data.")
        self.zfs_dataset = OExt().get_data("http://purl.obolibrary.org/obo/zfs.obo", "zfs.obo")
        print("Extracting WBBT data.")
        self.wbbt_dataset = OExt().get_data("http://purl.obolibrary.org/obo/wbbt.obo", "wbbt.obo")
        print("Extracting Cell data.")
        self.cell_dataset = OExt().get_data("http://purl.obolibrary.org/obo/cl.obo", "cl.obo")
        print("Extracting FBDV data.")
        self.fbdv_dataset = OExt().get_data("http://purl.obolibrary.org/obo/fbdv.obo", "fbdv-simple.obo")
        print("Extracting FBBT data.")
        self.fbbt_dataset = OExt().get_data("http://purl.obolibrary.org/obo/fbbt.obo", "fbbt.obo")
        print("Extracting FBCV data.")
        self.fbcv_dataset = OExt().get_data("http://purl.obolibrary.org/obo/fbcv.obo", "fbcv.obo")
        print("Extracting MA data.")
        self.ma_dataset = OExt().get_data("http://www.informatics.jax.org/downloads/reports/adult_mouse_anatomy.obo", "ma.obo")
        print("Extracting EMAPA data.")
        self.emapa_dataset = OExt().get_data("http://purl.obolibrary.org/obo/emapa.obo", "emapa.obo")
        print("Extracting UBERON data.")
        self.uberon_dataset = OExt().get_data("http://ontologies.berkeleybop.org/uberon/basic.obo", "basic.obo")
        print("Extracting FBCV data.")
        self.fbcv_dataset = OExt().get_data("http://purl.obolibrary.org/obo/fbcv.obo", "fbcv.obo")
        print("Extracting MMUSDV data.")
        self.mmusdv_dataset = OExt().get_data("http://purl.obolibrary.org/obo/mmusdv.obo", "mmusdv.obo")
        print("Extracting BPSO data.")
        self.bspo_dataset = OExt().get_data("http://purl.obolibrary.org/obo/bspo.obo", "bpso.obo")
        print("Extracting MMO data.")
        self.mmo_dataset = OExt().get_data("http://purl.obolibrary.org/obo/mmo.obo", "mmo.obo")
        print("Extracting WBLS data.")
        self.wbls_dataset = OExt().get_data("http://purl.obolibrary.org/obo/wbls.obo", "wbls.obo")

        print("Downloading MI data.")
        self.mi_dataset = MIExt().get_data()

        print("Loading MI data into Neo4j.")
        MILoader(self.graph).load_mi(self.mi_dataset)
        print("Loading SO data into Neo4j.")
        SOLoader(self.graph).load_so(self.so_dataset)
        print("Loading GO data into Neo4j.")
        GOLoader(self.graph).load_go(self.go_dataset)
        print("Loading DO data into Neo4j.")
        DOLoader(self.graph).load_do(self.do_dataset)

        print("Loading ZFA data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.zfa_dataset, "ZFATerm")
        print("Loading ZFS data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.zfs_dataset, "ZFSTerm")
        print("Loading WBBT data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.wbbt_dataset, "WBBTTerm")
        print("Loading CL data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.cell_dataset, "CLTerm")
        #print("Loading FBDV data into Neo4j.")
        #GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.fbdv_dataset, "FBDVTerm")
        print("Loading FBBT data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.fbbt_dataset, "FBBTTerm")
        print("Loading FBCV data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.fbcv_dataset, "FBCVTerm")
        print("Loading MA data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.ma_dataset, "MATerm")
        print("Loading EMAPA data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.emapa_dataset, "EMAPATerm")
        print("Loading UBERON data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.uberon_dataset, "UBERONTerm")

        print("Loading FBCV data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.fbcv_dataset, "FBCVTerm")
        print("Loading MMUSDV data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.mmusdv_dataset, "MMUSDVTerm")
        print("Loading BPSO data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.bspo_dataset, "BSPOTerm")
        print("Loading MMO data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.mmo_dataset, "MMOTerm")
        print("Loading WBLS data into Neo4j.")
        GenericAnatomicalStructureOntologyLoader(self.graph).load_ontology(self.wbls_dataset, "WBLSTerm")

    def load_bgi(self, mod):
        genes = mod.load_genes(self.batch_size, self.testObject, self.graph, mod.species)  # generator object
        c = 0
        start = time.time()
        for gene_list_of_entries in genes:
            BGILoader(self.graph).load_bgi(gene_list_of_entries)
            c = c + len(gene_list_of_entries)
        end = time.time()
        print("Average: %sr/s" % (round(c / (end - start), 2)))

    def load_from_mods(self):
        print("Extracting BGI data from each MOD.")
        #
        for mod in self.mods:
             print("Loading BGI data for %s into Neo4j." % mod.species)
             genes = mod.load_genes(self.batch_size, self.testObject, self.graph, mod.species)  # generator object
             c = 0
             start = time.time()
             for gene_list_of_entries in genes:
                BGILoader(self.graph).load_bgi(gene_list_of_entries)
                c = c + len(gene_list_of_entries)
             end = time.time()
             print("Average: %sr/s" % (round(c / (end - start), 2)))

        this_dir = os.path.split(__file__)[0]
        #initialize gene description generator from config file
        genedesc_generator = GeneDescGenerator(config_file_path=os.path.join(this_dir, "services", "gene_descriptions",
                                                                          "genedesc_config.yml"),
                                               go_ontology=self.go_dataset, do_ontology=self.do_dataset,
                                               graph_db=self.graph)
        cached_data_fetcher = None
        #Loading annotation data for all MODs after completion of BGI data.

        for mod in self.mods:

            print("Loading MOD alleles for %s into Neo4j." % mod.species)
            alleles = mod.load_allele_objects(self.batch_size, self.testObject, mod.species)
            for allele_list_of_entries in alleles:
                AlleleLoader(self.graph).load_allele_objects(allele_list_of_entries)

            print("Loading MOD wt expression annotations for %s into Neo4j." % mod.species)
            xpats = mod.load_wt_expression_objects(self.batch_size, self.testObject, mod.species)
            for xpat_list_of_entries in xpats:
                WTExpressionLoader(self.graph).load_wt_expression_objects(xpat_list_of_entries, mod.species)
            #
            print("Loading MOD gene disease annotations for %s into Neo4j." % mod.species)
            features = mod.load_disease_gene_objects(2000, self.testObject, mod.species)
            for feature_list_of_entries in features:
                DiseaseLoader(self.graph).load_disease_gene_objects(feature_list_of_entries)

            print("Loading MOD allele disease annotations for %s into Neo4j." % mod.species)
            features = mod.load_disease_allele_objects(self.batch_size, self.testObject, self.graph, mod.species)
            for feature_list_of_entries in features:
                DiseaseLoader(self.graph).load_disease_allele_objects(feature_list_of_entries)

            print("Loading MOD phenotype annotations for %s into Neo4j." % mod.species)
            phenos = mod.load_phenotype_objects(self.batch_size, self.testObject, mod.species)
            for pheno_list_of_entries in phenos:
                PhenotypeLoader(self.graph).load_phenotype_objects(pheno_list_of_entries, mod.species)

            print("Loading Orthology data for %s into Neo4j." % mod.species)
            ortholog_data = OrthoExt().get_data(self.testObject, mod.__class__.__name__, self.batch_size) # generator object
            for ortholog_list_of_entries in ortholog_data:
                OrthoLoader(self.graph).load_ortho(ortholog_list_of_entries)

            print("Extracting GO annotations for %s." % mod.__class__.__name__)
            go_annots = mod.extract_go_annots(self.testObject)
            print("Loading GO annotations for %s into Neo4j." % mod.__class__.__name__)
            GOAnnotLoader(self.graph).load_go_annot(go_annots)

            print("Extracting GEO annotations for %s." % mod.__class__.__name__)
            geo_xrefs = mod.extract_geo_entrez_ids_from_geo(self.graph)
            print("Loading GEO annotations for %s." % mod.__class__.__name__)
            GeoLoader(self.graph).load_geo_xrefs(geo_xrefs)
            #
            print("generate gene descriptions for %s." % mod.__class__.__name__)
            if mod.dataProvider:
                cached_data_fetcher = genedesc_generator.generate_descriptions(
                    go_annotations=go_annots,
                    do_annotations=mod.load_disease_gene_objects(self.batch_size, self.testObject, mod.species),
                    do_annotations_allele=mod.load_disease_allele_objects(self.batch_size, self.testObject,
                                                                          self.graph, mod.species),
                    data_provider=mod.dataProvider, cached_data_fetcher=cached_data_fetcher,
                    human=isinstance(mod, Human))

    def load_additional_datasets(self):
            print("Extracting and Loading Molecular Interaction data.")
            mol_int_data = MolIntExt(self.graph).get_data(self.batch_size)
            for mol_int_list_of_entries in mol_int_data:
                MolIntLoader(self.graph).load_mol_int(mol_int_list_of_entries)