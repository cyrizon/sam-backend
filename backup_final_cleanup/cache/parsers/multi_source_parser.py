"""
Multi-Source Parser
------------------

Coordinates parsing from multiple OSM GeoJSON sources.
"""

from typing import Dict, List, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor, as_completed

if TYPE_CHECKING:
    from .toll_booth_parser import TollBoothParser
    from .motorway_link_parser import MotorwayLinkParser
from ..models.link_types import LinkType
from ..models.toll_booth_station import TollBoothStation
from ..models.motorway_link import MotorwayLink


class ParsedOSMData:
    """Container pour les données OSM parsées."""
    
    def __init__(self):
        self.toll_booths: List[TollBoothStation] = []
        self.entry_links: List[MotorwayLink] = []
        self.exit_links: List[MotorwayLink] = []
        self.indeterminate_links: List[MotorwayLink] = []
    
    def get_all_motorway_links(self) -> List[MotorwayLink]:
        """Retourne tous les motorway links."""
        return self.entry_links + self.exit_links + self.indeterminate_links
    
    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques des données parsées."""
        return {
            'toll_booths': len(self.toll_booths),
            'entry_links': len(self.entry_links),
            'exit_links': len(self.exit_links),
            'indeterminate_links': len(self.indeterminate_links),
            'total_links': len(self.get_all_motorway_links())
        }


class MultiSourceParser:
    """Parser coordinateur pour les multiples sources OSM."""
    
    def __init__(self, data_sources: Dict[str, str]):
        """
        Initialise le parser multi-sources.
        
        Args:
            data_sources: Dict avec les chemins des fichiers
                {
                    'toll_booths': 'path/to/toll_booths.geojson',
                    'entries': 'path/to/motorway_entries.geojson',
                    'exits': 'path/to/motorway_exits.geojson',
                    'indeterminate': 'path/to/motorway_indeterminate.geojson'
                }
        """
        self.data_sources = data_sources
        self.parsed_data = ParsedOSMData()
    
    def parse_all_sources(self, use_parallel: bool = True) -> ParsedOSMData:
        """
        Parse toutes les sources OSM.
        
        Args:
            use_parallel: Si True, utilise le parsing en parallèle
            
        Returns:
            ParsedOSMData: Données parsées de toutes les sources
        """
        print("🚀 Début du parsing multi-sources OSM...")
        
        if use_parallel:
            return self._parse_parallel()
        else:
            return self._parse_sequential()
    
    def _parse_sequential(self) -> ParsedOSMData:
        """Parse séquentiel des sources."""
        # Import dynamique pour éviter les imports circulaires
        from .toll_booth_parser import TollBoothParser
        from .motorway_link_parser import MotorwayLinkParser
        
        # 1. Parse toll booths
        if 'toll_booths' in self.data_sources:
            toll_parser = TollBoothParser(self.data_sources['toll_booths'])
            self.parsed_data.toll_booths = toll_parser.parse()
        
        # 2. Parse entry links
        if 'entries' in self.data_sources:
            entry_parser = MotorwayLinkParser(self.data_sources['entries'], LinkType.ENTRY)
            self.parsed_data.entry_links = entry_parser.parse()
        
        # 3. Parse exit links
        if 'exits' in self.data_sources:
            exit_parser = MotorwayLinkParser(self.data_sources['exits'], LinkType.EXIT)
            self.parsed_data.exit_links = exit_parser.parse()
        
        # 4. Parse indeterminate links
        if 'indeterminate' in self.data_sources:
            indeterminate_parser = MotorwayLinkParser(self.data_sources['indeterminate'], LinkType.INDETERMINATE)
            self.parsed_data.indeterminate_links = indeterminate_parser.parse()
        
        self._print_parsing_summary()
        return self.parsed_data
    
    def _parse_parallel(self) -> ParsedOSMData:
        """Parse en parallèle des sources."""
        # Import dynamique pour éviter les imports circulaires
        from .toll_booth_parser import TollBoothParser
        from .motorway_link_parser import MotorwayLinkParser
        
        tasks = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Soumettre toutes les tâches de parsing
            if 'toll_booths' in self.data_sources:
                parser = TollBoothParser(self.data_sources['toll_booths'])
                tasks['toll_booths'] = executor.submit(parser.parse)
            
            if 'entries' in self.data_sources:
                parser = MotorwayLinkParser(self.data_sources['entries'], LinkType.ENTRY)
                tasks['entries'] = executor.submit(parser.parse)
            
            if 'exits' in self.data_sources:
                parser = MotorwayLinkParser(self.data_sources['exits'], LinkType.EXIT)
                tasks['exits'] = executor.submit(parser.parse)
            
            if 'indeterminate' in self.data_sources:
                parser = MotorwayLinkParser(self.data_sources['indeterminate'], LinkType.INDETERMINATE)
                tasks['indeterminate'] = executor.submit(parser.parse)
            
            # Récupérer les résultats
            for task_name in tasks:
                try:
                    result = tasks[task_name].result()
                    if task_name == 'toll_booths':
                        self.parsed_data.toll_booths = result
                    elif task_name == 'entries':
                        self.parsed_data.entry_links = result
                    elif task_name == 'exits':
                        self.parsed_data.exit_links = result
                    elif task_name == 'indeterminate':
                        self.parsed_data.indeterminate_links = result
                except Exception as e:
                    print(f"❌ Erreur lors du parsing {task_name}: {e}")
        
        self._print_parsing_summary()
        return self.parsed_data
    
    def _print_parsing_summary(self):
        """Affiche un résumé du parsing."""
        stats = self.parsed_data.get_stats()
        print(f"\n📊 Résumé du parsing OSM:")
        print(f"   • Toll booths: {stats['toll_booths']}")
        print(f"   • Entry links: {stats['entry_links']}")
        print(f"   • Exit links: {stats['exit_links']}")
        print(f"   • Indeterminate links: {stats['indeterminate_links']}")
        print(f"   • Total links: {stats['total_links']}")
        print("✅ Parsing multi-sources terminé!\n")
