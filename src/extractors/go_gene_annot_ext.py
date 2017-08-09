from .test_check import check_for_test_entry
class GOGeneAnnot:

    def __init__(self, annots, go_data, batch_size, test_set):
        self.go_blacklist = ("GO:0008150", "GO:0003674", "GO:0005575")
        self.annots = annots
        self.go = go_data

    def attach_annotations(self, genes, batch_size, test_set):
        list_to_yield = []
        for annot in self.annots:

            go_id = annot['go_id']
            gene_id = annot['gene_id']

            if go_id not in self.go_blacklist and gene_id in check_for_test_entry(gene_id):
                go_type = self.go[go_id]["go_type"]
                term_name = self.go[go_id]["name"]

                if term_name not in genes[gene_id]["gene_" + go_type]:
                      genes[gene_id]["gene_" + go_type].append(term_name)

