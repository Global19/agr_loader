from .mod import MOD

class RGD(MOD):

    def __init__(self):
        self.species = "Rattus norvegicus"
        self.loadFile = "RGD_1.0.0.2_5.tar.gz"
        self.bgiName = "/RGD_1.0.0.2_BGI.10116.json"
        self.diseaseName = "/RGD_1.0.0.2_disease.10116.json"
        self.alleleName = "/RGD_1.0.0.2_feature.10116.json"
        self.geneAssociationFile = "gene_association_1.0.rgd.gz"
        self.identifierPrefix = "RGD:"
        self.geoSpecies = "Rattus+norvegicus"

    def load_genes(self, batch_size, testObject, graph):
        data = MOD.load_genes_mod(self, batch_size, testObject, self.bgiName, self.loadFile, graph)
        return data

    @staticmethod
    def gene_href(gene_id):
        return "http://www.rgd.mcw.edu/rgdweb/report/gene/main.html?id=" + gene_id

    @staticmethod
    def get_organism_names():
        return ["Rattus norvegicus", "R. norvegicus", "RAT"]

    def extract_go_annots(self, testObject):
        go_annot_list = MOD.extract_go_annots_mod(self, self.geneAssociationFile, self.species, self.identifierPrefix, testObject)
        return go_annot_list

    def load_disease_gene_objects(self, batch_size, testObject):
        data = MOD.load_disease_gene_objects_mod(self, batch_size, testObject, self.diseaseName, self.loadFile)
        return data

    def load_disease_allele_objects(self, batch_size, testObject, graph):
        data = MOD.load_disease_allele_objects_mod(self, batch_size, testObject, self.diseaseName, self.loadFile, graph)
        return data

    def load_allele_objects(self, batch_size, testObject, graph):
        data = MOD.load_allele_objects_mod(self, batch_size, testObject, self.alleleName, self.loadFile, graph)
        return data

    def extract_geo_entrez_ids(self):
        entrezIds = MOD.extract_entrez_ids_from_geo(self.geoSpecies)
        return entrezIds

    def extract_geo_entrez_ids(self):
        entrezIds = MOD.extract_entrez_ids_from_geo(self.geoSpecies)
        return entrezIds