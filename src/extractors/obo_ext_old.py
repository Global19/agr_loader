import uuid as id
from files import TXTFile, Download
from .obo_parser import parseOBO
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ObExto(object):

    def get_data(self, url, filename):

        savepath = "tmp";
        saved_path = Download(savepath, url, filename).download_file()
        o_data = TXTFile(saved_path).get_data()
        dict_to_append = {}
        parsed_line = parseOBO(o_data)
        list_to_return = []
        for line in parsed_line:  # Convert parsed obo term into a schema-friendly AGR dictionary.
            isasWithoutNames = []
            posWithoutNames = []
            o_syns = line.get('synonym')
            syns = []
            xrefs = []
            complete_url = None
            xref = None
            xref_urls = []
            local_id = None
            defLinksProcessed = []
            defText = None
            defLinks = []
            subset = []
            newSubset = None
            definition = ""
            is_obsolete = "false"
            ident = line['id']
            prefix = ident.split(":")[0]

            if syns is None:
                syns = []  # Set the synonyms to an empty array if None. Necessary for Neo4j parsing
            if o_syns is not None:
                if isinstance(o_syns, (list, tuple)):
                    for syn in o_syns:
                        syn = syn.split("\"")[1].strip()
                        syns.append(syn)
                else:
                    syn = o_syns.split("\"")[1].strip()
                    syns.append(syn)
            display_synonym = line.get('property_value')
            if display_synonym is not None:
                if isinstance(display_synonym, (list, tuple)):
                    display_synonym = display_synonym
                else:
                    if "DISPLAY_SYNONYM" in display_synonym:
                        display_synonym = display_synonym.split("\"")[1].strip()
                    else:
                        display_synonym = ""
            o_xrefs = line.get('xref')
            if o_xrefs is not None:
                if isinstance(o_xrefs, (list, tuple)):
                    for xrefId in o_xrefs:
                        if ":" in xrefId:
                            local_id = xrefId.split(":")[1].strip()
                            prefix = xrefId.split(":")[0].strip()
                            complete_url = self.get_complete_url_ont(local_id, xrefId)
                            uuid = str(id.uuid4())
                            xrefs.append(xref)
                            xref_urls.append({"uuid": uuid, "displayName": prefix+":"+local_id,
                                              "globalCrossRefId": prefix+":"+local_id,
                                              "primaryKey": prefix + ":" +local_id+ "ontology_provided_cross_reference",
                                              "oid": line['id'], "xrefId": xrefId, "local_id": local_id,
                                              "prefix": prefix, "crossRefCompleteUrl": complete_url,
                                              "complete_url": complete_url,
                                              "crossRefType": "ontology_provided_cross_reference"})
                else:
                    if ":" in o_xrefs:
                        local_id = o_xrefs.split(":")[1].strip()
                        prefix = o_xrefs.split(":")[0].strip()
                        uuid = str(id.uuid4())
                        xrefs.append(o_xrefs)
                        complete_url = self.get_complete_url_ont(local_id, o_xrefs)
                        xref_urls.append({"uuid": uuid, "displayName": prefix+":"+local_id,
                                          "globalCrossRefId": prefix+":"+local_id,
                                          "primaryKey": prefix +":"+ local_id + "ontology_provided_cross_reference",
                                          "oid": line['id'], "xrefId": o_xrefs, "local_id": local_id,
                                          "prefix": prefix, "crossRefCompleteUrl": complete_url,
                                          "complete_url": complete_url,
                                          "crossRefType": "ontology_provided_cross_reference"})
            if xrefs is None:
                xrefs = []  # Set the synonyms to an empty array if None. Necessary for Neo4j parsing
            o_is_as = line.get('is_a')
            if o_is_as is None:
                isasWithoutNames = []
            else:
                if isinstance(o_is_as, (list, tuple)):
                    for isa in o_is_as:
                        isaWithoutName = isa.split("!")[0].strip()
                        isasWithoutNames.append(isaWithoutName)
                else:
                    isaWithoutName = o_is_as.split("!")[0].strip()
                    isasWithoutNames.append(isaWithoutName)
            o_part_of = line.get('part_of')
            if o_part_of is None:
                posWithoutNames = []
            else:
                if isinstance(o_part_of, (list, tuple)):
                    for po in o_part_of:
                        poWithoutName = po.split("!")[0].strip()
                        posWithoutNames.append(poWithoutName)
                else:
                    poWithoutName = po.split("!")[0].strip()
                    posWithoutNames.append(poWithoutName)
            definition = line.get('def')
            defLinks = ""
            defLinksProcessed = []
            if definition is None:
                definition = ""
            else:
                if definition is not None and "\"" in definition:
                    defText = definition.split("\"")[1].strip()
                    if "[" in definition.split("\"")[2].strip():
                        defLinks = definition.split("\"")[2].strip()
                        defLinks = defLinks.rstrip("]").replace("[", "")
                        defLinks = defLinks.replace("url:www", "http://wwww")
                        defLinks = defLinks.replace("url:", "")
                        defLinks = defLinks.replace("URL:", "")
                        defLinks = defLinks.replace("\\:", ":")

                        if "," in defLinks:
                            defLinks = defLinks.split(",")
                            for link in defLinks:
                                if link.strip().startswith("http"):
                                    defLinksProcessed.append(link)
                        else:
                            if defLinks.strip().startswith("http"):
                                defLinksProcessed.append(defLinks)
                else:
                    definition = defText
            if definition is None:
                definition = ""

            newSubset = line.get('subset')
            if isinstance(newSubset, (list, tuple)):
                subset = newSubset
            else:
                if newSubset is not None:
                    subset.append(newSubset)
            is_obsolete = line.get('is_obsolete')
            if is_obsolete is None:
                is_obsolete = "false"

            if line['id'] is None or line['id'] == '':
               logger.info("missing oid")
            else:
                dict_to_append = {
                    'o_genes': [],
                    'o_species': [],
                    'name': line.get('name'),
                    'o_synonyms': syns,
                    'name_key': line.get('name'),
                    'oid': line['id'],
                    'definition': definition,
                    'isas': isasWithoutNames,
                    'partofs': posWithoutNames,
                    'is_obsolete': is_obsolete,
                    'subset': subset,
                    'xrefs': xrefs,
                    'oPrefix': prefix,
                    'xref_urls': xref_urls,
                    'defText': defText,
                    'defLinksProcessed': defLinksProcessed,
                    'oboFile': prefix,
                    'category': 'go',
                    'o_type': line.get('namespace'),
                    'display_synonym': display_synonym

                }
                list_to_return.append(dict_to_append)

            # if testObject.using_test_data() is True:
            #     filtered_dict = []
            #     for entry in list_to_return:
            #         if testObject.check_for_test_ontology_entry(entry['id']) is True:
            #             filtered_dict.append(entry)
            #         else:
            #             continue
            #     return filtered_dict
            # else:
        return list_to_return

    #TODO: add these to resourceDescriptors.yaml and remove hardcoding.
    def get_complete_url_ont (self, local_id, global_id):

        complete_url = None

        if 'OMIM' in global_id:
            complete_url = 'https://www.omim.org/entry/' + local_id
        if 'OMIM:PS' in global_id:
            complete_url = 'https://www.omim.org/phenotypicSeries/' + local_id
        if 'ORDO' in global_id:
            complete_url = 'http://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=EN&Expert=' +local_id
        if 'MESH' in global_id:
            complete_url = 'https://www.ncbi.nlm.nih.gov/mesh/' + local_id
        if 'EFO' in global_id:
            complete_url = 'http://www.ebi.ac.uk/efo/EFO_' + local_id
        if 'KEGG' in global_id:
            complete_url ='http://www.genome.jp/dbget-bin/www_bget?map' +local_id
        if 'NCI' in global_id:
            complete_url = 'https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=' + local_id

        return complete_url
