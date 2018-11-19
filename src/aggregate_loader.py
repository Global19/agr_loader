import logging, coloredlogs, os, sys

coloredlogs.install(level=logging.INFO,
    fmt='%(asctime)s %(levelname)s: %(name)s:%(lineno)d: %(message)s',
    field_styles={
        'asctime': {'color': 'green'}, 
        'hostname': {'color': 'magenta'}, 
        'levelname': {'color': 'white', 'bold': True}, 
        'name': {'color': 'blue'}, 
        'programname': {'color': 'cyan'}
    })

# logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s: %(name)s:%(lineno)d: %(message)s')
logger = logging.getLogger(__name__)

# This has to be done because the OntoBio module does not use DEBUG it uses INFO which spews output.
# So we have to set the default to WARN in order to "turn off" OntoBio and then "turn on" by setting 
# to DEBUG the modules we want to see output for.

from etl import *
from transactors import CSVTransactor, Neo4jTransactor, FileTransactor
from transactions import Indicies
from data_manager import DataFileManager

class AggregateLoader(object):

    def run_loader(self):

        # TODO Allow the yaml file location to be overwritten by command line input (for Travis).
        data_manager = DataFileManager(os.path.abspath('src/config/develop.yml'))
        data_manager.process_config()

        FileTransactor().start_threads(8)
        data_manager.download_and_validate()
        FileTransactor().wait_for_queues()

        Neo4jTransactor().start_threads(4)
        CSVTransactor().start_threads(4)
        
        logger.info("Creating indices.")
        Indicies().create_indices()

        etl_dispatch = {
            'GO': GOETL,
            'DO': DOETL,
            'SO': SOETL,
            'MI': MIETL,
            'BGI': BGIETL,
            'Allele': AlleleETL,
            'Expression': ExpressionETL,
            'DiseaseAllele': DiseaseAlleleETL,
        }

        list_of_types = [
            ['GO', 'DO', 'SO', 'MI'],
            ['BGI'],
            ['Allele'],
            #['Expression'],
            ['DiseaseAllele'],
            #['DiseaseGene'],
            #['Phenotype'],
            #['Orthology'],
            #['GOAnnot'],
            #['GeoXref'],
        ]

        for data_types in list_of_types:
            for data_type in data_types:
                config = data_manager.get_config(data_type)
                if config is not None:
                    etl = etl_dispatch[data_type](config)
                    etl.run_etl()
            logger.info("Waiting for Queues to sync up")
            CSVTransactor().wait_for_queues()
            Neo4jTransactor().wait_for_queues()
            logger.info("Queue sync finished")

if __name__ == '__main__':
    AggregateLoader().run_loader()
